# WebSocket 推送示例

> 设计说明见 [WebSocket推送机制.md](../details/WebSocket推送机制.md)。消息格式见 [API接口.md](../API接口.md#六websocket)。

## 一、文件清单

```text
frontend/src/
├── utils/ws.ts
├── stores/taskStore.ts
└── main.ts

backend/app/
├── services/websocket_manager.py
└── api/websocket_api.py
```

## 二、前端 ws.ts

```ts
import { useTaskStore } from '@/stores/taskStore'

let socket: WebSocket | null = null
let reconnectTimer: number | null = null

export function connectTaskWebSocket() {
  const taskStore = useTaskStore()
  const wsUrl = import.meta.env.VITE_WS_URL

  if (socket) socket.close()

  socket = new WebSocket(wsUrl)

  socket.onopen = () => {
    console.log('[WS] connected')
  }

  socket.onmessage = event => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'task_update' && data.task) {
        taskStore.upsertTask(data.task)
      }
    } catch (error) {
      console.error('[WS] invalid message', error)
    }
  }

  socket.onclose = () => {
    reconnectTimer = window.setTimeout(() => connectTaskWebSocket(), 3000)
  }

  socket.onerror = error => console.error('[WS] error', error)
}
```

## 三、main.ts 启动连接

```ts
import { connectTaskWebSocket } from './utils/ws'

app.mount('#app')
connectTaskWebSocket()
```

## 四、taskStore.upsertTask（MVP 版）

```ts
upsertTask(task: GenerationTask) {
  const index = this.tasks.findIndex(item => item.taskId === task.taskId)
  if (index >= 0) {
    this.tasks[index] = { ...this.tasks[index], ...task }
  } else {
    this.tasks.unshift(task)
  }
},

async createTask(data: CreateTaskRequest) {
  const task = await createTask(data)
  this.upsertTask(task)
  return task
},
```

## 五、TaskList 挂载时拉历史

```vue
<script setup lang="ts">
import { onMounted } from 'vue'
import { useTaskStore } from '@/stores/taskStore'

const taskStore = useTaskStore()

onMounted(() => {
  taskStore.fetchTasks()
})
</script>
```

## 六、后端 websocket_manager.py

```python
import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self.connections: list[WebSocket] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.connections:
            self.connections.remove(websocket)

    async def broadcast(self, data: dict) -> None:
        disconnected: list[WebSocket] = []
        text = json.dumps(data, ensure_ascii=False)
        for ws in self.connections:
            try:
                await ws.send_text(text)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(ws)

    async def broadcast_task_update_async(self, task: Any) -> None:
        await self.broadcast({
            "type": "task_update",
            "task": task.to_response_dict(),
        })

    def broadcast_task_update(self, task: Any) -> None:
        """Mock 线程等同步上下文也可安全调用"""
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.broadcast_task_update_async(task),
                self._loop,
            )
        else:
            logger.warning("event loop 未绑定，跳过 WS 推送")


websocket_manager = WebSocketManager()
```

## 七、main.py 绑定 event loop

```python
@app.on_event("startup")
async def on_startup():
    websocket_manager.bind_loop(asyncio.get_running_loop())
    if not settings.USE_MOCK:
        start_callback_consumer()
```

或使用 FastAPI `lifespan` 在启动时 `bind_loop`。

## 八、websocket_api.py

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.websocket_manager import websocket_manager

router = APIRouter()


@router.websocket("/api/v1/ws/tasks")
async def task_websocket(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # 保持连接
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
```

## 九、推送消息示例

```json
{
  "type": "task_update",
  "task": {
    "taskId": "ucub_task_20260712_abc123",
    "toolKey": "style_transfer",
    "toolName": "风格迁移",
    "status": "running",
    "progress": 60,
    "taskSubmitParams": {
      "prompt": "赛博朋克",
      "refImageList": ["http://...", "http://..."]
    },
    "taskCallbackParams": {},
    "errorMessage": "",
    "costTime": null,
    "favorite": false,
    "createdAt": "2026-07-12 16:00:00",
    "updatedAt": "2026-07-12 16:01:00"
  }
}
```

## 十、谁触发推送

```text
task_service.create_task()     → 创建后推一次
mock_task_runner 每步更新      → 推 progress
handle_imggen_callback()       → 完成后推最终结果
```
