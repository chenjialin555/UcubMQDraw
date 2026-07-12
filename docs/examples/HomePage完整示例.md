# HomePage 完整示例

> 简化版三栏首页。工具 ≤ 3 个时可用 `v-if` 替代动态组件，见文末。

## 一、布局结构

```text
┌──────────┬──────────────────┬──────────┐
│  左栏    │      中栏        │   右栏   │
│ 工具列表 │  预览 + 提交按钮 │ 任务列表 │
│ 表单     │                  │          │
└──────────┴──────────────────┴──────────┘
```

## 二、动态组件写法（推荐，工具 > 3 时）

```vue
<template>
  <div class="page">
    <div class="left">
      <div class="tool-list">
        <button
          v-for="tool in tools"
          :key="tool.key"
          :class="{ active: tool.key === currentTool.key }"
          @click="changeTool(tool.key)"
        >
          {{ tool.name }}
        </button>
      </div>

      <component :is="currentTool.Form" :form="form" />
    </div>

    <div class="center">
      <component
        v-if="currentTool.Preview"
        :is="currentTool.Preview"
        :form="form"
      />
      <DefaultPreview v-else :form="form" />

      <button :disabled="submitting" @click="submit">
        {{ submitting ? '提交中...' : '立即生成' }}
      </button>
    </div>

    <div class="right">
      <TaskList />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, shallowRef } from 'vue'
import { ElMessage } from 'element-plus'
import { tools, getDefaultTool, getTool } from '@/tools'
import { useTaskStore } from '@/stores/taskStore'
import TaskList from '@/components/TaskList.vue'
import DefaultPreview from '@/components/DefaultPreview.vue'

const taskStore = useTaskStore()

const currentTool = shallowRef(getDefaultTool())
const form = ref(currentTool.value.createForm())
const submitting = ref(false)

function changeTool(key: string) {
  const tool = getTool(key)
  if (!tool) return
  currentTool.value = tool
  form.value = tool.createForm()
}

async function submit() {
  const error = currentTool.value.validate(form.value)
  if (error) {
    ElMessage.warning(error)
    return
  }

  const request = currentTool.value.buildRequest(form.value)
  submitting.value = true

  try {
    await taskStore.createTask(request)
    ElMessage.success('任务已提交')
  } catch (error: any) {
    ElMessage.error(error.message || '提交失败')
  } finally {
    submitting.value = false
  }
}
</script>
```

## 三、v-if 写法（工具 ≤ 3，最直观）

```vue
<StyleTransferForm v-if="currentToolKey === 'style_transfer'" :form="form" />
<InpaintForm v-if="currentToolKey === 'inpaint'" :form="form" />

<script setup lang="ts">
function buildRequest() {
  if (currentToolKey.value === 'style_transfer') {
    return buildStyleTransferRequest(form.value)
  }
  if (currentToolKey.value === 'inpaint') {
    return buildInpaintRequest(form.value)
  }
}
</script>
```

## 四、主流程对照

```text
changeTool(key)  → 换工具，form = tool.createForm()
submit()         → error = tool.validate(form)
                 → request = tool.buildRequest(form)
                 → taskStore.createTask(request)
```

## 五、RightPanel / TaskList

右栏挂载时拉历史：

```ts
onMounted(() => {
  taskStore.fetchTasks()
})
```

WS 连接在 `main.ts` 全局建立，见 [WebSocket推送机制.md](../details/WebSocket推送机制.md)。

## 六、相关文档

- 工具定义：[前端工具模块示例.md](./前端工具模块示例.md)
- 新增工具：[新增工具开发指南.md](../新增工具开发指南.md)
- 创建任务 API：[API接口.md](../API接口.md#三创建任务)
