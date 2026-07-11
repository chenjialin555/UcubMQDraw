import threading
from typing import Dict, List, Optional

from ucub_mqdraw.models import GenerationTask, TaskStatus

_TASKS: Dict[str, GenerationTask] = {}
_LOCK = threading.Lock()

RUNNING_STATUSES = {
    TaskStatus.CREATED,
    TaskStatus.QUEUED,
    TaskStatus.DISPATCHING,
    TaskStatus.RUNNING,
    TaskStatus.RETRYING,
}


def add_task(task: GenerationTask) -> None:
    with _LOCK:
        _TASKS[task.task_id] = task


def get_task(task_id: str) -> Optional[GenerationTask]:
    with _LOCK:
        return _TASKS.get(task_id)


def update_task(task_id: str, **kwargs) -> None:
    with _LOCK:
        task = _TASKS.get(task_id)
        if not task:
            return

        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)


def list_tasks(filter_type: str = "全部") -> List[GenerationTask]:
    with _LOCK:
        tasks = list(_TASKS.values())

    tasks.sort(key=lambda item: item.created_at, reverse=True)

    if filter_type == "全部":
        return tasks

    if filter_type == "进行中":
        return [task for task in tasks if task.status in RUNNING_STATUSES]

    if filter_type == "已完成":
        return [task for task in tasks if task.status == TaskStatus.COMPLETED]

    if filter_type == "收藏":
        return [task for task in tasks if task.favorite]

    return tasks
