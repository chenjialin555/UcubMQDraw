import random
import threading
import time

from ucub_mqdraw.models import TaskStatus
from ucub_mqdraw.store import update_task


def simulate_task_progress(task_id: str) -> None:
    """
    前端演示用任务状态模拟。

    正式环境中，该状态应由：
    FastAPI -> RocketMQ -> imggen -> callback -> WebSocket
    这条链路驱动。
    """
    steps = [
        (TaskStatus.QUEUED, 5),
        (TaskStatus.DISPATCHING, 15),
        (TaskStatus.RUNNING, 30),
        (TaskStatus.RUNNING, 50),
        (TaskStatus.RUNNING, 75),
        (TaskStatus.RUNNING, 90),
        (TaskStatus.COMPLETED, 100),
    ]

    for status, progress in steps:
        time.sleep(random.uniform(0.5, 1.2))
        update_task(task_id, status=status, progress=progress)

    update_task(
        task_id,
        status=TaskStatus.COMPLETED,
        progress=100,
        output_preview="https://images.unsplash.com/photo-1547891654-e66ed7ebb968?w=600",
        cost_time=round(random.uniform(8, 25), 2),
    )


def start_mock_task(task_id: str) -> None:
    thread = threading.Thread(
        target=simulate_task_progress,
        args=(task_id,),
        daemon=True,
    )
    thread.start()
