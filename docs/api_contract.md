# FastAPI 接口契约

前端只调用 UcubMQDraw FastAPI，不直接调用 imggen。

## 创建任务

```http
POST /api/v1/images/generations/tasks
```

请求体：

```json
{
  "taskId": "ucub_task_20260711_00001",
  "userId": "op021",
  "modelName": "SDXL/Flux",
  "prompt": "高清商品图，8K，写实",
  "negativePrompt": "模糊，水印，低画质",
  "width": 1024,
  "height": 1024,
  "batchSize": 2,
  "refImageList": [
    "oss://ucub-img/ref/base.jpg",
    "oss://ucub-img/ref/style.jpg"
  ],
  "timeout": 300,
  "computeType": "comfy_api",
  "workflowTemplate": "style_transfer_v1.json",
  "workflowJson": "",
  "extra": {
    "tool": "风格迁移",
    "styleStrength": 0.75,
    "bizScene": "style_transfer"
  }
}
```

响应体：

```json
{
  "taskId": "ucub_task_20260711_00001",
  "status": "queued",
  "message": "任务已创建并进入队列"
}
```

## 查询任务

```http
GET /api/v1/images/generations/tasks/{taskId}
```

响应体：

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

## 重跑任务

```http
POST /api/v1/images/generations/tasks/{taskId}/retry
```

响应体：

```json
{
  "taskId": "ucub_task_20260711_00002",
  "originTaskId": "ucub_task_20260711_00001",
  "status": "queued",
  "message": "重跑任务已创建"
}
```
