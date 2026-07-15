# imggen-stub 示例

> 设计说明 → [imggen-stub联调模式设计.md](../details/imggen-stub联调模式设计.md)

## 一、目录

```text
imggen-stub/
├── README.md
├── pyproject.toml
├── .env.example
└── app/
    ├── __init__.py
    ├── main.py
    ├── config.py
    ├── rocketmq_client.py
    └── stub_worker.py
```

## 二、`.env.example`

```env
ROCKETMQ_NAME_SERVER=
ROCKETMQ_ACCESS_KEY=
ROCKETMQ_SECRET_KEY=

ROCKETMQ_CONSUMER_GROUP=imggen-stub-consumer
ROCKETMQ_PRODUCER_GROUP=imggen-stub-producer
ROCKETMQ_TOPIC_TASK=ucub_imggen_api_task
ROCKETMQ_TOPIC_CALLBACK=ucub_imggen_callback

IMGGEN_STUB_SLEEP_SECONDS=3
IMGGEN_STUB_RESULT=success
IMGGEN_STUB_OUTPUT_URL=http://object.intuly.com/ai/img/build/mock-output.png
IMGGEN_STUB_SEND_PROGRESS=false
```

## 三、config.py

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ROCKETMQ_NAME_SERVER: str = ""
    ROCKETMQ_ACCESS_KEY: str = ""
    ROCKETMQ_SECRET_KEY: str = ""
    ROCKETMQ_CONSUMER_GROUP: str = "imggen-stub-consumer"
    ROCKETMQ_PRODUCER_GROUP: str = "imggen-stub-producer"
    ROCKETMQ_TOPIC_TASK: str = "ucub_imggen_api_task"
    ROCKETMQ_TOPIC_CALLBACK: str = "ucub_imggen_callback"

    IMGGEN_STUB_SLEEP_SECONDS: float = 3
    IMGGEN_STUB_RESULT: str = "success"  # success | failed
    IMGGEN_STUB_OUTPUT_URL: str = (
        "http://object.intuly.com/ai/img/build/mock-output.png"
    )
    IMGGEN_STUB_SEND_PROGRESS: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
```

## 四、stub_worker.py

```python
import json
import logging
import time

from rocketmq.client import Message, Producer, PushConsumer

from app.config import settings

logger = logging.getLogger(__name__)

_producer: Producer | None = None


def start_producer() -> None:
    global _producer
    producer = Producer(settings.ROCKETMQ_PRODUCER_GROUP)
    producer.set_name_server_address(settings.ROCKETMQ_NAME_SERVER)
    producer.set_session_credentials(
        settings.ROCKETMQ_ACCESS_KEY,
        settings.ROCKETMQ_SECRET_KEY,
        "",
    )
    producer.start()
    _producer = producer


def send_callback(payload: dict) -> None:
    assert _producer is not None
    msg = Message(settings.ROCKETMQ_TOPIC_CALLBACK)
    msg.set_keys(payload.get("innerTaskId", ""))
    msg.set_tags("imggen-stub")
    msg.set_body(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    _producer.send_sync(msg)


def on_task_message(msg) -> int:
    try:
        task = json.loads(msg.body.decode("utf-8"))
        inner_task_id = task.get("innerTaskId")
        if not inner_task_id:
            logger.warning("missing innerTaskId: %s", msg.body)
            return 0

        logger.info("imggen-stub received task: %s", inner_task_id)

        if settings.IMGGEN_STUB_SEND_PROGRESS:
            send_callback({
                "innerTaskId": inner_task_id,
                "status": "running",
                "progress": 40,
                "message": "imggen-stub started",
            })

        start = time.time()
        time.sleep(settings.IMGGEN_STUB_SLEEP_SECONDS)
        cost_time = round(time.time() - start, 3)

        if settings.IMGGEN_STUB_RESULT == "failed":
            send_callback({
                "innerTaskId": inner_task_id,
                "status": "failed",
                "costTime": cost_time,
                "imageUrlList": [],
                "errorMsg": "imggen-stub simulated failure",
            })
        else:
            send_callback({
                "innerTaskId": inner_task_id,
                "status": "success",
                "costTime": cost_time,
                "imageUrlList": [settings.IMGGEN_STUB_OUTPUT_URL],
                "errorMsg": "",
            })
        return 0
    except Exception:
        logger.exception("imggen-stub handle task failed")
        return 1


def start_consumer():
    consumer = PushConsumer(settings.ROCKETMQ_CONSUMER_GROUP)
    consumer.set_name_server_address(settings.ROCKETMQ_NAME_SERVER)
    consumer.set_session_credentials(
        settings.ROCKETMQ_ACCESS_KEY,
        settings.ROCKETMQ_SECRET_KEY,
        "",
    )
    consumer.subscribe(settings.ROCKETMQ_TOPIC_TASK, on_task_message)
    consumer.start()
    logger.info("imggen-stub consumer started")
    return consumer
```

## 五、main.py

```python
import logging
import time

from app.stub_worker import start_consumer, start_producer

logging.basicConfig(level=logging.INFO)


def main() -> None:
    start_producer()
    start_consumer()
    logging.info("imggen-stub running; Ctrl+C to stop")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("imggen-stub stopped")


if __name__ == "__main__":
    main()
```

## 六、UcubMQDraw 侧（对照）

创建任务后**始终**投递，无 `USE_MOCK`：

```python
mq_service.send(task_dispatch_params, tool_key=tool.key)
```

Callback Consumer 在 `mq_enabled()` 时启动：

```python
if mq_enabled():
    start_callback_consumer()
```
