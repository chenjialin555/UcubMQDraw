import asyncio
import json
import threading

import websockets

from ucub_mqdraw.config import BACKEND_WS_URL
from ucub_mqdraw.models import TaskStatus
from ucub_mqdraw.store import update_task


def _normalize_status(raw_status: str) -> TaskStatus:
    mapping = {
        "created": TaskStatus.CREATED,
        "queued": TaskStatus.QUEUED,
        "dispatching": TaskStatus.DISPATCHING,
        "running": TaskStatus.RUNNING,
        "success": TaskStatus.COMPLETED,
        "completed": TaskStatus.COMPLETED,
        "fail": TaskStatus.FAILED,
        "failed": TaskStatus.FAILED,
        "cancelled": TaskStatus.CANCELLED,
        "retrying": TaskStatus.RETRYING,
    }
    return mapping.get(raw_status, TaskStatus.RUNNING)


async def websocket_loop() -> None:
    """
    监听 UcubMQDraw 后端推送的业务任务状态。
    不连接 imggen，不暴露 innerTaskId。
    """
    while True:
        try:
            async with websockets.connect(BACKEND_WS_URL) as websocket:
                print(f"[WS] connected: {BACKEND_WS_URL}")

                async for message in websocket:
                    data = json.loads(message)
                    task_id = data.get("taskId")
                    if not task_id:
                        continue

                    image_list = data.get("imageUrlList") or []
                    output_preview = image_list[0] if image_list else ""

                    update_task(
                        task_id,
                        status=_normalize_status(data.get("status", "running")),
                        progress=int(data.get("progress", 0)),
                        output_preview=output_preview,
                        error_message=data.get("errorMsg") or "",
                        cost_time=data.get("costTime"),
                    )

        except Exception as exc:
            print(f"[WS] disconnected: {exc}")
            await asyncio.sleep(3)


def start_websocket_listener() -> None:
    thread = threading.Thread(
        target=lambda: asyncio.run(websocket_loop()),
        daemon=True,
    )
    thread.start()
