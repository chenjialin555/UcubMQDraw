# API 接口

> 前后端联调契约。**字段定义的权威来源**，其它文档请引用本文档，不要重复粘贴完整定义。

**文档导航** → [README.md](./README.md)

## 一、接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/uploads/images` | 上传图片 |
| POST | `/api/v1/images/generations/tasks` | 创建任务 |
| GET | `/api/v1/images/generations/tasks` | 任务列表 |
| GET | `/api/v1/images/generations/tasks/{taskId}` | 单条任务 |
| WS | `/api/v1/ws/tasks` | 任务状态推送 |

**第一版不做：** 重跑、取消、收藏接口。

---

## 二、上传图片

```http
POST /api/v1/uploads/images
Content-Type: multipart/form-data

file: <二进制>
```

响应：

```json
{
  "url": "http://object.intuly.com/ai/img/build/20260712/abc_base.png"
}
```

开发环境与生产环境均返回 OSS URL，例如：

```text
http://object.intuly.com/ai/img/build/20260712/abc_base.png
```

---

## 三、创建任务

```http
POST /api/v1/images/generations/tasks
Content-Type: application/json
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
  "progress": 5,
  "taskSubmitParams": { },
  "taskCallbackParams": { },
  "errorMessage": "",
  "costTime": null,
  "favorite": false,
  "createdAt": "2026-07-12 16:00:00",
  "updatedAt": "2026-07-12 16:00:00"
}
```

说明：

- `taskDispatchParams` **不返回给前端**（仅数据库存 + 投 MQ）
- `taskSubmitParams` = 请求的 `params` 副本
- 进行中 `taskCallbackParams` 为空；完成后含 `imageUrlList` 等

---

## 四、查询任务列表

```http
GET /api/v1/images/generations/tasks
```

响应：`TaskResponse[]`，按 `createdAt` 倒序。

---

## 五、查询单条任务

```http
GET /api/v1/images/generations/tasks/{taskId}
```

---

## 六、WebSocket

```text
ws://{host}/api/v1/ws/tasks
```

### 服务端推送

```json
{
  "type": "task_update",
  "task": {
    "taskId": "ucub_task_xxx",
    "status": "running",
    "progress": 60,
    "taskSubmitParams": { },
    "taskCallbackParams": { },
    "errorMessage": "",
    "costTime": null,
    "favorite": false,
    "createdAt": "...",
    "updatedAt": "..."
  }
}
```

### 客户端

- 连接后保持即可，无需发业务消息
- 收到 `task_update` → `taskStore.upsertTask(task)`

---

## 七、任务状态枚举

| status | 含义 |
|--------|------|
| created | 已创建 |
| queued | 已入队 |
| dispatching | 投递中 |
| running | 执行中 |
| completed | 成功 |
| failed | 失败 |

---

## 八、前端 TypeScript 类型（参考）

```ts
export interface CreateTaskRequest {
  toolKey: string
  params: Record<string, unknown>
}

export interface GenerationTask {
  taskId: string
  toolKey: string
  toolName: string
  status: string
  progress: number
  taskSubmitParams: Record<string, unknown>
  taskCallbackParams: Record<string, unknown>
  errorMessage: string
  costTime?: number
  favorite: boolean
  createdAt: string
  updatedAt: string
}
```

---

## 九、imggen 回调（后端内部，前端不调用）

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

通过 `inner_task_id` 映射到业务 `task_id`。

---

## 十、错误响应

HTTP 4xx/5xx：

```json
{
  "detail": "风格迁移需要底图和风格参考图"
}
```

前端 axios 拦截器统一转成 `Error` 提示。
