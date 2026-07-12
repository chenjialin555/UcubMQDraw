# RocketMQ 对接设计

> imggen 消息体字段另见 [mq_contract.md](../mq_contract.md)。

## 一、整体链路

```text
task_service.create_task
  ↓
tool.build_task_dispatch_params()
  ↓
mq_service.send(task_dispatch_params, tool_key)
  ↓
rocketmq_client.send_message
  ↓
imggen 消费执行

--- 回调 ---

imggen 完成
  ↓
ucub_imggen_callback Topic
  ↓
callback_consumer
  ↓
handle_imggen_callback
  ↓
更新 DB + WebSocket 推送
```

`USE_MOCK=true` 时跳过 Producer / Consumer。

## 二、Topic 规划

| 环境变量 | 默认值 | 用途 |
|----------|--------|------|
| `ROCKETMQ_TOPIC_TASK` | `ucub_imggen_api_task` | 下发任务 |
| `ROCKETMQ_TOPIC_CALLBACK` | `ucub_imggen_callback` | imggen 回调 |

第一版所有工具走同一 Task Topic；后续可按 `tool_key` 扩展路由。

## 三、task_id 与 innerTaskId

| 字段 | 存哪里 | 用途 |
|------|--------|------|
| `task_id` | 仅 DB | 前端展示的业务任务 ID |
| `inner_task_id` | DB + MQ | imggen 执行、回调映射 |

**MQ 消息体只有 `innerTaskId`，没有 `workflow`、`bizTaskId`、`toolKey`。** 业务归属靠 DB 映射，imggen 不解析。

下发 JSON 示例（风格迁移，见 [mq_contract.md](../mq_contract.md)）：

```json
{
  "innerTaskId": "inner_20260712_00001",
  "modelName": "SDXL/Flux",
  "prompt": "赛博朋克风格",
  "width": 1024,
  "height": 1024,
  "batchSize": 1,
  "refImageList": ["https://...", "https://..."],
  "timeout": 300,
  "styleStrength": 0.75
}
```

回调 JSON 用 `innerTaskId` 查 DB 中的 `inner_task_id` 列。

## 四、mq_service

```python
class MQService:
    def send(self, payload: dict, tool_key: str) -> None:
        topic = settings.ROCKETMQ_TOPIC_TASK
        body = json.dumps(payload, ensure_ascii=False)
        keys = str(payload.get("innerTaskId") or "")
        rocketmq_client.send_message(topic=topic, body=body, tags=tool_key, keys=keys)
```

## 五、Producer 要点

```text
1. 依赖 rocketmq-client-python
2. 单例 Producer，ACL 鉴权
3. send_sync，status==0 为成功
4. 失败指数退避重试（ROCKETMQ_RETRY_TIMES）
5. 应用关闭时 producer.shutdown()
```

## 六、Callback Consumer

`main.py` lifespan 启动：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    start_callback_consumer()  # 非 Mock 且 MQ 已配置
    yield
    rocketmq_client.shutdown()
```

Consumer 收到消息后调用 `handle_imggen_callback(data)`。

## 七、回调处理

```python
def handle_imggen_callback(message: dict) -> None:
    inner_task_id = message.get("innerTaskId") or message.get("taskId")
    task = get_by_inner_task_id(inner_task_id)
    if not task:
        return

    updated = update_result(
        task_id=task.task_id,
        status=normalize_status(message.get("status")),
        task_callback_params=message,
        error_message=message.get("errorMsg") or "",
        cost_time=message.get("costTime"),
    )
    websocket_manager.broadcast_task_update(updated)
```

回调格式见 [API接口.md](../API接口.md#九imggen-回调后端内部前端不调用)。

## 八、失败重试

- **发送侧**：Producer 指数退避重试
- **消费侧**：处理异常返回 `RECONSUME_LATER`
- **业务侧**：任务 `failed` 后 MVP 不提供重跑，第二版基于 `task_submit_params` 建新任务

## 九、环境变量

```env
ROCKETMQ_NAME_SERVER=10.1.10.5:9876
ROCKETMQ_PRODUCER_GROUP=ucub-mqdraw-producer
ROCKETMQ_ACCESS_KEY=
ROCKETMQ_SECRET_KEY=
ROCKETMQ_TOPIC_TASK=ucub_imggen_api_task
ROCKETMQ_TOPIC_CALLBACK=ucub_imggen_callback
ROCKETMQ_RETRY_TIMES=3
```

**完整可复制代码** → [examples/RocketMQ对接示例.md](../examples/RocketMQ对接示例.md)
