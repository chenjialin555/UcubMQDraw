from datetime import datetime
from uuid import uuid4


def generate_task_id() -> str:
    date_part = datetime.now().strftime("%Y%m%d")
    random_part = uuid4().hex[:10]
    return f"ucub_task_{date_part}_{random_part}"


def generate_inner_task_id() -> str:
    date_part = datetime.now().strftime("%Y%m%d")
    random_part = uuid4().hex[:10]
    return f"inner_{date_part}_{random_part}"
