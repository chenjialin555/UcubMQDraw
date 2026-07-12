# WebSocket 推送机制

> 消息格式权威定义见 [API接口.md](../API接口.md#六websocket)。

## 一、地址

```text
ws://{host}/api/v1/ws/tasks
```

前端环境变量：`VITE_WS_URL=ws://localhost:8000/api/v1/ws/tasks`

## 二、消息格式

服务端只推送一种业务消息：

```json
{
  "type": "task_update",
  "task": { }
}
```

`task` 结构与 `TaskResponse` 一致（camelCase），详见 API 文档。

客户端无需发送业务消息，保持连接即可（可 `receive_text` 维持心跳）。

## 三、前端连接（`utils/ws.ts`）

```ts
import { useTaskStore } from '@/stores/taskStore'

let socket: WebSocket | null = null
let reconnectTimer: number | null = null

export function connectTaskWebSocket() {
  const taskStore = useTaskStore()
  const wsUrl = import.meta.env.VITE_WS_URL

  if (socket) socket.close()

  socket = new WebSocket(wsUrl)

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
    if (reconnectTimer) window.clearTimeout(reconnectTimer)
    reconnectTimer = window.setTimeout(() => connectTaskWebSocket(), 3000)
  }

  socket.onerror = error => console.error('[WS] error', error)
}
```

`main.ts` 挂载后调用 `connectTaskWebSocket()`。

## 四、taskStore.upsertTask

```text
收到 task_update
  → 列表中已有 taskId：合并更新
  → 没有：插入列表头部
```

右栏 `TaskList` 绑定 `taskStore.filteredTasks`。**挂载时务必 `fetchTasks()`** 拉历史，防止 WS 漏消息。

## 五、后端 WebSocketManager

```python
class WebSocketManager:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.connections:
            self.connections.remove(websocket)

    async def broadcast(self, data: dict):
        disconnected = []
        for ws in self.connections:
            try:
                await ws.send_text(json.dumps(data, ensure_ascii=False))
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(ws)

    def broadcast_task_update(self, task):
        data = {"type": "task_update", "task": task.to_response_dict()}
        # 同步上下文中需调度到 event loop（BackgroundTasks / anyio.from_thread）
```

## 六、WebSocket API

```python
@router.websocket("/api/v1/ws/tasks")
async def task_websocket(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
```

## 七、谁触发推送

| 时机 | 调用方 |
|------|--------|
| 创建任务后 | `task_service.create_task` |
| Mock 每步进度 | `mock_task_runner` |
| imggen 回调后 | `handle_imggen_callback` |

## 八、注意事项

1. **同步函数里广播**：Mock 跑在后台线程，需用 `asyncio.run_coroutine_threadsafe` 或统一走 async service
2. **第一版不做复杂心跳**：断线 3 秒重连 + 手动刷新列表即可
3. **多 Tab**：每个 Tab 各建一条 WS，广播会推给所有连接

**完整可复制代码** → [examples/WebSocket推送示例.md](../examples/WebSocket推送示例.md)
