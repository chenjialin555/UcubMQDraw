# 前端 HTTP 封装示例

> 本文提供可复制的 `http.ts`、`auth.ts`、`task.ts` 示例。
> **先实现 Phase 1**（register/login/guest/me + 带 token 的 task API），Phase 2 再补改密码等。
> 阅读顺序 → [代码阅读指南.md](../代码阅读指南.md)

## 一、目录位置

```text
frontend/src/api/
├── http.ts
├── auth.ts
├── task.ts
└── upload.ts
```

| 文件 | 职责 |
|------|------|
| `http.ts` | axios 实例、**自动带 Authorization**、统一错误提取 |
| `auth.ts` | 注册、登录、游客、me、改昵称、改密码 |
| `task.ts` | 任务 CRUD 与操作 |
| `upload.ts` | 图片上传 |

---

## 二、环境变量

`frontend/.env.development` 示例：

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/api/v1/ws/tasks
```

`VITE_API_BASE_URL` 只包含后端域名，**不包含**具体 API path。

正确：

```text
http://localhost:8000
```

错误：

```text
http://localhost:8000/api/v1
```

---

## 三、`src/api/http.ts`

```ts
import axios, { AxiosError } from 'axios'

export interface ApiErrorPayload {
  detail?: string
  message?: string
  error?: string
}

function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError<ApiErrorPayload>(error)) {
    const data = error.response?.data

    return (
      data?.message ||
      data?.detail ||
      data?.error ||
      error.message ||
      '请求失败'
    )
  }

  if (error instanceof Error) {
    return error.message
  }

  return '请求失败'
}

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
})

http.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  response => response.data,
  (error: AxiosError<ApiErrorPayload>) => {
    return Promise.reject(new Error(extractErrorMessage(error)))
  },
)
```

说明：

1. 成功响应直接返回 `response.data`，业务代码不需要再写 `.data`。
2. 失败响应统一转为 `Error`，便于 `ElMessage.error(err.message)`。
3. 错误优先级：`message` → `detail` → `error` → axios message。
4. 后端 FastAPI 常见错误字段是 `detail` 或 `{ code, message }`（见 [API接口.md](../API接口.md#十五错误响应)）。

---

## 四、`src/api/auth.ts`

```ts
import { http } from './http'
import type { AuthResponse, CurrentUser, RegisterLoginRequest } from '@/types/auth'

export function register(data: RegisterLoginRequest): Promise<AuthResponse> {
  return http.post('/api/v1/auth/register', data)
}

export function login(data: RegisterLoginRequest): Promise<AuthResponse> {
  return http.post('/api/v1/auth/login', data)
}

export function loginAsGuest(): Promise<AuthResponse> {
  return http.post('/api/v1/auth/guest')
}

export function fetchMe(): Promise<CurrentUser> {
  return http.get('/api/v1/auth/me')
}

export function updateNickname(nickname: string): Promise<CurrentUser> {
  return http.patch('/api/v1/auth/me', { nickname })
}

export function changePassword(oldPassword: string, newPassword: string) {
  return http.post('/api/v1/auth/password/change', { oldPassword, newPassword })
}

export function logout() {
  return http.post('/api/v1/auth/logout')
}
```

---

## 五、任务类型建议

建议集中放在 `src/types/task.ts`：

```ts
export type TaskStatus =
  | 'created'
  | 'queued'
  | 'dispatching'
  | 'running'
  | 'succeeded'
  | 'failed'
  | 'canceled'

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

export interface CreateTaskRequest {
  toolKey: string
  params: Record<string, unknown>
}

export interface TaskListParams {
  page?: number
  pageSize?: number
  status?: TaskStatus
}

export interface TaskListResponse {
  items: GenerationTask[]
  page: number
  pageSize: number
  total: number
}
```

状态枚举见 [API接口.md](../API接口.md#十一任务状态枚举)。

---

## 六、`src/api/task.ts`

### 6.1 核心接口

```ts
import { http } from './http'
import type {
  CreateTaskRequest,
  GenerationTask,
  TaskListParams,
  TaskListResponse,
} from '@/types/task'

/** 创建生图任务 */
export function createTask(data: CreateTaskRequest): Promise<GenerationTask> {
  return http.post('/api/v1/images/generations/tasks', data)
}

/** 分页查询当前用户任务列表 */
export function listTasks(params: TaskListParams = {}): Promise<TaskListResponse> {
  return http.get('/api/v1/images/generations/tasks', { params })
}

/** 查询单条任务详情 */
export function getTask(taskId: string): Promise<GenerationTask> {
  return http.get(`/api/v1/images/generations/tasks/${taskId}`)
}

/** 软删除任务 */
export function deleteTask(taskId: string): Promise<void> {
  return http.delete(`/api/v1/images/generations/tasks/${taskId}`)
}

/** 再次生成：复制 taskSubmitParams，创建全新 taskId */
export function rerunTask(taskId: string): Promise<GenerationTask> {
  return http.post(`/api/v1/images/generations/tasks/${taskId}/rerun`)
}

/** 取消进行中任务 */
export function cancelTask(taskId: string): Promise<GenerationTask> {
  return http.post(`/api/v1/images/generations/tasks/${taskId}/cancel`)
}

/** 切换收藏 */
export function favoriteTask(
  taskId: string,
  favorite: boolean,
): Promise<GenerationTask> {
  return http.patch(`/api/v1/images/generations/tasks/${taskId}/favorite`, {
    favorite,
  })
}
```

### 6.2 边界说明

```text
创建 / 删除 / 再次生成 / 取消 / 收藏 → HTTP
任务状态通知 → WebSocket（task.created / task.updated / …）
不在 WebSocket 里发送 delete / rerun 等业务指令
```

---

## 七、`src/api/upload.ts`

```ts
import { http } from './http'

/** 上传接口响应，字段以 API 文档为准 */
export interface UploadResult {
  url: string
}

/**
 * 上传单张图片
 * @param file 本地 File 对象
 * @returns OSS 可访问 URL
 */
export function uploadImage(file: File): Promise<UploadResult> {
  const formData = new FormData()
  formData.append('file', file)

  return http.post('/api/v1/uploads/images', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}
```

请求/响应契约 → [API接口.md](../API接口.md#三上传图片)。

组件侧用法 → [OSS上传示例.md](./OSS上传示例.md)。

---

## 八、authStore 与 bootstrap（Phase 1 精简）

Phase 1 只需：`login` / `loginAsGuest` / `fetchMe` / `logout`（前端清 token）。

完整 bootstrap 与 authStore 见 [用户与鉴权设计.md §十六](../details/用户与鉴权设计.md#十六前端改造)。**不要一上来抄 Phase 2 的改昵称/改密码。**

---

## 九、在页面中的典型用法

```ts
import { ElMessage } from 'element-plus'
import { useTaskStore } from '@/stores/taskStore'

const taskStore = useTaskStore()

async function submit() {
  const error = currentTool.value.validate(form.value)
  if (error) {
    ElMessage.warning(error)
    return
  }

  try {
    const request = currentTool.value.buildRequest(form.value)
    await taskStore.createTask(request)
    ElMessage.success('任务已提交')
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '提交失败')
  }
}
```

`taskStore.createTask` 内部调用 `createTask()`，成功后 `upsertTask` 插入右栏。见 [WebSocket推送示例.md](./WebSocket推送示例.md)。

---

## 十、与现行规范的边界

| 项 | 说明 |
|----|------|
| 请求体 | 只传 `toolKey` + `params`，不传 `innerTaskId` / `workflow` |
| 响应体 | 不含 `taskDispatchParams` |
| 错误处理 | 统一走 `http.ts` 拦截器，不在每个 API 函数重复解析 |
| retry / cancel / favorite | 正式版走 HTTP，见 [API接口.md](../API接口.md) |

---

## 十一、自检清单

```text
□ baseURL 不含 /api/v1 前缀
□ 成功响应已 unwrap，调用方不再 .data
□ createTask / listTasks 路径与 API接口.md 一致
□ 上传使用 multipart/form-data
□ 未在 http 层写业务逻辑（如不根据 toolKey 分支）
□ retry / rerun / cancel / favorite 走 HTTP，不在 WS 发业务指令
```
