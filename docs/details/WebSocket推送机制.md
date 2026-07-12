# WebSocket 推送机制

> 消息格式见 [API接口.md](../API接口.md#十一websocket)。
> **阅读：** [代码阅读指南.md](../代码阅读指南.md) → [WebSocket推送示例 §二最小版](../examples/WebSocket推送示例.md#二最小可读版先看这个)

## 〇、分期阅读

| 阶段 | 看什么 | 先别看 |
|------|--------|--------|
| Phase 1 | §二鉴权 + §六 Manager + 示例 §二最小版 + §四拆文件 | Redis、心跳 |
| Phase 2 | 游客过滤、心跳、task.deleted | — |
| Phase 3 | §九多实例 Redis Pub/Sub | — |

---

## 一、设计原则

```text
HTTP   负责认证 + 业务命令
WS     负责服务端事件通知；连接必须带 JWT token
MySQL  负责任务事实（SQLite 仅开发库）
RocketMQ 负责任务队列（不用 Redis List 替代）
Redis Pub/Sub（可选）仅用于多实例 WS 事件分发
```

正式版 WebSocket 与 MVP 广播模式的核心差异：

| 维度 | MVP（开发可简化） | 正式版 |
|------|-------------------|--------|
| 连接模型 | 全局 `list[WebSocket]` | `dict[userId, set[WebSocket]]` |
| 推送范围 | 广播所有连接 | 只推任务所属 `user_id` |
| 鉴权 | 可无 | token / Cookie 解析用户 |
| 重连 | 固定 3 秒 | 指数退避 + 重连后 `fetchTasks` |
| 心跳 | 可选 | `system.ping` / `system.pong` |
| 消息类型 | 仅 `task_update` | `task.created` / `task.updated` / … |

---

## 二、连接地址与鉴权

```text
ws://{host}/api/v1/ws/tasks?token=<jwt>
```

或使用与 HTTP 相同的 Cookie / `Authorization` 头。

后端在 accept 前校验 token，解析出 `user_id`：

```python
user = await get_current_user_from_ws(websocket)
await websocket_manager.connect(user.user_id, websocket)
```

**禁止** `/ws/connect/{user_id}`——`user_id` 必须从 JWT `sub` 解析。

游客 token 的 `sub` 为 `user_guest_public`。后端仍会推送该用户任务事件；**前端需按 localStorage `guest_task_ids` 过滤**。见 [用户与鉴权设计.md §十三](./用户与鉴权设计.md#十三游客模式)。

一个用户可开多个 Tab，因此连接池为 **set**：

```python
connections: dict[str, set[WebSocket]] = {}
```

---

## 三、事件类型

详见 [API接口.md §10.4](../API接口.md#104-事件类型)。

前端统一处理含 `task` 的事件：

```ts
if (message.task) {
  taskStore.upsertTask(message.task)
}
```

删除：

```ts
if (message.type === 'task.deleted' && message.taskId) {
  taskStore.removeTask(message.taskId)
}
```

---

## 四、前端连接（`utils/ws.ts`）

正式版需实现：

```text
1. 建立连接（带 token）
2. 收到事件 → 更新 taskStore
3. 断线指数退避重连
4. 重连 onopen 后立即 fetchTasks 补齐历史
5. 30 秒心跳 system.ping
```

**完整可复制代码** → [examples/WebSocket推送示例.md](../examples/WebSocket推送示例.md)

关键点：

```ts
socket.onopen = async () => {
  reconnectAttempt = 0
  await taskStore.fetchTasks()  // 修复断线期间漏消息
  startHeartbeat()
}
```

WebSocket 消息可能丢失，**不能**只靠 WS 保证列表一致性；数据库 + HTTP 拉取是最终真相来源。

---

## 五、taskStore 要点

```text
upsertTask   按 taskId 合并，并按 createdAt 排序（不要只靠 unshift）
removeTask   响应 task.deleted
fetchTasks   挂载时 + WS 重连后必调
```

---

## 六、后端 WebSocketManager（正式版）

```python
class WebSocketManager:
    def __init__(self):
        self.connections: dict[str, set[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.connections.setdefault(user_id, set()).add(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket):
        user_connections = self.connections.get(user_id)
        if not user_connections:
            return
        user_connections.discard(websocket)
        if not user_connections:
            self.connections.pop(user_id, None)

    async def send_to_user(self, user_id: str, payload: dict):
        connections = list(self.connections.get(user_id, set()))
        disconnected = []
        for ws in connections:
            try:
                await ws.send_json(payload)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(user_id, ws)
```

任务状态变化时：

```python
await websocket_manager.send_to_user(
    task.user_id,
    {
        "type": "task.updated",
        "eventId": generate_event_id(),
        "serverTime": now_iso(),
        "task": task.to_response_dict(),
    },
)
```

**不要** `broadcast` 给所有连接。

---

## 七、WebSocket API

```python
@router.websocket("/api/v1/ws/tasks")
async def task_websocket(websocket: WebSocket, token: str = Query(None)):
    user = await get_current_user_from_ws(websocket, token)
    await websocket_manager.connect(user.user_id, websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            if msg.get("type") == "system.ping":
                await websocket.send_json({
                    "type": "system.pong",
                    "serverTime": now_iso(),
                })
    except WebSocketDisconnect:
        websocket_manager.disconnect(user.user_id, websocket)
```

客户端**不应**通过 WS 发送 `delete` / `rerun` 等业务指令。

---

## 八、谁触发推送

| 时机 | 事件 type | 调用方 |
|------|-----------|--------|
| 创建任务写库后 | `task.created` | `task_service.create_task` |
| 投递 MQ 前后 | `task.updated` | `task_service.create_task` |
| Mock 每步进度 | `task.updated` | `mock_task_runner` |
| imggen 成功 | `task.succeeded` | `handle_imggen_callback` |
| imggen 失败 | `task.failed` | `handle_imggen_callback` |
| 软删除后 | `task.deleted` | `task_service.delete_task` |
| 收藏变更 | `task.favorite_set` | `task_service.favorite_task` |

链路：

```text
RocketMQ callback → 更新 DB → send_to_user(task.user_id)
```

---

## 九、多实例部署

单 FastAPI 进程时，内存 `WebSocketManager` 即可。

生产多 worker / 多实例时会出现：

```text
用户 WS 连在实例 A
MQ callback 被实例 B 消费
实例 B 内存里没有该用户 WS → 推送失败
```

### 方案 A：WebSocket 单实例（初期）

所有 WS 连接固定到一个 ws 服务，task event 转发给它。简单，扩展性一般。

### 方案 B：Redis Pub/Sub（推荐正式版）

```text
任意实例收到 task 变更
  ↓
更新 DB
  ↓
publish Redis channel: task_events:{user_id}
  ↓
所有实例订阅 task_events
  ↓
持有该 user_id WS 连接的实例 send_to_user
```

**注意：** 此处 Redis 是 **Pub/Sub 事件总线**，不是任务队列。任务队列仍是 **RocketMQ**。

环境变量示例：

```env
REDIS_URL=redis://127.0.0.1:6379/0
REDIS_WS_CHANNEL_PREFIX=ucub:task_events
```

---

## 十、幂等与终态保护

回调 Consumer 必须：

```text
1. innerTaskId 唯一映射
2. 重复回调幂等更新
3. 终态 succeeded / failed / canceled 不允许被 running 覆盖
4. 终态重复 success 回调可更新 callback raw，但不重复推异常状态
```

```python
if task.status in ("succeeded", "failed", "canceled"):
    return task  # 或仅 merge callback raw
```

---

## 十一、注意事项

1. **同步上下文推送**：Mock 跑在后台线程，需 `asyncio.run_coroutine_threadsafe` 或统一 async service
2. **多 Tab**：同一 user 多个 WS，全部 `send_to_user`
3. **开发 Mock**：`USE_MOCK=true` 时仍走 `send_to_user`，便于本地验证定向推送
4. **不要用 Redis List 做主任务队列**：与 imggen 对接必须走 RocketMQ

**完整可复制代码** → [examples/WebSocket推送示例.md](../examples/WebSocket推送示例.md)
