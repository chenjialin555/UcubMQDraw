# OSS 上传示例

> 设计说明见 [OSS上传设计.md](../details/OSS上传设计.md)。**开发与生产统一走 OSS**，无本地 static 回退。

## 一、文件清单

```text
backend/app/
├── config.py              # OSS 环境变量
├── services/
│   ├── oss_client.py      # OSS SDK 封装
│   └── upload_service.py  # 上传业务入口
└── api/
    └── upload_api.py      # POST /uploads/images

frontend/src/
├── api/upload.ts
└── components/ImageUploader.vue
```

## 二、config.py（OSS 部分）

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OSS_ACCESS_KEY_ID: str = ""
    OSS_ACCESS_KEY_SECRET: str = ""
    OSS_REGION: str = "cn-guangzhou"
    OSS_ENDPOINT: str = "http://object.intuly.com"
    OSS_USE_CNAME: bool = True
    OSS_BUCKET_NAME: str = ""
    OSS_PATH: str = "ai/img/build"

    class Config:
        env_file = ".env"


settings = Settings()


def oss_enabled() -> bool:
    return bool(settings.OSS_ACCESS_KEY_ID and settings.OSS_ACCESS_KEY_SECRET)
```

## 三、oss_client.py

```python
import logging
import os
import uuid
from datetime import datetime

import alibabacloud_oss_v2 as oss

from app.config import settings, oss_enabled

logger = logging.getLogger(__name__)


class OSSUploadError(Exception):
    def __init__(self, message: str, object_name: str | None = None):
        super().__init__(message)
        self.message = message
        self.object_name = object_name


class OSSClient:
    def __init__(self):
        if not oss_enabled():
            raise OSSUploadError("OSS 未配置，请检查环境变量")
        self._client = self._build_client()

    def _build_client(self) -> oss.Client:
        credentials = oss.credentials.StaticCredentialsProvider(
            settings.OSS_ACCESS_KEY_ID,
            settings.OSS_ACCESS_KEY_SECRET,
        )
        cfg = oss.config.load_default()
        cfg.credentials_provider = credentials
        cfg.region = settings.OSS_REGION
        cfg.endpoint = settings.OSS_ENDPOINT
        cfg.use_cname = settings.OSS_USE_CNAME
        return oss.Client(cfg)

    def build_object_key(self, filename: str) -> str:
        date_part = datetime.now().strftime("%Y%m%d")
        safe_name = os.path.basename(filename) or "image.png"
        unique = uuid.uuid4().hex[:8]
        return f"{settings.OSS_PATH}/{date_part}/{unique}_{safe_name}"

    def build_public_url(self, object_key: str) -> str:
        endpoint = settings.OSS_ENDPOINT.rstrip("/")
        return f"{endpoint}/{object_key}"

    def upload(self, filename: str, content: bytes, content_type: str = "image/png") -> str:
        object_key = self.build_object_key(filename)
        try:
            result = self._client.put_object(
                oss.PutObjectRequest(
                    bucket=settings.OSS_BUCKET_NAME,
                    key=object_key,
                    body=content,
                    headers={"Content-Type": content_type},
                    acl="public-read",
                )
            )
            if not (result and getattr(result, "status_code", None) == 200):
                raise OSSUploadError(
                    f"OSS 上传失败: status={getattr(result, 'status_code', None)}",
                    object_name=object_key,
                )
            url = self.build_public_url(object_key)
            logger.info("OSS 上传成功: %s", url)
            return url
        except OSSUploadError:
            raise
        except Exception as exc:
            raise OSSUploadError(f"OSS 上传异常: {exc}", object_name=object_key) from exc


oss_client = OSSClient()
```

## 四、upload_service.py

```python
from fastapi import HTTPException, UploadFile

from app.services.oss_client import oss_client, OSSUploadError


class UploadService:
    async def upload_image(self, file: UploadFile) -> dict:
        content = await file.read()
        try:
            url = oss_client.upload(
                filename=file.filename or "image.png",
                content=content,
                content_type=file.content_type or "image/png",
            )
        except OSSUploadError as exc:
            raise HTTPException(status_code=500, detail=exc.message) from exc
        return {"url": url}


upload_service = UploadService()
```

## 五、upload_api.py

```python
from fastapi import APIRouter, File, UploadFile

from app.services.upload_service import upload_service

router = APIRouter(prefix="/api/v1/uploads", tags=["upload"])


@router.post("/images")
async def upload_image(file: UploadFile = File(...)):
    return await upload_service.upload_image(file)
```

## 六、前端 upload.ts

```ts
import { http } from './http'

export interface UploadResult {
  url: string
}

export function uploadImage(file: File): Promise<UploadResult> {
  const formData = new FormData()
  formData.append('file', file)
  return http.post('/api/v1/uploads/images', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
```

## 七、ImageUploader.vue

```vue
<template>
  <div class="uploader">
    <img v-if="modelValue" :src="modelValue" class="preview" />
    <el-upload
      :show-file-list="false"
      :before-upload="handleUpload"
      accept="image/*"
    >
      <el-button :loading="uploading">{{ modelValue ? '重新上传' : '上传图片' }}</el-button>
    </el-upload>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { uploadImage } from '@/api/upload'

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const uploading = ref(false)

async function handleUpload(file: File) {
  uploading.value = true
  try {
    const { url } = await uploadImage(file)
    emit('update:modelValue', url)
  } catch (error: any) {
    ElMessage.error(error.message || '上传失败')
  } finally {
    uploading.value = false
  }
  return false  // 阻止 el-upload 默认上传
}
</script>
```

## 八、调用示例

```text
用户选图
  → uploadImage(file)
  → POST /api/v1/uploads/images
  → 返回 { "url": "http://object.intuly.com/ai/img/build/20260712/abc_base.png" }
  → form.baseImageUrl = url
  → 提交任务时放进 params.refImageList
```

蒙版图同样走此接口，见 [MaskEditor示例.md](./MaskEditor示例.md)。
