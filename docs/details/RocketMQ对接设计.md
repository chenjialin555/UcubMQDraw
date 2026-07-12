# RocketMQ 对接设计

> imggen 消息体字段另见 [mq_contract.md](../mq_contract.md)。

## 一、整体链路

正式版任务队列 **只用 RocketMQ**，不用 Redis List 替代。

```text
前端 Vue
  ↓ HTTP POST 创建任务
UcubMQDraw FastAPI
  ↓ 写 MySQL / SQLite（开发库）
  ↓ RocketMQ 投递任务
imggen / ComfyUI 消费
  ↓ RocketMQ callback
UcubMQDraw callback consumer
  ↓ 幂等更新 DB
  ↓ WebSocket send_to_user(task.user_id)
前端创作记录刷新
```

`USE_MOCK=true` 时跳过 Producer / Consumer，Mock 线程模拟进度。

---

## 二、Topic 规划

| 环境变量 | 默认值 | 用途 |
|----------|--------|------|
| `ROCKETMQ_TOPIC_TASK` | `ucub_imggen_api_task` | UcubMQDraw → imggen 下发 |
| `ROCKETMQ_TOPIC_CALLBACK` | `ucub_imggen_callback` | imggen → UcubMQDraw 回调 |

第一版所有工具走同一 Task Topic；后续可按 `tool_key` 扩展路由。

---

## 三、task_id 与 innerTaskId

| 字段 | 存哪里 | 用途 |
|------|--------|------|
| `task_id` | DB | 前端展示的业务任务 ID |
| `inner_task_id` | DB + MQ | imggen 执行、回调映射 |
| `user_id` | DB | 权限隔离、WS 定向推送 |

**MQ 消息体只有 `innerTaskId`**，没有 `workflow`、`bizTaskId`、`toolKey`。业务归属靠 DB 映射。

---

## 四、创建任务投递链路

```text
task_service.create_task
  ↓ validate + 写 DB（created）
  ↓ WS task.created
  ↓ status=dispatching
  ↓ tool.build_task_dispatch_params()
  ↓ mq_service.send(payload)
  ↓ 成功 → status=queued；失败 → status=failed
  ↓ WS task.updated / task.failed
```

伪代码：

```python
async def create_task(user_id: str, req: CreateTaskRequest):
    tool = tool_registry.get(req.toolKey)
    tool.validate(req.params)

    task = task_repo.create(
        user_id=user_id,
        tool_key=req.toolKey,
        status="created",
        task_submit_params=req.params,
    )
    await ws.send_task_event(user_id, "task.created", task)

    task_repo.update_status(task.task_id, "dispatching", progress=5)
    dispatch = tool.build_task_dispatch_params(
        task.task_id, task.inner_task_id, req.params
    )

    try:
        mq_service.send(dispatch, tool_key=tool.key)
        task = task_repo.update_status(task.task_id, "queued", progress=10)
        await ws.send_task_event(user_id, "task.updated", task)
        return task
    except Exception:
        task = task_repo.mark_failed(task.task_id, "任务提交失败，请稍后重试")
        await ws.send_task_event(user_id, "task.failed", task)
        return task
```

---

## 五、mq_service

```python
class MQService:
    def send(self, payload: dict, tool_key: str) -> None:
        topic = settings.ROCKETMQ_TOPIC_TASK
        body = json.dumps(payload, ensure_ascii=False)
        keys = str(payload.get("innerTaskId") or "")
        rocketmq_client.send_message(topic=topic, body=body, tags=tool_key, keys=keys)
```

Producer 要点：单例、ACL、`send_sync` status==0、指数退避重试、shutdown 时 `producer.shutdown()`。

---

## 六、Callback Consumer

`main.py` lifespan 启动（非 Mock）：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    start_callback_consumer()
    yield
    rocketmq_client.shutdown()
```

---

## 七、回调处理（正式版）

```python
def handle_imggen_callback(message: dict) -> None:
    inner_task_id = message.get("innerTaskId")
    task = task_repo.get_by_inner_task_id(inner_task_id)
    if not task:
        logger.warning("unknown innerTaskId: %s", inner_task_id)
        return

    if task.status in ("succeeded", "failed", "canceled"):
        return  # 终态保护

    raw_status = message.get("status")

    if raw_status == "success":
        task = task_repo.mark_succeeded(
            task_id=task.task_id,
            task_callback_params=message,
            cost_time=message.get("costTime"),
        )
        websocket_manager.send_task_event(
            task.user_id, "task.succeeded", task
        )

    elif raw_status in ("failed", "error"):
        task = task_repo.mark_failed(
            task_id=task.task_id,
            error_message=message.get("errorMsg") or "生成失败，请稍后重试",
            task_callback_params=message,
        )
        websocket_manager.send_task_event(
            task.user_id, "task.failed", task
        )

    else:
        task = task_repo.update_progress(
            task_id=task.task_id,
            status="running",
            progress=message.get("progress") or task.progress,
            task_callback_params=message,
        )
        websocket_manager.send_task_event(
            task.user_id, "task.updated", task
        )
```

`normalize_status`：`success` → `succeeded`，`failed`/`error` → `failed`。

---

## 八、幂等与重复消费

```text
1. innerTaskId 唯一索引
2. callback 按 innerTaskId 幂等更新
3. 终态不允许被 running 覆盖
4. succeeded 重复回调：可更新 callback raw，不重复推异常
5. 创建任务：前端 loading + 可选 idempotency key
```

---

## 九、HTTP 回调备选方案（非默认）

若目标环境**无法**消费 MQ callback Topic，可启用 HTTP 备选：

```http
POST /api/v1/images/generations/callbacks
Content-Type: application/json
X-Callback-Secret: <shared-secret>
```

Body 与 MQ callback 相同（含 `innerTaskId`）。

**默认方案仍是 RocketMQ callback consumer。** HTTP 仅作 fallback，处理逻辑复用 `handle_imggen_callback`。

---

## 十、多实例与 WebSocket

Callback 可能被任意实例消费，但该实例内存里不一定持有用户 WS。

解决：更新 DB 后通过 **Redis Pub/Sub** 广播 task event，各实例推送给本地 WS 连接。

详见 [WebSocket推送机制.md §九](./WebSocket推送机制.md#九多实例部署)。

**Redis Pub/Sub ≠ 任务队列。任务队列仍是 RocketMQ。**

---

## 十一、失败重试

- **发送侧**：Producer 指数退避重试
- **消费侧**：异常返回 `RECONSUME_LATER`
- **业务侧**：`failed` 后用户可 `POST .../rerun` 创建**新任务**

---

## 十二、环境变量

```env
ROCKETMQ_NAME_SERVER=10.1.10.5:9876
ROCKETMQ_PRODUCER_GROUP=ucub-mqdraw-producer
ROCKETMQ_ACCESS_KEY=
ROCKETMQ_SECRET_KEY=
ROCKETMQ_TOPIC_TASK=ucub_imggen_api_task
ROCKETMQ_TOPIC_CALLBACK=ucub_imggen_callback
ROCKETMQ_RETRY_TIMES=3
```

**完整可复制代码** → [examples/RocketMQ对接示例.md](../examples/RocketMQ对接示例.md)
