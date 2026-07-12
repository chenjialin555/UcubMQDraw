# RocketMQ 对接示例

> 设计说明见 [RocketMQ对接设计.md](../details/RocketMQ对接设计.md)。消息体字段以 [mq_contract.md](../mq_contract.md) 为准。

## 一、文件清单

```text
backend/app/
├── config.py                    # MQ 环境变量 + mq_enabled()
├── services/
│   ├── mq_service.py            # 选 Topic、序列化、发送
│   ├── rocketmq_client.py       # Producer 单例
│   ├── rocketmq_consumer.py     # Callback Consumer
│   ├── callback_service.py      # 处理 imggen 回调
│   └── task_service.py          # 创建任务时调用 mq_service
└── main.py                      # lifespan 启动 Consumer
```

## 二、config.py（MQ 部分）

```python
class Settings(BaseSettings):
    ROCKETMQ_NAME_SERVER: str = ""
    ROCKETMQ_PRODUCER_GROUP: str = "ucub-mqdraw-producer"
    ROCKETMQ_ACCESS_KEY: str = ""
    ROCKETMQ_SECRET_KEY: str = ""
    ROCKETMQ_TOPIC_TASK: str = "ucub_imggen_api_task"
    ROCKETMQ_TOPIC_CALLBACK: str = "ucub_imggen_callback"
    ROCKETMQ_RETRY_TIMES: int = 3
    ROCKETMQ_RETRY_BACKOFF_BASE: float = 0.5
    ROCKETMQ_RETRY_BACKOFF_MAX: float = 5.0
    USE_MOCK: bool = True


def mq_enabled() -> bool:
    return bool(
        settings.ROCKETMQ_NAME_SERVER
        and settings.ROCKETMQ_ACCESS_KEY
        and settings.ROCKETMQ_SECRET_KEY
    )
```

## 三、rocketmq_client.py

```python
import json
import logging
import time
import uuid

from rocketmq.client import Message, Producer

from app.config import settings, mq_enabled

logger = logging.getLogger(__name__)


class RocketMQSendError(Exception):
    pass


class RocketMQClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance._init_producer()
        return cls._instance

    def _init_producer(self) -> None:
        self._producer = None
        if not mq_enabled():
            logger.warning("RocketMQ 未配置，Producer 不启动")
            return
        group_name = f"{settings.ROCKETMQ_PRODUCER_GROUP}-{uuid.uuid4().hex[:8]}"
        producer = Producer(group_name)
        producer.set_name_server_address(settings.ROCKETMQ_NAME_SERVER)
        producer.set_session_credentials(
            settings.ROCKETMQ_ACCESS_KEY,
            settings.ROCKETMQ_SECRET_KEY,
            "",
        )
        producer.start()
        self._producer = producer

    def send_message(self, topic: str, body: str, *, tags: str = "", keys: str = ""):
        if not self._producer:
            raise RocketMQSendError("RocketMQ 未初始化")
        msg = Message(topic)
        msg.set_keys(keys)
        msg.set_tags(tags)
        msg.set_body(body)

        for attempt in range(1, settings.ROCKETMQ_RETRY_TIMES + 2):
            try:
                result = self._producer.send_sync(msg)
                if getattr(result, "status", -1) == 0:
                    return result
            except Exception as exc:
                if attempt > settings.ROCKETMQ_RETRY_TIMES:
                    raise RocketMQSendError(str(exc)) from exc
                time.sleep(min(
                    settings.ROCKETMQ_RETRY_BACKOFF_BASE * (2 ** (attempt - 1)),
                    settings.ROCKETMQ_RETRY_BACKOFF_MAX,
                ))

    def shutdown(self) -> None:
        if self._producer:
            self._producer.shutdown()


rocketmq_client = RocketMQClient()
```

## 四、mq_service.py

```python
import json

from app.config import settings, mq_enabled
from app.services.rocketmq_client import rocketmq_client, RocketMQSendError


class MQService:
    def send(self, payload: dict, tool_key: str) -> None:
        if not mq_enabled():
            raise RocketMQSendError("RocketMQ 未配置")
        topic = settings.ROCKETMQ_TOPIC_TASK
        body = json.dumps(payload, ensure_ascii=False)
        keys = str(payload.get("innerTaskId") or "")
        rocketmq_client.send_message(
            topic=topic,
            body=body,
            tags=tool_key,
            keys=keys,
        )


mq_service = MQService()
```

## 五、下发消息示例（风格迁移）

Handler 组装后存入 `task_dispatch_params` 并投递：

```json
{
  "innerTaskId": "inner_20260712_00001",
  "modelName": "SDXL/Flux",
  "prompt": "赛博朋克风格",
  "width": 1024,
  "height": 1024,
  "batchSize": 1,
  "refImageList": [
    "http://object.intuly.com/ai/img/build/20260712/base.png",
    "http://object.intuly.com/ai/img/build/20260712/style.png"
  ],
  "timeout": 300,
  "styleStrength": 0.75
}
```

## 六、回调消息示例

imggen 写入 `ucub_imggen_callback`：

```json
{
  "innerTaskId": "inner_20260712_00001",
  "status": "success",
  "costTime": 24.3,
  "imageUrlList": ["http://object.intuly.com/ai/img/build/20260712/out.png"],
  "errorMsg": ""
}
```

## 七、rocketmq_consumer.py

```python
import json
import logging

from rocketmq.client import PushConsumer

from app.config import settings, mq_enabled
from app.services.callback_service import handle_imggen_callback

logger = logging.getLogger(__name__)


def start_callback_consumer() -> None:
    if not mq_enabled():
        return
    consumer = PushConsumer(f"ucub-mqdraw-callback-{settings.ROCKETMQ_TOPIC_CALLBACK}")
    consumer.set_name_server_address(settings.ROCKETMQ_NAME_SERVER)
    consumer.set_session_credentials(
        settings.ROCKETMQ_ACCESS_KEY,
        settings.ROCKETMQ_SECRET_KEY,
        "",
    )
    consumer.subscribe(settings.ROCKETMQ_TOPIC_CALLBACK, _on_message)
    consumer.start()
    logger.info("Callback Consumer 已启动")


def _on_message(msg):
    try:
        data = json.loads(msg.body.decode("utf-8"))
        handle_imggen_callback(data)
        return 0
    except Exception:
        logger.exception("回调处理失败")
        return 1
```

## 八、callback_service.py

```python
from app.services.websocket_manager import websocket_manager


def normalize_status(raw: str | None) -> str:
    if raw in ("success", "completed"):
        return "completed"
    if raw in ("failed", "error"):
        return "failed"
    return raw or "failed"


def handle_imggen_callback(message: dict) -> None:
    inner_task_id = message.get("innerTaskId") or message.get("taskId")
    if not inner_task_id:
        return

    task = get_by_inner_task_id(inner_task_id)  # 查 DB
    if not task:
        return

    updated = update_result(
        task_id=task.task_id,
        status=normalize_status(message.get("status")),
        progress=100,
        task_callback_params=message,
        error_message=message.get("errorMsg") or "",
        cost_time=message.get("costTime"),
    )
    websocket_manager.broadcast_task_update(updated)
```

## 九、task_service 中的调用

```python
if settings.USE_MOCK:
    start_mock_task(task_id)
else:
    mq_service.send(task_dispatch_params, tool_key=tool.key)

task = update_status(task_id, "queued", 5)
websocket_manager.broadcast_task_update(task)
```

## 十、main.py lifespan

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.USE_MOCK:
        start_callback_consumer()
    yield
    rocketmq_client.shutdown()
```
