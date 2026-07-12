# WebSocket 推送示例

> 设计说明见 [WebSocket推送机制.md](../details/WebSocket推送机制.md)。消息格式见 [API接口.md](../API接口.md#十websocket)。

## 一、文件清单

```text
frontend/src/
├── utils/ws.ts
├── stores/taskStore.ts
└── main.ts

backend/app/
├── services/websocket_manager.py
├── services/ws_event_bus.py      # 可选：Redis Pub/Sub
└── api/websocket_api.py
```

---

## 二、前端 ws.ts（正式版）

```ts
import { useTaskStore } from '@/stores/taskStore'

let socket: WebSocket | null = null
let reconnectTimer: number | null = null
let reconnectAttempt = 0
let manuallyClosed = false
let heartbeatTimer: number | null = null

const MAX_RECONNECT_DELAY = 30000

function getWsUrl() {
  const base = import.meta.env.VITE_WS_URL
  const token = localStorage.getItem('access_token')
  if (!token) return base
  const sep = base.includes('?') ? '&' : '?'
  return `${base}${sep}token=${encodeURIComponent(token)}`
}

function getReconnectDelay() {
  const delay = Math.min(1000 * 2 ** reconnectAttempt, MAX_RECONNECT_DELAY)
  reconnectAttempt += 1
  return delay
}

function clearHeartbeat() {
  if (heartbeatTimer) {
    window.clearInterval(heartbeatTimer)
    heartbeatTimer = null
  }
}

function startHeartbeat() {
  clearHeartbeat()
  heartbeatTimer = window.setInterval(() => {
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: 'system.ping' }))
    }
  }, 30000)
}

function handleMessage(raw: string) {
  const taskStore = useTaskStore()
  const message = JSON.parse(raw)

  switch (message.type) {
    case 'task.created':
    case 'task.updated':
    case 'task.succeeded':
    case 'task.failed':
    case 'task.favorite_set':
      if (message.task) {
        taskStore.upsertTask(message.task)
      }
      break

    case 'task.deleted':
      if (message.taskId) {
        taskStore.removeTask(message.taskId)
      }
      break

    case 'system.pong':
      break

    default:
      console.warn('[WS] unknown message', message)
  }
}

export function connectTaskWebSocket() {
  const taskStore = useTaskStore()
  manuallyClosed = false

  if (socket && socket.readyState === WebSocket.OPEN) {
    return
  }

  socket = new WebSocket(getWsUrl())

  socket.onopen = async () => {
    reconnectAttempt = 0
    await taskStore.fetchTasks()
    startHeartbeat()
  }

  socket.onmessage = event => {
    try {
      handleMessage(event.data)
    } catch (error) {
      console.error('[WS] invalid message', error)
    }
  }

  socket.onclose = () => {
    clearHeartbeat()
    if (manuallyClosed) return

    const delay = getReconnectDelay()
    reconnectTimer = window.setTimeout(() => {
      connectTaskWebSocket()
    }, delay)
  }

  socket.onerror = error => {
    console.error('[WS] error', error)
  }
}

export function disconnectTaskWebSocket() {
  manuallyClosed = true

  if (reconnectTimer) {
    window.clearTimeout(reconnectTimer)
    reconnectTimer = null
  }

  clearHeartbeat()
  socket?.close()
  socket = null
}
```

---

## 三、main.ts 启动连接

```ts
import { connectTaskWebSocket } from './utils/ws'

app.mount('#app')
connectTaskWebSocket()
```

---

## 四、taskStore（正式版核心）

```ts
import { defineStore } from 'pinia'
import type { GenerationTask, CreateTaskRequest } from '@/types/task'
import {
  listTasks,
  createTask,
  deleteTask,
  rerunTask,
  cancelTask,
  favoriteTask,
} from '@/api/task'

const RUNNING_STATUSES = ['created', 'queued', 'dispatching', 'running']

export const useTaskStore = defineStore('task', {
  state: () => ({
    tasks: [] as GenerationTask[],
    currentFilter: '全部' as string,
    loading: false,
    page: 1,
    pageSize: 20,
    total: 0,
  }),

  getters: {
    filteredTasks(state) {
      if (state.currentFilter === '进行中') {
        return state.tasks.filter(t => RUNNING_STATUSES.includes(t.status))
      }
      if (state.currentFilter === '已完成') {
        return state.tasks.filter(t => t.status === 'succeeded')
      }
      if (state.currentFilter === '失败') {
        return state.tasks.filter(t => t.status === 'failed')
      }
      if (state.currentFilter === '收藏') {
        return state.tasks.filter(t => t.favorite)
      }
      return state.tasks
    },
  },

  actions: {
    sortTasks() {
      this.tasks.sort(
        (a, b) =>
          new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
      )
    },

    upsertTask(task: GenerationTask) {
      const index = this.tasks.findIndex(item => item.taskId === task.taskId)
      if (index >= 0) {
        this.tasks[index] = { ...this.tasks[index], ...task }
      } else {
        this.tasks.push(task)
      }
      this.sortTasks()
    },

    removeTask(taskId: string) {
      this.tasks = this.tasks.filter(task => task.taskId !== taskId)
    },

    async fetchTasks() {
      this.loading = true
      try {
        const res = await listTasks({
          page: this.page,
          pageSize: this.pageSize,
        })
        this.tasks = res.items
        this.total = res.total
        this.sortTasks()
      } finally {
        this.loading = false
      }
    },

    async createTask(data: CreateTaskRequest) {
      const task = await createTask(data)
      this.upsertTask(task)
      return task
    },

    async deleteTask(taskId: string) {
      await deleteTask(taskId)
      this.removeTask(taskId)
    },

    async rerunTask(taskId: string) {
      const task = await rerunTask(taskId)
      this.upsertTask(task)
      return task
    },

    async cancelTask(taskId: string) {
      const task = await cancelTask(taskId)
      this.upsertTask(task)
      return task
    },

    async setFavorite(taskId: string, favorite: boolean) {
      const task = await favoriteTask(taskId, favorite)
      this.upsertTask(task)
      return task
    },
  },
})
```

删除流程：HTTP DELETE 成功后本地可先 `removeTask`；其他 Tab 靠 `task.deleted` WS 同步。

---

## 五、后端 websocket_manager.py（正式版）

```python
import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self.connections: dict[str, set[WebSocket]] = {}
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.setdefault(user_id, set()).add(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        user_connections = self.connections.get(user_id)
        if not user_connections:
            return
        user_connections.discard(websocket)
        if not user_connections:
            self.connections.pop(user_id, None)

    async def send_to_user(self, user_id: str, payload: dict) -> None:
        connections = list(self.connections.get(user_id, set()))
        disconnected: list[WebSocket] = []
        text = json.dumps(payload, ensure_ascii=False)

        for ws in connections:
            try:
                await ws.send_text(text)
            except Exception:
                disconnected.append(ws)

        for ws in disconnected:
            self.disconnect(user_id, ws)

    async def send_task_event_async(
        self,
        user_id: str,
        event_type: str,
        task: Any,
        **extra,
    ) -> None:
        await self.send_to_user(user_id, {
            "type": event_type,
            "eventId": generate_event_id(),
            "serverTime": now_iso(),
            "task": task.to_response_dict(),
            **extra,
        })

    def send_task_event(self, user_id: str, event_type: str, task: Any) -> None:
        """Mock 线程等同步上下文安全调用"""
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.send_task_event_async(user_id, event_type, task),
                self._loop,
            )
        else:
            logger.warning("event loop 未绑定，跳过 WS 推送")


websocket_manager = WebSocketManager()
```

---

## 六、websocket_api.py

```python
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.auth import get_current_user_from_ws
from app.services.websocket_manager import websocket_manager

router = APIRouter()


@router.websocket("/api/v1/ws/tasks")
async def task_websocket(
    websocket: WebSocket,
    token: str | None = Query(default=None),
):
    user = await get_current_user_from_ws(websocket, token)
    user_id = user.user_id

    await websocket_manager.connect(user_id, websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if msg.get("type") == "system.ping":
                await websocket.send_json({
                    "type": "system.pong",
                    "serverTime": now_iso(),
                })
    except WebSocketDisconnect:
        websocket_manager.disconnect(user_id, websocket)
```

---

## 七、推送消息示例

### task.updated

```json
{
  "type": "task.updated",
  "eventId": "evt_20260712_abc",
  "serverTime": "2026-07-12T16:01:00+08:00",
  "task": {
    "taskId": "ucub_task_20260712_abc123",
    "toolKey": "style_transfer",
    "toolName": "风格迁移",
    "status": "running",
    "progress": 60,
    "taskSubmitParams": { "prompt": "赛博朋克", "refImageList": ["http://..."] },
    "taskCallbackParams": {},
    "errorMessage": "",
    "costTime": null,
    "favorite": false,
    "createdAt": "2026-07-12T16:00:00+08:00",
    "updatedAt": "2026-07-12T16:01:00+08:00"
  }
}
```

### task.deleted

```json
{
  "type": "task.deleted",
  "eventId": "evt_20260712_def",
  "serverTime": "2026-07-12T16:05:00+08:00",
  "taskId": "ucub_task_20260712_abc123"
}
```

---

## 八、谁触发推送

```text
task_service.create_task()       → task.created / task.updated
mock_task_runner 每步            → task.updated
handle_imggen_callback()         → task.succeeded / task.failed / task.updated
task_service.delete_task()       → task.deleted
task_service.favorite_task()     → task.favorite_set
```

链路：

```text
业务写 DB → send_to_user(task.user_id) → 前端 upsertTask / removeTask
```

---

## 九、Redis Pub/Sub 跨实例（可选）

```python
# ws_event_bus.py 伪代码
async def publish_task_event(user_id: str, payload: dict):
    await redis.publish(f"ucub:task_events:{user_id}", json.dumps(payload))

async def subscribe_task_events():
    pubsub = redis.pubsub()
    await pubsub.psubscribe("ucub:task_events:*")
    async for message in pubsub.listen():
        user_id = extract_user_id(message.channel)
        payload = json.loads(message.data)
        await websocket_manager.send_to_user(user_id, payload)
```

Consumer 更新 DB 后 `publish`，各实例订阅并推送给本地持有的 WS 连接。

**Redis 此处不是任务队列，任务队列仍是 RocketMQ。**
