# UcubMQDraw Gradio 前端

优卡普 AI 生图异步调度中台 — Gradio 可视化前端，采用「UI + 状态管理 + API 服务层 + WebSocket 服务层」分层结构。

## 目录结构

```text
├── app.py
├── start.sh
├── requirements.txt
├── pyproject.toml
├── .env.example
├── docs/
│   ├── api_contract.md
│   ├── mq_contract.md
│   └── websocket_contract.md
└── ucub_mqdraw/
    ├── config.py
    ├── constants.py
    ├── models.py
    ├── store.py
    ├── services/
    │   ├── api_client.py
    │   ├── websocket_client.py
    │   ├── mock_task_runner.py
    │   └── mq_contract.py
    ├── ui/
    └── utils/
        ├── id_generator.py
        └── image.py
```

## 快速启动

```bash
./start.sh
```

或手动：

```bash
uv venv && uv sync
uv run python app.py
```

访问 `http://127.0.0.1:7860`

## 环境变量

复制 `.env.example` 为 `.env` 后按需修改：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `UCUB_MQDRAW_USE_MOCK` | `true` | 本地模拟任务进度 |
| `UCUB_MQDRAW_HTTP_BASE` | `http://127.0.0.1:8000` | FastAPI 地址 |
| `UCUB_MQDRAW_WS_URL` | `ws://.../tasks/ws` | WebSocket 地址 |
| `GRADIO_SERVER_PORT` | `7860` | Gradio 端口 |

接入真实后端：

```bash
UCUB_MQDRAW_USE_MOCK=false ./start.sh
```

## 架构边界

- 前端只调 UcubMQDraw FastAPI，不直连 imggen / RocketMQ
- `taskId` 为业务 ID，`innerTaskId` 仅后端与 imggen 通信
- ComfyUI 推理由独立服务 imggen 负责

## 文档

- [UI 设计规范](docs/ui_design.md)
- [API 契约](docs/api_contract.md)
- [MQ 契约](docs/mq_contract.md)
- [WebSocket 契约](docs/websocket_contract.md)
