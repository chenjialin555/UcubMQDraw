# OSS 上传设计

> 上传接口契约见 [API接口.md](../API接口.md#二上传图片)。

## 一、整体链路

```text
前端 ImageUploader / MaskEditor
  ↓ multipart file
POST /api/v1/uploads/images
  ↓
upload_service.upload_image()
  ↓
oss_client.upload()  → 阿里云 OSS
  ↓
返回 { "url": "..." }
  ↓
表单字段存 url，提交任务时放进 params
```

**本地开发与生产统一走 OSS**，不区分环境。

## 二、返回 URL 格式

```text
http://object.intuly.com/ai/img/build/{yyyyMMdd}/{uuid8}_{filename}
```

对象路径规则：

```text
{OSS_PATH}/{yyyyMMdd}/{uuid8}_{filename}
例：ai/img/build/20260712/a1b2c3d4_base.png
```

## 三、环境变量

开发与生产均需配置 OSS：

```env
OSS_ACCESS_KEY_ID=
OSS_ACCESS_KEY_SECRET=
OSS_REGION=cn-guangzhou
OSS_ENDPOINT=http://object.intuly.com
OSS_USE_CNAME=true
OSS_BUCKET_NAME=
OSS_PATH=ai/img/build
```

完整列表见 [部署与环境变量.md](./部署与环境变量.md)。

## 四、oss_client 要点

```text
1. SDK：alibabacloud-oss-v2 + StaticCredentialsProvider
2. use_cname=true + 自定义 endpoint
3. acl=public-read，确保 imggen / 前端能匿名读取
4. 本地开发与生产同一套 OSS 配置，同一 Bucket
5. 第一版不做 batch_upload、签名 URL
```

## 五、upload_service

```python
class UploadService:
    async def upload_image(self, file: UploadFile):
        content = await file.read()
        url = oss_client.upload(
            filename=file.filename or "image.png",
            content=content,
            content_type=file.content_type or "image/png",
        )
        return {"url": url}
```

## 六、前端 ImageUploader

```text
1. 用户选图 → 调 upload API
2. 拿到 url → v-model 写入 form.xxxImageUrl
3. 提交任务时 url 放进 params.refImageList 等字段
```

**不要**在 `POST /tasks` 时传本地 File 对象。

## 七、蒙版图上传

局部重绘流程：

```text
MaskEditor 导出 PNG
  → 同样走 POST /uploads/images
  → form.maskImageUrl = url
  → buildRequest 时 params.maskImageUrl = url
  → 后端下发 JSON 转为 maskOssUrl（imggen 约定）
```

详见 [MaskEditor示例.md](../examples/MaskEditor示例.md)。

## 八、注意

imggen 必须能访问返回的 URL。第一版建议 `public-read` + 自定义域名。

**完整可复制代码** → [examples/OSS上传示例.md](../examples/OSS上传示例.md)
