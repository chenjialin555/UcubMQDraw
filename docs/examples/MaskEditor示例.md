# MaskEditor 示例

> 局部重绘专用。上传链路见 [OSS上传设计.md](../details/OSS上传设计.md)。

## 一、使用场景

```text
用户上传底图
  → 中栏显示 MaskEditor
  → 画笔圈选区域
  → 导出蒙版 PNG
  → 上传 OSS 得到 maskImageUrl
  → 写入 form.maskImageUrl
  → 提交任务
```

## 二、InpaintPreview.vue 骨架

```vue
<template>
  <div class="inpaint-preview">
    <img v-if="form.baseImageUrl" :src="form.baseImageUrl" class="base-image" />
    <MaskEditor
      v-if="form.baseImageUrl"
      :base-image-url="form.baseImageUrl"
      @mask-saved="onMaskSaved"
    />
    <EmptyState v-else text="请先上传底图" />
  </div>
</template>

<script setup lang="ts">
import MaskEditor from '@/components/MaskEditor.vue'
import EmptyState from '@/components/EmptyState.vue'

const props = defineProps<{ form: any }>()

function onMaskSaved(url: string) {
  props.form.maskImageUrl = url
}
</script>
```

## 三、MaskEditor 职责（第一版 MVP）

```text
1. Canvas 叠在底图上
2. 画笔绘制白色蒙版区域（可调笔刷大小）
3. 点击「保存蒙版」→ 导出 PNG → 调 upload API
4. emit('mask-saved', url)
```

**MVP 不做**：撤销栈、橡皮擦、多图层、缩放平移（可第二版加）。

## 四、上传蒙版

```ts
async function saveMask(blob: Blob) {
  const formData = new FormData()
  formData.append('file', blob, 'mask.png')
  const { url } = await uploadImage(formData)
  emit('mask-saved', url)
}
```

## 五、提交时 params

```json
{
  "toolKey": "inpaint",
  "params": {
    "prompt": "...",
    "refImageList": ["底图URL"],
    "maskImageUrl": "蒙版URL",
    "denoiseStrength": 0.65,
    "maskBlurRadius": 8
  }
}
```

后端 `build_task_dispatch_params` 将 `maskImageUrl` 转为 `maskOssUrl` 投 MQ。

## 六、蒙版格式

- PNG，白底/透明底 + 白色涂抹区域（与 imggen 约定一致）
- 尺寸与底图一致

## 七、相关

- 局部重绘 tool：[前端工具模块示例.md](./前端工具模块示例.md#二局部重绘-toolsinpainttoolts)
- 后端处理器：[后端工具处理器示例.md](./后端工具处理器示例.md#二局部重绘-toolsinpaintpy)
