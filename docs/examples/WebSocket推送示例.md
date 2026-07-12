# WebSocket 推送示例

> 设计说明见 [WebSocket推送机制.md](../details/WebSocket推送机制.md)。
> 消息格式见 [API接口.md](../API接口.md#十一websocket)。
>
> **阅读顺序：** 先看 [代码阅读指南.md](../代码阅读指南.md) → 本章 §二最小版 → 再往下看拆文件与增强。

---

## 一、文件清单（按阶段）

### Phase 1（先实现）

```text
frontend/src/
├── ws/
│   ├── taskWsMessages.ts
│   ├── taskWsHandlers.ts
│   └── taskWsClient.ts
├── stores/taskStore.ts
├── stores/authStore.ts
└── main.ts

backend/app/
├── services/websocket_manager.py
└── api/websocket_api.py
```

### Phase 2 再加

```text
utils/guestTasks.ts
bootstrap.ts
```

### Phase 3 再加

```text
services/ws_event_bus.py    # Redis Pub/Sub
```

---

## 二、最小可读版（先看这个）

**核心就三步：** 连 WS → 收消息 → `upsertTask`。

```ts
import { useTaskStore } from '@/stores/taskStore'

let socket: WebSocket | null = null

export function connectTaskWebSocket() {
  const token = localStorage.getItem('access_token')
  const wsUrl = `${import.meta.env.VITE_WS_URL}?token=${encodeURIComponent(token || '')}`

  socket = new WebSocket(wsUrl)

  socket.onmessage = event => {
    const message = JSON.parse(event.data)
    const taskStore = useTaskStore()

    if (message.task) {
      taskStore.upsertTask(message.task)
    }

    if (message.type === 'task.deleted' && message.taskId) {
      taskStore.removeTask(message.taskId)
    }
  }
}
```

`main.ts` 里登录或 guest 成功后调用 `connectTaskWebSocket()` 即可。

正式版在最小版之上**逐步加**：断线重连 → 重连后 fetchTasks → 拆文件 → 游客过滤 → 心跳 → Redis。见下文 §四～§八。

---

## 三、taskStore 最小版（Phase 1）

```ts
upsertTask(task: GenerationTask) {
  const i = this.tasks.findIndex(t => t.taskId === task.taskId)
  if (i >= 0) this.tasks[i] = { ...this.tasks[i], ...task }
  else this.tasks.unshift(task)
},

async fetchTasks() {
  const res = await listTasks({ page: 1, pageSize: 20 })
  this.tasks = res.items
},
```

Phase 2 再加：`removeTask`、排序、筛选、`deleteTask` 等。完整版见 §七。

---

## 四、拆文件版（Phase 1 推荐结构）

一个 `ws.ts` 管十件事会难读。拆成三个文件，**每个文件只做一件事**。

### 4.1 `ws/taskWsMessages.ts` — 只管消息格式

```ts
import type { GenerationTask } from '@/types/task'

export type TaskWsMessage =
  | {
      type: 'task.created' | 'task.updated' | 'task.succeeded' | 'task.failed'
      task: GenerationTask
    }
  | { type: 'task.deleted'; taskId: string }
  | { type: 'system.pong'; serverTime?: string }

export function parseTaskWsMessage(raw: string): TaskWsMessage | null {
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}
```

### 4.2 `ws/taskWsHandlers.ts` — 只管「收到消息后更新 store」

Phase 1（无游客过滤）：

```ts
import { useTaskStore } from '@/stores/taskStore'
import type { TaskWsMessage } from './taskWsMessages'

export function handleTaskWsMessage(message: TaskWsMessage) {
  const taskStore = useTaskStore()

  switch (message.type) {
    case 'task.created':
    case 'task.updated':
    case 'task.succeeded':
    case 'task.failed':
      taskStore.upsertTask(message.task)
      break
    case 'task.deleted':
      taskStore.removeTask(message.taskId)
      break
    case 'system.pong':
      break
    default:
      console.warn('[WS] unknown message', message)
  }
}
```

Phase 2 在 `upsertTask` 前加游客判断 → 见 §五。

### 4.3 `ws/taskWsClient.ts` — 只管连接与重连

Phase 1：连接 + 指数退避重连 + 重连后 `fetchTasks`（无心跳）。

```ts
import { useAuthStore } from '@/stores/authStore'
import { useTaskStore } from '@/stores/taskStore'
import { parseTaskWsMessage } from './taskWsMessages'
import { handleTaskWsMessage } from './taskWsHandlers'

let socket: WebSocket | null = null
let reconnectTimer: number | null = null
let reconnectAttempt = 0
let manuallyClosed = false

const MAX_RECONNECT_DELAY = 30000

function getWsUrl() {
  const base = import.meta.env.VITE_WS_URL
  const token = localStorage.getItem('access_token')
  if (!token) return base
  return `${base}?token=${encodeURIComponent(token)}`
}

function getReconnectDelay() {
  const delay = Math.min(1000 * 2 ** reconnectAttempt, MAX_RECONNECT_DELAY)
  reconnectAttempt += 1
  return delay
}

export function connectTaskWebSocket() {
  const authStore = useAuthStore()
  const taskStore = useTaskStore()

  if (!authStore.accessToken) return

  if (socket?.readyState === WebSocket.OPEN || socket?.readyState === WebSocket.CONNECTING) {
    return
  }

  manuallyClosed = false
  socket = new WebSocket(getWsUrl())

  socket.onopen = async () => {
    reconnectAttempt = 0
    if (!authStore.isGuest) {
      await taskStore.fetchTasks()
    }
  }

  socket.onmessage = event => {
    const message = parseTaskWsMessage(event.data)
    if (!message) return
    handleTaskWsMessage(message)
  }

  socket.onclose = () => {
    if (manuallyClosed) return
    reconnectTimer = window.setTimeout(connectTaskWebSocket, getReconnectDelay())
  }

  socket.onerror = err => console.error('[WS] error', err)
}

export function disconnectTaskWebSocket() {
  manuallyClosed = true
  if (reconnectTimer) clearTimeout(reconnectTimer)
  socket?.close()
  socket = null
}
```

---

## 五、Phase 2 增强：游客 taskId 过滤

仅在 `taskWsHandlers.ts` 增加判断，**不必改 client**：

```ts
import { useAuthStore } from '@/stores/authStore'
import { shouldAcceptGuestTask } from '@/utils/guestTasks'

// upsertTask 前：
if (authStore.isGuest && !shouldAcceptGuestTask(message.task.taskId)) {
  return
}
```

```ts
// utils/guestTasks.ts
const KEY = 'guest_task_ids'

export function addGuestTaskId(taskId: string) {
  const ids = new Set(JSON.parse(localStorage.getItem(KEY) || '[]'))
  ids.add(taskId)
  localStorage.setItem(KEY, JSON.stringify([...ids]))
}

export function shouldAcceptGuestTask(taskId: string): boolean {
  return JSON.parse(localStorage.getItem(KEY) || '[]').includes(taskId)
}
```

---

## 六、Phase 2 增强：心跳

在 `taskWsClient.ts` 增加 `startHeartbeat` / `stopHeartbeat`，每 30s 发 `{ type: 'system.ping' }`。后端 `websocket_api.py` 回 `system.pong`。

Phase 1 **可不做心跳**，靠断线重连 + `fetchTasks` 补齐即可。

---

## 七、Phase 2：taskStore 完整 actions

在 Phase 1 的 `upsertTask` / `fetchTasks` 基础上增加：

```text
removeTask / sortTasks / filteredTasks
deleteTask / rerunTask / cancelTask / setFavorite（需对应 HTTP API）
```

实现参考此前完整 store；**第一版可只保留 upsert + fetch + create**。

---

## 八、后端（Phase 1 够用）

### websocket_manager.py

```python
class WebSocketManager:
    def __init__(self):
        self.connections: dict[str, set[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.connections.setdefault(user_id, set()).add(websocket)

    async def send_to_user(self, user_id: str, payload: dict):
        for ws in list(self.connections.get(user_id, set())):
            try:
                await ws.send_json(payload)
            except Exception:
                self.disconnect(user_id, ws)
```

### websocket_api.py

```python
@router.websocket("/api/v1/ws/tasks")
async def task_websocket(websocket: WebSocket, token: str = Query(None)):
    user = await get_current_user_from_ws(websocket, token)
    await websocket_manager.connect(user.user_id, websocket)
    try:
        while True:
            await websocket.receive_text()  # Phase 1：保持连接即可
    except WebSocketDisconnect:
        websocket_manager.disconnect(user.user_id, websocket)
```

任务变更后：

```python
await websocket_manager.send_to_user(task.user_id, {
    "type": "task.updated",
    "task": task.to_response_dict(),
})
```

---

## 九、Phase 3：Redis Pub/Sub（多实例时再读）

单进程开发 **不需要**。多实例部署时：callback 更新 DB → `publish` Redis → 各实例 `send_to_user`。

详见 [WebSocket推送机制.md §九](../details/WebSocket推送机制.md#九多实例部署)。

---

## 十、推送消息示例

```json
{
  "type": "task.updated",
  "task": {
    "taskId": "ucub_task_xxx",
    "status": "running",
    "progress": 60
  }
}
```

谁触发 → [任务状态与任务流转.md](../details/任务状态与任务流转.md#七回调后如何更新任务)。
