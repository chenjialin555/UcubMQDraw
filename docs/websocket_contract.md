# WebSocket 消息契约

WebSocket 连接 UcubMQDraw FastAPI，不连接 imggen。

```text
imggen → RocketMQ callback → UcubMQDraw FastAPI → WebSocket → Gradio 前端
```

## 连接地址

```
ws://{host}:8000/api/v1/images/generations/tasks/ws
```

## 推送消息格式

进行中：

```json
{
  "taskId": "ucub_task_20260711_00001",
  "status": "running",
  "progress": 60,
  "imageUrlList": [],
  "errorMsg": "",
  "costTime": null
}
```

完成：

```json
{
  "taskId": "ucub_task_20260711_00001",
  "status": "completed",
  "progress": 100,
  "imageUrlList": ["https://oss.xxx/output.png"],
  "errorMsg": "",
  "costTime": 18.6
}
```

失败：

```json
{
  "taskId": "ucub_task_20260711_00001",
  "status": "failed",
  "progress": 100,
  "imageUrlList": [],
  "errorMsg": "ComfyUI 工作流执行失败",
  "costTime": 12.4
}
```

## 状态映射

| 后端 status | 前端 TaskStatus |
|---|---|
| created | CREATED |
| queued | QUEUED |
| dispatching | DISPATCHING |
| running | RUNNING |
| completed / success | COMPLETED |
| failed / fail | FAILED |
| cancelled | CANCELLED |
| retrying | RETRYING |

代码参考：`ucub_mqdraw/services/websocket_client.py`
