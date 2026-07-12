# API 接口

> 前后端联调契约。**字段定义的权威来源**，其它文档请引用本文档，不要重复粘贴完整定义。

**文档导航** → [README.md](./README.md)

## 一、接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/uploads/images` | 上传图片 |
| POST | `/api/v1/images/generations/tasks` | 创建任务 |
| GET | `/api/v1/images/generations/tasks` | 任务列表（分页） |
| GET | `/api/v1/images/generations/tasks/{taskId}` | 单条任务 |
| DELETE | `/api/v1/images/generations/tasks/{taskId}` | 软删除任务 |
| POST | `/api/v1/images/generations/tasks/{taskId}/rerun` | 再次生成（新建 taskId） |
| POST | `/api/v1/images/generations/tasks/{taskId}/cancel` | 取消进行中任务 |
| PATCH | `/api/v1/images/generations/tasks/{taskId}/favorite` | 收藏 / 取消收藏 |
| WS | `/api/v1/ws/tasks` | 任务事件推送（只读通知） |

**边界原则：**

```text
HTTP  负责业务命令（创建、删除、再次生成、取消、收藏、查询）
WS    负责服务端事件通知，不承载写操作
```

任务队列走 **RocketMQ**，不走 Redis List。Redis（可选）仅用于多实例 WebSocket 事件分发，见 [WebSocket推送机制.md](./details/WebSocket推送机制.md#九多实例部署)。

---

## 二、上传图片

```http
POST /api/v1/uploads/images
Content-Type: multipart/form-data

file: <二进制>
Authorization: Bearer <token>    # 正式版需登录态
```

响应：

```json
{
  "url": "http://object.intuly.com/ai/img/build/20260712/abc_base.png"
}
```

开发与生产均返回 OSS URL。

---

## 三、创建任务

```http
POST /api/v1/images/generations/tasks
Content-Type: application/json
Authorization: Bearer <token>
```

### 请求体（统一格式）

```json
{
  "toolKey": "style_transfer",
  "params": { }
}
```

`params` 结构**因工具而异**，由各自 `tool.ts` / `XxxTool` 定义。

### 风格迁移示例

```json
{
  "toolKey": "style_transfer",
  "params": {
    "prompt": "赛博朋克风格",
    "refImageList": [
      "https://cdn.xxx.com/base.png",
      "https://cdn.xxx.com/style.png"
    ],
    "generationCount": 1,
    "styleStrength": 0.75
  }
}
```

### 局部重绘示例

```json
{
  "toolKey": "inpaint",
  "params": {
    "prompt": "把选中区域改成花园",
    "refImageList": ["https://cdn.xxx.com/base.png"],
    "maskImageUrl": "https://cdn.xxx.com/mask.png",
    "denoiseStrength": 0.65,
    "maskBlurRadius": 8
  }
}
```

### 响应（TaskResponse）

```json
{
  "taskId": "ucub_task_20260712_abc123",
  "toolKey": "style_transfer",
  "toolName": "风格迁移",
  "status": "queued",
  "progress": 10,
  "taskSubmitParams": { },
  "taskCallbackParams": { },
  "errorMessage": "",
  "costTime": null,
  "favorite": false,
  "createdAt": "2026-07-12T16:00:00+08:00",
  "updatedAt": "2026-07-12T16:00:01+08:00"
}
```

说明：

- `taskDispatchParams` **不返回给前端**（仅数据库存 + 投 MQ）
- `taskSubmitParams` = 请求的 `params` 副本
- 进行中 `taskCallbackParams` 为空；成功后含 `imageUrlList` 等
- 后端从 token 解析 `user_id`，前端不传

### 创建链路（正式版）

```text
1. validate toolKey + params
2. 写 DB，status=created
3. WS 推 task.created
4. status=dispatching
5. 投递 RocketMQ
6. 成功 → status=queued；失败 → status=failed
7. WS 推 task.updated / task.failed
```

---

## 四、查询任务列表

```http
GET /api/v1/images/generations/tasks?page=1&pageSize=20&status=running
Authorization: Bearer <token>
```

| 参数 | 说明 |
|------|------|
| `page` | 页码，从 1 开始，默认 1 |
| `pageSize` | 每页条数，默认 20，最大 100 |
| `status` | 可选，筛选状态（见 §七） |

响应：

```json
{
  "items": [ { "taskId": "...", "status": "running", "...": "..." } ],
  "page": 1,
  "pageSize": 20,
  "total": 128
}
```

- 只返回**当前用户**、**未软删除**（`deleted_at IS NULL`）的任务
- `items` 内元素结构与 `TaskResponse` 一致
- 按 `createdAt` 倒序

---

## 五、查询单条任务

```http
GET /api/v1/images/generations/tasks/{taskId}
Authorization: Bearer <token>
```

校验任务属于当前用户，否则 404。

---

## 六、删除任务（软删除）

```http
DELETE /api/v1/images/generations/tasks/{taskId}
Authorization: Bearer <token>
```

逻辑：

```text
校验 user_id → 设置 deleted_at → WS 推 task.deleted
```

响应：`204 No Content` 或返回最新快照。

**不物理删除**，保留审计与排查记录。

---

## 七、再次生成

```http
POST /api/v1/images/generations/tasks/{taskId}/rerun
Authorization: Bearer <token>
```

逻辑：

```text
查旧任务 → 校验 user_id → 复制 taskSubmitParams
→ 生成全新 taskId + innerTaskId → 走 create_task 完整链路
```

**必须创建新任务，不覆盖旧任务。**

响应：新任务的 `TaskResponse`。

---

## 八、取消任务

```http
POST /api/v1/images/generations/tasks/{taskId}/cancel
Authorization: Bearer <token>
```

仅 `created` / `queued` / `dispatching` / `running` 可取消。

响应：更新后的 `TaskResponse`，`status=canceled`。

取消成功后 WS 推 `task.updated` 或专用事件。

---

## 九、收藏

```http
PATCH /api/v1/images/generations/tasks/{taskId}/favorite
Content-Type: application/json
Authorization: Bearer <token>

{ "favorite": true }
```

响应：更新后的 `TaskResponse`。WS 推 `task.favorite_set`（可选，前端也可仅依赖 HTTP 响应）。

---

## 十、WebSocket

### 10.1 连接地址

```text
ws://{host}/api/v1/ws/tasks?token=<jwt>
```

或使用 Cookie / `Authorization` 头鉴权（与 HTTP 同一套登录态）。

**禁止**使用 `/ws/connect/{user_id}` 这类 URL 传用户身份——`user_id` 必须由后端从 token 解析。

### 10.2 职责边界

```text
WebSocket 只接收服务端事件通知
创建 / 删除 / 再次生成 / 取消 / 收藏 → 全部走 HTTP
```

### 10.3 事件 envelope

```json
{
  "type": "task.updated",
  "eventId": "evt_20260712_xxx",
  "serverTime": "2026-07-12T16:01:00+08:00",
  "task": {
    "taskId": "ucub_task_20260712_abc123",
    "toolKey": "style_transfer",
    "toolName": "风格迁移",
    "status": "running",
    "progress": 60,
    "taskSubmitParams": { },
    "taskCallbackParams": { },
    "errorMessage": "",
    "costTime": null,
    "favorite": false,
    "createdAt": "2026-07-12T16:00:00+08:00",
    "updatedAt": "2026-07-12T16:01:00+08:00"
  }
}
```

### 10.4 事件类型

| type | 说明 |
|------|------|
| `task.created` | 任务创建后 |
| `task.updated` | 状态 / 进度变化 |
| `task.succeeded` | 生成成功（终态） |
| `task.failed` | 生成失败（终态） |
| `task.deleted` | 软删除成功，见 §10.5 |
| `task.favorite_set` | 收藏变化（可选） |
| `system.pong` | 心跳响应 |
| `system.error` | WS 指令错误 |

前端处理建议：

```ts
// 含 task 字段的事件统一合并
if (message.task) {
  taskStore.upsertTask(message.task)
}

// 删除单独处理
if (message.type === 'task.deleted' && message.taskId) {
  taskStore.removeTask(message.taskId)
}
```

### 10.5 删除事件

```json
{
  "type": "task.deleted",
  "eventId": "evt_20260712_yyy",
  "serverTime": "2026-07-12T16:05:00+08:00",
  "taskId": "ucub_task_20260712_abc123"
}
```

### 10.6 客户端心跳

客户端可发送：

```json
{ "type": "system.ping" }
```

服务端响应：

```json
{
  "type": "system.pong",
  "serverTime": "2026-07-12T16:01:00+08:00"
}
```

### 10.7 断线恢复

WebSocket **不是可靠消息队列**。前端重连成功后**必须**调用 `GET /tasks` 补齐断线期间漏掉的状态变化。

详见 [WebSocket推送机制.md](./details/WebSocket推送机制.md)。

---

## 十一、任务状态枚举

统一使用以下值，**不要混用** `success` / `succeeded` / `completed`：

| status | 含义 | 前端展示 |
|--------|------|----------|
| `created` | 已创建，尚未入队 | 已创建 |
| `queued` | 已入队，等待 imggen 消费 | 排队中 |
| `dispatching` | 正在投递 MQ | 提交中 |
| `running` | imggen / ComfyUI 处理中 | 生成中 |
| `succeeded` | 成功（终态） | 已完成 |
| `failed` | 失败（终态） | 生成失败 |
| `canceled` | 已取消（终态） | 已取消 |

终态：`succeeded` / `failed` / `canceled`。终态任务不允许被迟到的回调改回 `running`。

imggen MQ 回调仍可能使用 `success`（见 [mq_contract.md](./mq_contract.md)），后端 `normalize_status` 映射为 `succeeded`。

---

## 十二、前端 TypeScript 类型（参考）

```ts
export type TaskStatus =
  | 'created'
  | 'queued'
  | 'dispatching'
  | 'running'
  | 'succeeded'
  | 'failed'
  | 'canceled'

export interface CreateTaskRequest {
  toolKey: string
  params: Record<string, unknown>
}

export interface GenerationTask {
  taskId: string
  toolKey: string
  toolName: string
  status: TaskStatus
  progress: number
  taskSubmitParams: Record<string, unknown>
  taskCallbackParams: Record<string, unknown>
  errorMessage: string
  costTime?: number | null
  favorite: boolean
  createdAt: string
  updatedAt: string
}

export interface TaskListResponse {
  items: GenerationTask[]
  page: number
  pageSize: number
  total: number
}

export interface WsTaskEvent {
  type: string
  eventId?: string
  serverTime?: string
  task?: GenerationTask
  taskId?: string
}
```

---

## 十三、imggen 回调（后端内部，前端不调用）

MQ 消息体存入 `task_callback_params`，典型字段：

```json
{
  "innerTaskId": "inner_xxx",
  "status": "success",
  "imageUrlList": ["https://..."],
  "errorMsg": "",
  "costTime": 18.6
}
```

处理流程：

```text
callback consumer → get_by_inner_task_id
→ 幂等更新 DB → send_to_user(task.user_id, event)
```

`status=success` → 业务库 `succeeded`；`status=failed` → `failed`。

---

## 十四、错误响应

HTTP 4xx/5xx：

```json
{
  "detail": "风格迁移需要底图和风格参考图"
}
```

前端 axios 拦截器统一转成 `Error` 提示。

常见状态码：

| 码 | 场景 |
|----|------|
| 400 | 参数校验失败 |
| 401 | 未登录 / token 无效 |
| 403 | 无权操作他人任务 |
| 404 | 任务不存在或已删除 |
| 409 | 终态任务不可取消 |
| 500 | 服务端异常 |
