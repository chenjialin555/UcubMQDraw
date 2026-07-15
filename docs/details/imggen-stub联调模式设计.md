# imggen-stub 联调模式设计

> 环境变量与基础设施 → [部署与环境变量.md](./部署与环境变量.md)  
> 可复制代码 → [examples/imggen-stub示例.md](../examples/imggen-stub示例.md)

## Mock / Stub 统一原则

**UcubMQDraw 不在业务侧使用 `USE_MOCK` 伪造 imggen 进度。**

本地开发或 imggen 未就绪时，使用独立的 **imggen-stub** 最小服务模拟 imggen。  
imggen-stub 仍然通过 RocketMQ 消费任务和投递回调，因此 UcubMQDraw 的主链路与生产一致：

```text
写库 → MQ 投递 → imggen / imggen-stub 消费 → 回调 MQ → 更新 DB → WS 推送
```

> **不要 Mock UcubMQDraw 的业务链路；要 Stub 外部 imggen 服务。**

---

## 一、统一链路

```text
前端提交任务
  ↓ HTTP
UcubMQDraw FastAPI
  ↓ 写 PostgreSQL task
  ↓ 投递 ROCKETMQ_TOPIC_TASK
RocketMQ task topic
  ↓
imggen-stub（或真实 imggen）
  ↓ sleep 几秒
  ↓ 可选投递 running/progress 回调
  ↓ 投递 success / failed callback
RocketMQ callback topic
  ↓
UcubMQDraw Callback Consumer
  ↓ 根据 innerTaskId 查任务
  ↓ 更新 DB
  ↓ WebSocket send_to_user
前端右栏更新
```

UcubMQDraw **删除**：`USE_MOCK`、`mock_task_runner`、`task_service` 里的 `if USE_MOCK` 分支。

---

## 二、环境变量

### UcubMQDraw 后端（无 USE_MOCK）

```env
ROCKETMQ_ENABLED=true
ROCKETMQ_NAME_SERVER=
ROCKETMQ_PRODUCER_GROUP=ucub-mqdraw-producer
ROCKETMQ_CONSUMER_GROUP=ucub-mqdraw-callback-consumer
ROCKETMQ_ACCESS_KEY=
ROCKETMQ_SECRET_KEY=
ROCKETMQ_TOPIC_TASK=ucub_imggen_api_task
ROCKETMQ_TOPIC_CALLBACK=ucub_imggen_callback
```

`mq_enabled()` 只判断 RocketMQ 配置是否完整，**不再看 `USE_MOCK`**。

### imggen-stub

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

---

## 三、imggen-stub 最小职责

```text
1. 消费 ROCKETMQ_TOPIC_TASK
2. 解析 innerTaskId
3. sleep 几秒
4. 投递 ROCKETMQ_TOPIC_CALLBACK
```

可选增强：

```text
- IMGGEN_STUB_RESULT=success / failed
- 固定输出图 URL
- 中间 running/progress callback（契约支持时再开）
- 按 tool tag 区分延迟或失败率
```

第一版建议**只回终态**，避免 `mq_contract.md` 未定义的进度字段扩散。

---

## 四、目录建议

独立顶层目录（模拟外部算力，不属于 UcubMQDraw 业务）：

```text
imggen-stub/
├── README.md
├── pyproject.toml
├── .env.example
└── app/
    ├── main.py
    ├── config.py
    ├── rocketmq_client.py
    └── stub_worker.py
```

---

## 五、callback 契约

### 终态成功

```json
{
  "innerTaskId": "inner_20260712_00001",
  "status": "success",
  "costTime": 3.2,
  "imageUrlList": [
    "http://object.intuly.com/ai/img/build/mock-output.png"
  ],
  "errorMsg": ""
}
```

### 终态失败

```json
{
  "innerTaskId": "inner_20260712_00001",
  "status": "failed",
  "costTime": 3.2,
  "imageUrlList": [],
  "errorMsg": "imggen-stub simulated failure"
}
```

### 进度（可选，契约支持再开）

```json
{
  "innerTaskId": "inner_20260712_00001",
  "status": "running",
  "progress": 40,
  "message": "imggen-stub running"
}
```

---

## 六、UcubMQDraw 侧要点

### create_task：始终走 MQ

```python
# 禁止：if USE_MOCK: start_mock_task(...)
mq_service.send(dispatch, tool_key=tool.key)
```

### lifespan：按 MQ 配置启 Consumer

```python
if mq_enabled():
    start_callback_consumer()
```

### callback_service

- `success` / `succeeded` / `completed` → `mark_succeeded` → `task.succeeded`
- `failed` / `error` → `mark_failed` → `task.failed`
- 可选：`running` + `progress` → `update_status` → `task.updated`

---

## 七、本地启动顺序

```bash
# 1. PostgreSQL + Redis
docker compose up -d

# 2. UcubMQDraw 后端（配置好 RocketMQ）
cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 3. imggen-stub
cd imggen-stub && uv run python -m app.main

# 4. 前端
cd frontend && npm run dev
```

联调检查：

```text
□ task_dispatch_params 写库正确
□ 投递到 ROCKETMQ_TOPIC_TASK
□ imggen-stub 能解析 innerTaskId
□ callback 更新 DB
□ WS 推送 task.succeeded / task.failed
```

切换到真实 imggen：停掉 stub，同一 Topic 由真实服务消费；**UcubMQDraw 业务代码不变**。

---

## 八、已废弃口径

| 废弃 | 现行 |
|------|------|
| `USE_MOCK=true` | 删除 |
| 业务侧 `start_mock_task` | 删除 |
| 跳过 RocketMQ | 本地也必须配置 MQ |
| 后端线程伪造进度 | imggen-stub 经 callback 驱动状态 |

历史文档中的 Mock 描述见 [归档与现行规范差异.md](../archive/归档与现行规范差异.md)。
