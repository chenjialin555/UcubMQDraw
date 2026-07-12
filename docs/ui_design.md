# UI 布局与视觉规范

> 本文是 UcubMQDraw Vue 前端的 UI 布局、视觉 Token、组件树和交互验收规范。
> 字段契约以 [API接口.md](./API接口.md) 为准；新增工具方式以 [新增工具开发指南.md](./新增工具开发指南.md) 为准。

**文档导航** → [README.md](./README.md)

## 一、页面目标

UcubMQDraw 首页采用三栏工作台结构，目标是让用户在一个页面内完成：

1. 选择生图工具
2. 上传图片或填写文本参数
3. 在中栏查看输入预览 / 蒙版编辑
4. 提交异步任务
5. 在右栏查看任务状态和历史记录

页面不承载后端调度逻辑。前端只负责交互、展示和调用 HTTP / WebSocket。

---

## 二、页面结构

首页组件树固定为：

```text
HomePage
└── ThreeColumnLayout
    ├── LeftPanel
    │   ├── ToolSelector
    │   └── 当前工具 Form 组件
    ├── CenterPanel
    │   ├── 当前工具 Preview 组件
    │   ├── MaskEditor（可选）
    │   └── SubmitBar
    └── RightPanel
        ├── TaskFilterTabs
        └── TaskList
            └── TaskCard
```

各区域职责：

| 区域 | 组件 | 职责 |
|------|------|------|
| 左栏 | `LeftPanel` | 工具选择、参数填写、图片上传入口 |
| 中栏 | `CenterPanel` | 输入预览、输出占位、蒙版编辑、提交按钮 |
| 右栏 | `RightPanel` | 任务筛选、任务列表、任务状态、任务操作 |

工具 ≤ 3 个时，`HomePage` 可用 `v-if` 切换表单，见 [examples/HomePage完整示例.md](./examples/HomePage完整示例.md)。

---

## 三、三栏布局

推荐使用 CSS Grid 实现三栏布局。

```text
┌────────────────────────────────────────────────────────────┐
│                         Header                             │
├───────────────┬────────────────────────┬───────────────────┤
│ LeftPanel     │ CenterPanel            │ RightPanel        │
│ 工具选择       │ 图片预览 / 蒙版编辑      │ 创作记录           │
│ 参数表单       │ 提交按钮                │ 状态 / 进度 / 操作  │
└───────────────┴────────────────────────┴───────────────────┘
```

推荐宽度：

| 区域 | 宽度 |
|------|------|
| 左栏 | `320px` |
| 中栏 | `1fr` |
| 右栏 | `360px` |

示例：

```css
.home-page {
  min-height: 100vh;
  background: var(--color-bg-page);
}

.three-column-layout {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr) 360px;
  gap: var(--spacing-4);
  height: calc(100vh - var(--header-height));
  padding: var(--spacing-4);
}

.layout-panel {
  min-height: 0;
  border-radius: var(--radius-lg);
  background: var(--color-bg-panel);
  box-shadow: var(--shadow-panel);
  overflow: hidden;
}
```

响应式策略：

| 屏幕宽度 | 策略 |
|----------|------|
| `>= 1280px` | 三栏完整展示 |
| `1024px ~ 1279px` | 左栏压缩，右栏保持 |
| `< 1024px` | 可改为上下堆叠或隐藏右栏为抽屉 |

MVP 阶段优先保证桌面端体验，不强制做移动端完整适配。

---

## 四、CSS Token

建议在 `frontend/src/styles/variables.css` 定义全局 Token。

```css
:root {
  --header-height: 56px;

  --spacing-1: 4px;
  --spacing-2: 8px;
  --spacing-3: 12px;
  --spacing-4: 16px;
  --spacing-5: 24px;
  --spacing-6: 32px;

  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;

  --color-bg-page: #f5f7fb;
  --color-bg-panel: #ffffff;
  --color-bg-muted: #f7f8fa;

  --color-border: #e5e7eb;
  --color-text-primary: #1f2937;
  --color-text-secondary: #6b7280;
  --color-text-muted: #9ca3af;

  --color-primary: #2563eb;
  --color-success: #16a34a;
  --color-warning: #f59e0b;
  --color-danger: #dc2626;

  --shadow-panel: 0 8px 24px rgba(15, 23, 42, 0.06);
}
```

使用原则：

1. 页面级布局使用 Token，不在组件里散落魔法值。
2. 工具表单组件可以使用 Element Plus 默认样式。
3. 业务组件只做少量布局修饰，不重写复杂主题。
4. 第一版不做深色模式。

---

## 五、LeftPanel 规范

`LeftPanel` 负责工具选择和当前工具参数表单。

结构：

```text
LeftPanel
├── ToolSelector
└── ToolFormContainer
    └── 当前 tools/{tool}/XxxForm.vue
```

交互要求：

1. 默认选中第一个已注册工具。
2. 切换工具时重置当前工具默认表单（`tool.createForm()`）。
3. 表单组件只管理当前工具的用户输入。
4. 图片上传通过 `ImageUploader` 组件完成，上传结果写入表单 URL 字段。
5. 不在表单组件里直接投递任务，提交动作由 `HomePage` 或 `SubmitBar` 统一处理。

表单组件推荐 Props：

```ts
defineProps<{
  form: Record<string, unknown>
}>()
```

工具配置以现行 `tools/` 规范为准，不使用归档里的 `features/` 命名。对照见 [archive/features-to-tools术语对照.md](./archive/features-to-tools术语对照.md)。

---

## 六、CenterPanel 规范

`CenterPanel` 负责展示当前工具的预览区域。

结构：

```text
CenterPanel
├── PreviewHeader
├── 当前工具 Preview 组件
├── MaskEditor（可选）
└── SubmitBar
```

不同工具的预览策略：

| 工具类型 | 预览内容 |
|----------|----------|
| 风格迁移 | 底图 + 风格图 |
| 局部重绘 | 底图 + 蒙版图层 |
| 文生图（扩展） | prompt 摘要 + 占位图 |

当工具没有自定义 Preview 时，中栏展示 `DefaultPreview` 空状态：

```text
请选择图片或填写参数后查看预览
```

提交按钮状态：

| 状态 | 表现 |
|------|------|
| 表单未通过校验 | 禁止提交或提交时报错 |
| 正在提交 | Loading |
| 提交成功 | 清理 loading，右栏插入 queued 任务 |
| 提交失败 | 显示错误信息，不插入任务 |

---

## 七、RightPanel 规范

`RightPanel` 展示任务历史和状态。

结构：

```text
RightPanel
├── TaskFilterTabs
└── TaskList
    └── TaskCard
```

筛选 Tab：

| Tab | 规则 |
|-----|------|
| 全部 | 展示所有任务 |
| 进行中 | `created` / `queued` / `dispatching` / `running` / `retrying` |
| 已完成 | `succeeded` |
| 失败 | `failed` |
| 收藏 | `favorite === true` |

MVP 可只展示「全部」，但组件结构建议保留 `TaskFilterTabs`，便于第二版扩展。MVP store 见 [WebSocket推送示例.md](./examples/WebSocket推送示例.md)。

---

## 八、TaskCard 规范

`TaskCard` 展示单个任务快照。

推荐字段：

| 字段 | 来源 |
|------|------|
| 任务标题 | `toolName` |
| 状态 | `status` |
| 进度 | `progress` |
| 输入预览 | `taskSubmitParams.refImageList[0]` |
| 输出预览 | `taskCallbackParams.imageUrlList[0]` |
| 错误信息 | `errorMessage` |
| 创建时间 | `createdAt` |

文生图等无底图工具：`refImageList` 为空时显示占位图。

状态展示：

| status | 文案 |
|--------|------|
| created | 已创建 |
| queued | 排队中 |
| dispatching | 准备调度 |
| running | 生成中 |
| succeeded | 已完成 |
| failed | 失败 |
| canceled | 已取消 |
| retrying | 重试中 |

操作按钮：

| 操作 | MVP | 第二版 |
|------|-----|--------|
| 查看详情 | 可选 | 推荐 |
| 收藏 | 不做 | 支持 |
| 重跑 | 不做 | 支持 |
| 取消 | 不做 | 支持 |

---

## 九、主交互流程

### 9.1 创建任务

```text
用户填写表单
  → 点击提交
  → 当前工具 validate
  → 当前工具 buildRequest
  → taskStore.createTask
  → POST /api/v1/images/generations/tasks
  → 右栏插入新任务
  → WebSocket 后续更新任务状态
```

### 9.2 WebSocket 更新

```text
main.ts 建立 WebSocket（带 token）
  → 收到 task.created / task.updated / task.succeeded / task.failed
  → taskStore.upsertTask(task)
  → 收到 task.deleted → taskStore.removeTask(taskId)
  → 重连成功后 fetchTasks 补齐
```

详见 [details/WebSocket推送机制.md](./details/WebSocket推送机制.md)。

### 9.3 右栏初始化

右栏挂载时必须拉历史任务：

```ts
onMounted(() => {
  taskStore.fetchTasks()
})
```

原因：

1. 避免刷新页面后右栏为空。
2. 避免 WebSocket 连接前错过任务状态。
3. 保证服务端数据库是最终状态来源。

---

## 十、验收清单

### 布局验收

```text
□ 首页为左中右三栏
□ 左栏宽度稳定，不被中栏内容挤压
□ 中栏图片区域不会撑破页面
□ 右栏任务列表可滚动
□ 页面高度为 100vh，不出现整体页面异常滚动
```

### 交互验收

```text
□ 切换工具后表单重置为默认值
□ 上传图片后表单字段写入 URL
□ 提交前会执行工具校验
□ 提交成功后右栏立即出现任务
□ WebSocket 推送后 TaskCard 状态更新
□ 刷新页面后右栏能拉取历史任务
```

### 状态验收

```text
□ queued / running 显示进度
□ succeeded 显示输出图片
□ failed 显示错误信息
□ 无输出图时显示占位
□ 无任务时显示 EmptyState
```

---

## 十一、非目标

第一版不做：

1. 复杂低代码表单引擎
2. 拖拽式布局配置
3. 微前端
4. GraphQL
5. 深色模式
6. 移动端完整适配
7. 前端直接接 RocketMQ
8. 前端生成 `innerTaskId`
