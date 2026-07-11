# RocketMQ 消息契约

前端不直接操作 MQ，契约供 UcubMQDraw FastAPI 后端实现参考。

## Topic 规划

| Topic | 用途 | 消费方 |
|---|---|---|
| `ucub_imggen_api_task` | API 并发版任务队列 | imggen-ComfyUI-API |
| `ucub_imggen_gpt_task` | GPT 串行版任务队列 | imggen-ComfyUI-GPT |
| `ucub_imggen_callback` | 统一结果回调队列 | UcubMQDraw |

## 前置约束

下发消息仅存算力执行参数；用户归属、权限、任务统计由 UcubMQDraw 业务中台靠 `innerTaskId` 映射管理，imggen 不解析业务属性。

## 一、风格迁移任务

```json
{
  "innerTaskId": "inner_20260711_00001",
  "modelName": "SDXL/Flux",
  "prompt": "高清商品图，8K，写实",
  "negativePrompt": "模糊，水印，低画质",
  "width": 1024,
  "height": 1024,
  "batchSize": 2,
  "refImageList": ["oss://ucub-img/ref/base.jpg", "oss://ucub-img/ref/style_ref.jpg"],
  "timeout": 300,
  "workflowJson": "ComfyUI风格迁移导出完整JSON字符串",
  "styleStrength": 0.75,
  "computeType": "comfy_api"
}
```

- `refImageList`：第 1 项=基底原图，第 2 项=风格参考图
- `styleStrength`：界面滑块 0~1
- `computeType`：`comfy_api`（并发）/ `comfy_gpt`（串行）

## 二、局部重绘任务

```json
{
  "innerTaskId": "inner_20260711_00002",
  "modelName": "SDXL/Flux",
  "prompt": "墙面更换大理石材质，细腻石材纹理",
  "negativePrompt": "色差严重、破损、脏污",
  "width": 1024,
  "height": 1024,
  "batchSize": 1,
  "refImageList": ["oss://ucub-img/ref/base_render.jpg"],
  "maskOssUrl": "oss://ucub-img/mask/mask_20260711_00002.png",
  "timeout": 300,
  "workflowJson": "ComfyUI局部重绘导出完整JSON字符串",
  "maskBlurRadius": 6,
  "denoiseStrength": 0.8,
  "computeType": "comfy_gpt"
}
```

- `maskOssUrl`：Gradio 画笔圈选蒙版上传 OSS 后的地址
- `maskBlurRadius`：蒙版边缘羽化像素
- `denoiseStrength`：重绘去噪强度 0~1
- `refImageList`：仅填入基底原图

## 三、统一回调（ucub_imggen_callback）

```json
{
  "innerTaskId": "inner_20260711_00001",
  "status": "success",
  "costTime": 24.3,
  "imageUrlList": ["oss://ucub-img/output/out_0001.png"],
  "errorMsg": ""
}
```

## 四、局部重绘蒙版链路

1. Gradio 前端：用户在画布用画笔圈选范围，生成 PNG 蒙版
2. 前端上传 OSS，拿到蒙版链接
3. UcubMQDraw 后端写入 `maskOssUrl` 投递 MQ
4. imggen 读取蒙版执行 ComfyUI 局部重绘
5. 回调经 `innerTaskId` 映射业务 taskId，更新创作记录

代码参考：`ucub_mqdraw/services/mq_contract.py`
