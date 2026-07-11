# UcubMQDraw 优卡普 AI 生图异步调度中台项目计划书

## 1. 项目定位

### 1.1 项目名称

**UcubMQDraw 优卡普 AI 生图异步调度中台**

### 1.2 项目性质

UcubMQDraw 不是底层 AI 推理服务，也不在本项目中实现 ComfyUI 推理逻辑。

本项目的定位是：

> 基于 Gradio + FastAPI + RocketMQ 的 AI 生图业务调度中台，负责运营页面、任务提交、任务调度、业务数据管理、任务状态管理、结果回写展示。

底层真实生图能力已经由独立服务 `imggen` 实现。

UcubMQDraw 只负责：

- 给运营人员提供可视化操作页面。
- 接收前端任务请求。
- 保存业务任务数据。
- 生成业务任务 ID 和算力内部 ID。
- 根据算力类型投递 RocketMQ。
- 接收 imggen 回调结果。
- 更新任务状态。
- 通过 WebSocket 或轮询刷新前端任务记录。

### 1.3 与 imggen 的边界

| 系统 | 职责 |
|---|---|
| UcubMQDraw | 业务调度、运营页面、任务管理、用户数据、MQ 调度、状态回写 |
| imggen | ComfyUI 工作流解析、AI 推理、图片上传 OSS、结果回调 MQ |

UcubMQDraw 不做：

- 不实现 ComfyUI 工作流解析。
- 不执行 GPU 推理。
- 不暴露显卡服务公网接口。
- 不把用户、运营、权限、业务标签传给 imggen。
- 不直接存储图片二进制。

imggen 不做：

- 不感知 userId。
- 不感知运营人员信息。
- 不感知素材归属。
- 不处理权限。
- 不处理统计报表。
- 不处理业务任务重跑逻辑。
- 不对外暴露公网 HTTP 生图接口。

---

# 2. 建设背景

当前已有底层算力服务 `imggen`，它基于 ComfyUI 工作流服务化改造，支持读取 ComfyUI 导出的工作流 JSON，并在节点环境中执行图像生成。

imggen 当前拆分为两个版本：

1. **imggen-ComfyUI-API 并发版**
   - 支持多任务并发执行。
   - 适合轻量工作流、批量作图、商品图生成。
   - 消费 RocketMQ 队列：`ucub_imggen_api_task`。

2. **imggen-ComfyUI-GPT 串行版**
   - 依赖 GPU 资源。
   - 单实例同一时间只能执行 1 个任务。
   - 适合复杂图文理解、长提示词优化、复杂工作流。
   - 消费 RocketMQ 队列：`ucub_imggen_gpt_task`。

由于显卡服务不能暴露公网，且两个 imggen 版本的并发能力不同，因此需要建设一个上层业务中台 UcubMQDraw，用于统一管理运营任务、统一分发不同算力队列、统一接收结果回调，并给内部运营人员提供可视化页面。

---

# 3. 项目建设目标

## 3.1 当前阶段目标

当前阶段重点是先完成前端和调度中台的基础结构，不纠结真实后端细节，但代码架构必须清晰，方便后续接入正式 FastAPI、MySQL、OSS、RocketMQ 和 WebSocket。

当前阶段目标包括：

- 完成 Gradio 三栏式运营页面。
- 完成任务参数表单。
- 完成图片上传和中间大图预览。
- 完成任务提交交互。
- 完成右侧任务记录卡片。
- 完成任务状态 mock 刷新。
- 预留 FastAPI 调用接口。
- 预留 WebSocket 状态监听。
- 预留 RocketMQ 调度接入点。
- 预留 OSS 图片上传接入点。
- 预留 MySQL 任务落库接入点。
- 建立清晰、易懂、可扩展的项目目录结构。

## 3.2 正式阶段目标

正式阶段需要实现：

- FastAPI 接收任务。
- MySQL 保存任务、用户、素材、映射数据。
- OSS 保存参考图、生成图、工作流 JSON。
- RocketMQ 根据 `computeType` 分发任务。
- imggen 消费任务并生成结果。
- UcubMQDraw 消费回调队列。
- WebSocket 推送任务状态给 Gradio。
- 支持任务重跑、取消、删除、收藏、下载。
- 支持运营数据统计和看板。

---

# 4. 总体架构设计

## 4.1 系统分层

整体系统分为五层：

```text
可视化运营层
    ↓
UcubMQDraw 业务调度中台层
    ↓
RocketMQ 消息调度层
    ↓
imggen 双版本算力推理层
    ↓
统一存储层
```

## 4.2 架构图

```text
┌──────────────────────────────────────────────┐
│              Gradio 可视化运营页面             │
│  左侧参数配置 | 中间素材预览 | 右侧任务记录       │
└───────────────────────┬──────────────────────┘
                        │
                        │ POST 创建任务 / WebSocket 状态刷新
                        ↓
┌──────────────────────────────────────────────┐
│            UcubMQDraw FastAPI 业务中台          │
│  任务接口 | ID映射 | 用户数据 | 任务状态 | 统计数据 │
└───────────────┬─────────────────────┬────────┘
                │                     │
                │ 写入 MySQL           │ 上传/记录 OSS
                ↓                     ↓
        ┌────────────┐        ┌──────────────┐
        │ MySQL 8.0   │        │ 阿里云 OSS     │
        └────────────┘        └──────────────┘
                │
                │ 生成 innerTaskId，剥离业务字段
                ↓
┌──────────────────────────────────────────────┐
│                 阿里云 RocketMQ               │
│ ucub_imggen_api_task                          │
│ ucub_imggen_gpt_task                          │
│ ucub_imggen_callback                          │
└───────────────┬─────────────────────┬────────┘
                │                     │
                ↓                     ↓
┌──────────────────────┐      ┌──────────────────────┐
│ imggen API 并发版      │      │ imggen GPT 串行版      │
│ ComfyUI 工作流推理     │      │ ComfyUI 工作流推理     │
└───────────────┬──────┘      └───────────────┬──────┘
                │                             │
                └──────────→ OSS 输出图 ←──────┘
                              │
                              ↓
                    MQ callback 回调结果
                              │
                              ↓
                    UcubMQDraw 更新任务状态
                              │
                              ↓
                    WebSocket 推送 Gradio 页面
```

---

# 5. 核心业务流程

## 5.1 运营提交任务流程

```text
1. 运营人员在 Gradio 页面上传底图、风格参考图。
2. 选择生成数量、风格强度、算力类型、ComfyUI 工作流模板。
3. 点击“立即迁移”。
4. 前端校验必填参数。
5. Gradio 调用 FastAPI 创建任务接口。
6. FastAPI 生成业务 taskId。
7. FastAPI 保存用户、任务、参数、素材信息到 MySQL。
8. FastAPI 上传或记录 OSS 图片地址。
9. FastAPI 生成 innerTaskId。
10. FastAPI 写入 task_inner_mapping 映射表。
11. FastAPI 剥离 userId、运营标签等业务字段。
12. FastAPI 组装纯绘图消息。
13. 根据 computeType 投递 RocketMQ。
14. 前端右侧显示任务为“排队中”或“进行中”。
```

## 5.2 imggen 执行流程

```text
1. imggen API 版消费 ucub_imggen_api_task。
2. imggen GPT 版消费 ucub_imggen_gpt_task。
3. imggen 只读取 innerTaskId 和纯绘图参数。
4. imggen 调用已实现的 ComfyUI 工作流服务。
5. 生成图片后上传 OSS。
6. imggen 发送回调消息到 ucub_imggen_callback。
```

## 5.3 UcubMQDraw 回调更新流程

```text
1. UcubMQDraw 消费 ucub_imggen_callback。
2. 根据 innerTaskId 查询 task_inner_mapping。
3. 找回业务 taskId。
4. 更新 MySQL 任务状态。
5. 写入 output image OSS 地址。
6. 写入耗时、失败原因。
7. 通过 WebSocket 推送给前端。
8. Gradio 右侧任务卡片自动刷新。
```

---

# 6. 为什么使用 WebSocket

## 6.1 使用原因

AI 生图任务是异步任务，不适合用同步 HTTP 一直等待结果。

普通 HTTP 流程：

```text
请求 → 后端处理 → 立即返回结果
```

UcubMQDraw 生图流程：

```text
请求 → 创建任务 → MQ 排队 → imggen 消费 → ComfyUI 推理 → OSS 上传 → MQ 回调 → 更新状态
```

这个过程可能持续几秒到几分钟，因此创建任务接口应该快速返回 `taskId`，后续状态变化由 WebSocket 推送给前端。

## 6.2 WebSocket 在系统中的位置

WebSocket 不连接 imggen。

正确链路是：

```text
imggen
    ↓ RocketMQ callback
UcubMQDraw FastAPI
    ↓ WebSocket
Gradio 前端
```

也就是说：

- imggen 不直接通知前端。
- 前端不直接感知 imggen。
- WebSocket 推送的是 UcubMQDraw 整理后的业务任务状态。
- 前端只展示业务 `taskId`，不展示 `innerTaskId`。

## 6.3 WebSocket 与轮询对比

| 方案 | 优点 | 缺点 | 适用阶段 |
|---|---|---|---|
| 轮询 | 简单，容易实现 | 请求浪费，状态延迟 | MVP 早期 |
| SSE | 单向推送简单 | 扩展性弱于 WebSocket | 只做通知 |
| WebSocket | 实时、扩展性好、适合任务流 | 实现稍复杂 | 正式版本 |

当前建议：

```text
前端阶段：
    使用 Gradio Timer + 本地 mock store 实现自动刷新。

正式联调阶段：
    接入 WebSocket。

生产阶段：
    WebSocket 为主，轮询作为降级方案。
```

---

# 7. 页面规划

> **UI 视觉与交互的完整规范已独立成文档，不在本计划书内展开代码与样式细节。**  
> 请参阅：**[docs/ui_design.md](ui_design.md)**

## 7.1 设计定位

Gradio 前端采用 **「AI 创作工具台」** 风格，而非默认后台表单：

- 三栏布局：左配置 · 中预览 · 右任务流
- HTML 工具卡片 + State，避免 `gr.Radio` 原生样式
- 上传区浅蓝虚线轻卡片，数量用 pill 按钮
- 中栏空状态引导，右栏任务流卡片
- 运营向短文案，不出现开发说明

## 7.2 布局概要

```text
┌────────────────────┬────────────────────────┬────────────────────┐
│ 左栏 · 创作配置      │ 中栏 · 素材预览          │ 右栏 · 创作记录      │
│ 28fr (min 360px)   │ 44fr (min 520px)       │ 28fr (min 300px)   │
└────────────────────┴────────────────────────┴────────────────────┘
```

## 7.3 功能分区概要

| 区域 | 核心内容 |
|------|----------|
| 左栏 | 分类 tabs、搜索、工具卡片 2×3、风格迁移表单 |
| 中栏 | 底图预览、空状态、重新上传 / 裁剪 / 立即迁移 |
| 右栏 | 筛选 pills、任务卡片（进行中 / 已完成 / 失败） |

详细组件选型、CSS Token、交互流程、验收清单见 **[ui_design.md](ui_design.md)**。

---

# 8. 项目目录结构

## 8.1 总体目录

```text
UcubMQDraw/
├── app.py
├── start.sh
├── requirements.txt
├── pyproject.toml
├── README.md
├── .env.example
├── ucub_mqdraw/
│   ├── config.py
│   ├── constants.py
│   ├── models.py
│   ├── store.py
│   ├── services/
│   │   ├── api_client.py
│   │   ├── websocket_client.py
│   │   ├── mock_task_runner.py
│   │   └── mq_contract.py
│   ├── ui/
│   │   ├── layout.py
│   │   ├── left_panel.py
│   │   ├── center_panel.py
│   │   ├── right_panel.py
│   │   ├── events.py
│   │   ├── styles.py
│   │   └── tool_grid.py
│   └── utils/
│       ├── id_generator.py
│       └── image.py
└── docs/
    ├── ui_design.md          # UI 设计规范（独立文档）
    ├── api_contract.md
    ├── mq_contract.md
    └── websocket_contract.md
```

## 8.2 目录职责

| 文件 | 职责 |
|---|---|
| `app.py` | 项目启动入口 |
| `requirements.txt` | Python 依赖 |
| `.env.example` | 环境变量示例 |
| `config.py` | 后端地址、WebSocket 地址、mock 开关 |
| `constants.py` | 工具列表、工作流模板、算力类型 |
| `models.py` | 任务模型、状态枚举、表单模型 |
| `store.py` | 本地任务状态存储，前端 mock 阶段使用 |
| `api_client.py` | FastAPI 接口封装 |
| `websocket_client.py` | WebSocket 状态监听 |
| `mock_task_runner.py` | 本地模拟任务进度 |
| `mq_contract.py` | MQ 消息结构说明，不直接发 MQ |
| `layout.py` | Gradio 页面总装配 |
| `left_panel.py` | 左侧参数区 |
| `center_panel.py` | 中间预览区 |
| `right_panel.py` | 右侧任务记录区 |
| `events.py` | 页面事件逻辑 |
| `styles.py` | CSS 样式 |
| `tool_grid.py` | 工具卡片 HTML 与提示文案 |
| `id_generator.py` | taskId、innerTaskId 生成规则 |
| `image.py` | OSS 上传占位 |
| `docs/ui_design.md` | **UI 设计规范（视觉、布局、交互、验收）** |
| `docs/` 其他 | API、MQ、WebSocket 契约 |

---

# 9. Python 依赖

`requirements.txt`：

```txt
gradio>=4.44.0
requests>=2.31.0
websockets>=12.0
python-dotenv>=1.0.1
```

后续如果同仓库加入 FastAPI 后端，可增加：

```txt
fastapi>=0.111.0
uvicorn>=0.30.0
sqlalchemy>=2.0.0
pymysql>=1.1.0
oss2>=2.18.0
apscheduler>=3.10.0
```

---

# 10. 环境变量设计

`.env.example`：

```env
UCUB_MQDRAW_HTTP_BASE=http://127.0.0.1:8000
UCUB_MQDRAW_WS_URL=ws://127.0.0.1:8000/api/v1/images/generations/tasks/ws

# 前端阶段建议开启，后端不可用时模拟任务状态。
UCUB_MQDRAW_USE_MOCK=true

# Gradio 服务配置。
GRADIO_SERVER_NAME=0.0.0.0
GRADIO_SERVER_PORT=7860
```

---

# 11. 核心数据模型设计

## 11.1 任务状态

UcubMQDraw 业务状态建议统一为：

```text
created       已创建
queued        排队中
dispatching   投递中
running       生成中
completed     已完成
failed        失败
cancelled     已取消
retrying      重跑中
```

前端筛选映射：

```text
进行中 = created + queued + dispatching + running + retrying
已完成 = completed
失败 = failed
收藏 = favorite = true
```

## 11.2 前端任务模型

`ucub_mqdraw/models.py`：

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4


class TaskStatus(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    DISPATCHING = "dispatching"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class GenerationTask:
    task_id: str = field(default_factory=lambda: f"ucub_task_{uuid4().hex[:16]}")
    status: TaskStatus = TaskStatus.CREATED
    progress: int = 0
    task_type: str = "风格迁移"
    tool: str = "风格迁移"
    compute_type: str = "comfy_api"
    workflow_template: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    description: str = ""
    favorite: bool = False
    input_preview: str = ""
    output_preview: str = ""
    error_message: str = ""
    cost_time: Optional[float] = None
    request_payload: dict = field(default_factory=dict)


@dataclass
class StyleTransferForm:
    base_image_path: Optional[str]
    style_image_path: Optional[str]
    generation_count: str
    style_strength: float
    description: str
    compute_type: str
    workflow_template: str
    tool_name: str
```

---

# 12. 配置和常量设计

## 12.1 配置文件

`ucub_mqdraw/config.py`：

```python
import os

from dotenv import load_dotenv

load_dotenv()

BACKEND_HTTP_BASE = os.getenv("UCUB_MQDRAW_HTTP_BASE", "http://127.0.0.1:8000")
BACKEND_WS_URL = os.getenv(
    "UCUB_MQDRAW_WS_URL",
    "ws://127.0.0.1:8000/api/v1/images/generations/tasks/ws",
)

TASK_CREATE_API = f"{BACKEND_HTTP_BASE}/api/v1/images/generations/tasks"

USE_MOCK = os.getenv("UCUB_MQDRAW_USE_MOCK", "true").lower() == "true"

GRADIO_SERVER_NAME = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0")
GRADIO_SERVER_PORT = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
```

## 12.2 常量文件

`ucub_mqdraw/constants.py`：

```python
TOP_TABS = ["全部", "图像生成", "图像编辑", "图转视频", "实用工具"]

TOOL_CHOICES = [
    "风格迁移",
    "图转视频",
    "局部重绘",
    "材质替换",
    "智能扩图",
    "线稿生成",
]

COMPUTE_TYPES = {
    "comfy_api并发版": "comfy_api",
    "comfy_gpt串行版": "comfy_gpt",
}

DEFAULT_WORKFLOWS = [
    "style_transfer_v1.json",
    "style_transfer_high_quality.json",
    "anime_style_transfer.json",
    "product_photo_style_transfer.json",
    "lineart_generation_v1.json",
]

TASK_FILTERS = ["全部", "进行中", "已完成", "收藏"]
```

---

# 13. 本地任务 Store 设计

当前前端阶段用内存模拟任务状态。

正式环境中：

- 任务主数据来自 MySQL。
- 前端通过 FastAPI 查询任务列表。
- WebSocket 只负责推送状态变更事件。
- `store.py` 可以保留为 Gradio 前端页面的临时状态缓存。

`ucub_mqdraw/store.py`：

```python
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
```

---

# 14. API Client 设计

## 14.1 说明

前端只调用 UcubMQDraw FastAPI，不直接调用 imggen，也不直接操作 RocketMQ。

`api_client.py` 负责封装：

```http
POST /api/v1/images/generations/tasks
GET /api/v1/images/generations/tasks/{taskId}
POST /api/v1/images/generations/tasks/{taskId}/retry
```

## 14.2 代码示例

`ucub_mqdraw/services/api_client.py`：

```python
import requests

from ucub_mqdraw.config import TASK_CREATE_API
from ucub_mqdraw.constants import COMPUTE_TYPES
from ucub_mqdraw.models import StyleTransferForm
from ucub_mqdraw.utils.image import upload_to_oss_placeholder


class GenerationApiClient:
    """
    UcubMQDraw FastAPI 接口客户端。

    注意：
    这里不直接调用 imggen。
    这里也不直接投递 RocketMQ。
    Gradio 前端只提交业务任务给 UcubMQDraw 后端。
    """

    def build_style_transfer_payload(self, task_id: str, form: StyleTransferForm) -> dict:
        compute_type = COMPUTE_TYPES.get(form.compute_type, form.compute_type)

        return {
            "taskId": task_id,
            "userId": "op_demo_user",
            "modelName": "SDXL/Flux",
            "prompt": form.description or "风格迁移",
            "negativePrompt": "",
            "width": 1024,
            "height": 1024,
            "batchSize": int(form.generation_count.replace("张", "")),
            "refImageList": [
                upload_to_oss_placeholder(form.base_image_path),
                upload_to_oss_placeholder(form.style_image_path),
            ],
            "timeout": 300,
            "computeType": compute_type,
            "workflowTemplate": form.workflow_template,
            "workflowJson": "",
            "extra": {
                "tool": form.tool_name,
                "styleStrength": float(form.style_strength),
                "bizScene": "style_transfer",
            },
        }

    def submit_style_transfer(self, task_id: str, form: StyleTransferForm) -> dict:
        payload = self.build_style_transfer_payload(task_id, form)

        response = requests.post(
            TASK_CREATE_API,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()

        return response.json()

    def get_task(self, task_id: str) -> dict:
        response = requests.get(
            f"{TASK_CREATE_API}/{task_id}",
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def retry_task(self, task_id: str) -> dict:
        response = requests.post(
            f"{TASK_CREATE_API}/{task_id}/retry",
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
```

---

# 15. MQ 消息契约设计

这个前端项目不直接实现 MQ 生产消费，但要把 MQ 契约写清楚，方便后端对接。

`ucub_mqdraw/services/mq_contract.py`：

```python
"""
RocketMQ 消息契约说明。

注意：
当前 Gradio 前端不直接操作 MQ。
正式 MQ 生产和消费逻辑应放在 UcubMQDraw FastAPI 后端。

Topic:
- ucub_imggen_api_task: imggen-ComfyUI-API 并发版任务队列
- ucub_imggen_gpt_task: imggen-ComfyUI-GPT 串行版任务队列
- ucub_imggen_callback: imggen 统一回调队列
"""

IMGGEN_API_TASK_TOPIC = "ucub_imggen_api_task"
IMGGEN_GPT_TASK_TOPIC = "ucub_imggen_gpt_task"
IMGGEN_CALLBACK_TOPIC = "ucub_imggen_callback"


def build_imggen_task_message(
    inner_task_id: str,
    model_name: str,
    prompt: str,
    negative_prompt: str,
    width: int,
    height: int,
    batch_size: int,
    ref_image_list: list[str],
    timeout: int,
    workflow_json: str,
) -> dict:
    """
    后端投递给 imggen 的纯算力消息。

    这里不能包含：
    - userId
    - 操作人
    - 运营标签
    - 素材归属
    - 权限字段
    """
    return {
        "innerTaskId": inner_task_id,
        "modelName": model_name,
        "prompt": prompt,
        "negativePrompt": negative_prompt,
        "width": width,
        "height": height,
        "batchSize": batch_size,
        "refImageList": ref_image_list,
        "timeout": timeout,
        "workflowJson": workflow_json,
    }
```

---

# 16. WebSocket Client 设计

## 16.1 推送消息格式

后端 WebSocket 推给前端的消息应该是业务状态：

```json
{
  "taskId": "ucub_task_20260711_00001",
  "status": "running",
  "progress": 60,
  "imageUrlList": [],
  "errorMsg": "",
  "costTime": null
}
```

完成：

```json
{
  "taskId": "ucub_task_20260711_00001",
  "status": "completed",
  "progress": 100,
  "imageUrlList": ["https://oss.xxx/output.png"],
  "errorMsg": "",
  "costTime": 18.6
}
```

失败：

```json
{
  "taskId": "ucub_task_20260711_00001",
  "status": "failed",
  "progress": 100,
  "imageUrlList": [],
  "errorMsg": "ComfyUI 工作流执行失败",
  "costTime": 12.4
}
```

## 16.2 代码示例

`ucub_mqdraw/services/websocket_client.py`：

```python
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
```

---

# 17. Mock Task Runner 设计

当前阶段后端可以不用完整实现，前端要能独立演示，所以需要 mock 状态流。

`ucub_mqdraw/services/mock_task_runner.py`：

```python
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
```

---

# 18. UI 与前端实现说明

Gradio 前端的 **视觉规范、布局比例、组件选型、交互流程、验收清单** 已独立整理，不在本计划书中重复贴代码。

**请阅读：[docs/ui_design.md](ui_design.md)**

## 18.1 设计原则摘要

- 风格定位：**AI 创作工具台**，避免 Gradio 默认后台表单感。
- 工具选择：HTML 卡片 2×3 + `gr.State` + 透明点击层，**不用** `gr.Radio`。
- 数量选择：pill 按钮 + `gr.State`，**不用** `gr.Radio`。
- 上传区：浅蓝虚线轻卡片，`label=None` + HTML 字段标题。
- 中栏：空状态引导 + 底图预览。
- 右栏：任务流 HTML 卡片 + Timer 刷新。
- 文案：运营向短句，禁止开发说明用语。

## 18.2 实现代码索引

| 职责 | 文件 |
|------|------|
| 三栏装配与事件绑定 | `ucub_mqdraw/ui/layout.py` |
| 左栏（工具、表单） | `ucub_mqdraw/ui/left_panel.py` |
| 中栏（预览、空状态） | `ucub_mqdraw/ui/center_panel.py` |
| 右栏（任务卡片 HTML） | `ucub_mqdraw/ui/right_panel.py` |
| 交互逻辑 | `ucub_mqdraw/ui/events.py` |
| 全局 CSS | `ucub_mqdraw/ui/styles.py` |
| 工具卡片 HTML | `ucub_mqdraw/ui/tool_grid.py` |

## 18.3 与计划书其他章节关系

- 第 7 章：页面规划概要 → 详见 `ui_design.md`
- 第 19、20 章（原页面事件 / 布局代码）已合并入 UI 设计文档与上述源码，**不再在本计划书维护代码副本**。


# 21. 启动入口

`app.py`：

```python
import gradio as gr

from ucub_mqdraw.config import GRADIO_SERVER_NAME, GRADIO_SERVER_PORT, USE_MOCK
from ucub_mqdraw.services.websocket_client import start_websocket_listener
from ucub_mqdraw.ui.layout import build_app
from ucub_mqdraw.ui.styles import CUSTOM_CSS


def main():
    if not USE_MOCK:
        start_websocket_listener()

    demo = build_app()

    demo.queue(default_concurrency_limit=20).launch(
        server_name=GRADIO_SERVER_NAME,
        server_port=GRADIO_SERVER_PORT,
        footer_links=[],
        css=CUSTOM_CSS,
        theme=gr.themes.Soft(),
    )


if __name__ == "__main__":
    main()
```

---

# 22. OSS 占位工具

`ucub_mqdraw/utils/image.py`：

```python
import os
from typing import Optional


def upload_to_oss_placeholder(local_path: Optional[str]) -> Optional[str]:
    """
    OSS 接入点。

    当前阶段只返回模拟 OSS 路径。
    正式阶段这里应上传本地临时文件到 OSS，并返回可访问 URL。

    注意：
    MQ 消息中不传图片二进制，只传 OSS 地址。
    """
    if not local_path:
        return None

    filename = os.path.basename(local_path)
    return f"oss://ucub-img/ref/{filename}"
```

---

# 23. ID 生成工具

`ucub_mqdraw/utils/id_generator.py`：

```python
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
```

说明：

- `taskId` 是业务任务 ID，可以暴露给前端和运营人员。
- `innerTaskId` 是算力内部 ID，只用于 UcubMQDraw 和 imggen 之间通信。
- 前端不展示 `innerTaskId`。
- imggen 不接收 `taskId` 对应的用户业务信息。

---

# 24. FastAPI 后端接口契约

虽然当前阶段主要做 Gradio 前端，但后端接口契约需要提前定义。

## 24.1 创建任务

```http
POST /api/v1/images/generations/tasks
```

请求体：

```json
{
  "taskId": "ucub_task_20260711_00001",
  "userId": "op021",
  "modelName": "SDXL/Flux",
  "prompt": "高清商品图，8K，写实",
  "negativePrompt": "模糊，水印，低画质",
  "width": 1024,
  "height": 1024,
  "batchSize": 2,
  "refImageList": [
    "oss://ucub-img/ref/base.jpg",
    "oss://ucub-img/ref/style.jpg"
  ],
  "timeout": 300,
  "computeType": "comfy_api",
  "workflowTemplate": "style_transfer_v1.json",
  "workflowJson": "",
  "extra": {
    "tool": "风格迁移",
    "styleStrength": 0.75,
    "bizScene": "style_transfer"
  }
}
```

响应体：

```json
{
  "taskId": "ucub_task_20260711_00001",
  "status": "queued",
  "message": "任务已创建并进入队列"
}
```

## 24.2 查询任务

```http
GET /api/v1/images/generations/tasks/{taskId}
```

响应体：

```json
{
  "taskId": "ucub_task_20260711_00001",
  "status": "running",
  "progress": 60,
  "imageUrlList": [],
  "errorMsg": "",
  "costTime": null
}
```

## 24.3 重跑任务

```http
POST /api/v1/images/generations/tasks/{taskId}/retry
```

响应体：

```json
{
  "taskId": "ucub_task_20260711_00002",
  "originTaskId": "ucub_task_20260711_00001",
  "status": "queued",
  "message": "重跑任务已创建"
}
```

---

# 25. 数据库表结构建议

## 25.1 用户表 `ucub_user`

```sql
CREATE TABLE ucub_user (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(64) NOT NULL UNIQUE,
    username VARCHAR(128) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'operator',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
```

## 25.2 任务主表 `image_generation_task`

```sql
CREATE TABLE image_generation_task (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_id VARCHAR(64) NOT NULL UNIQUE,
    user_id VARCHAR(64) NOT NULL,
    task_type VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    compute_type VARCHAR(32) NOT NULL,
    model_name VARCHAR(128),
    prompt TEXT,
    negative_prompt TEXT,
    width INT,
    height INT,
    batch_size INT,
    workflow_template VARCHAR(255),
    ref_image_list JSON,
    output_image_list JSON,
    error_msg TEXT,
    cost_time DECIMAL(10, 2),
    retry_from_task_id VARCHAR(64),
    favorite TINYINT DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
```

## 25.3 ID 映射表 `task_inner_mapping`

```sql
CREATE TABLE task_inner_mapping (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_id VARCHAR(64) NOT NULL,
    inner_task_id VARCHAR(64) NOT NULL UNIQUE,
    compute_type VARCHAR(32) NOT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_task_id (task_id),
    INDEX idx_inner_task_id (inner_task_id)
);
```

## 25.4 工作流模板表 `workflow_template`

```sql
CREATE TABLE workflow_template (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    template_code VARCHAR(128) NOT NULL UNIQUE,
    template_name VARCHAR(128) NOT NULL,
    compute_type VARCHAR(32),
    workflow_json_oss_url VARCHAR(512),
    enabled TINYINT DEFAULT 1,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
```

## 25.5 素材资源表 `material_asset`

```sql
CREATE TABLE material_asset (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    asset_id VARCHAR(64) NOT NULL UNIQUE,
    user_id VARCHAR(64) NOT NULL,
    asset_type VARCHAR(32) NOT NULL,
    oss_url VARCHAR(512) NOT NULL,
    tags JSON,
    created_at DATETIME NOT NULL
);
```

---

# 26. RocketMQ Topic 规划

| Topic | 用途 | 消费方 |
|---|---|---|
| `ucub_imggen_api_task` | API 并发版任务队列 | imggen-ComfyUI-API |
| `ucub_imggen_gpt_task` | GPT 串行版任务队列 | imggen-ComfyUI-GPT |
| `ucub_imggen_callback` | 统一结果回调队列 | UcubMQDraw |

## 26.1 下发给 imggen 的消息

```json
{
  "innerTaskId": "inner_20260711_00001",
  "modelName": "SDXL/Flux",
  "prompt": "高清商品图，8K，写实",
  "negativePrompt": "模糊，水印，低画质",
  "width": 1024,
  "height": 1024,
  "batchSize": 2,
  "refImageList": ["oss://ucub-img/ref/xxx.jpg"],
  "timeout": 300,
  "workflowJson": "ComfyUI原始工作流JSON"
}
```

## 26.2 imggen 回调消息

```json
{
  "innerTaskId": "inner_20260711_00001",
  "status": "success",
  "costTime": 18.6,
  "imageUrlList": ["oss://ucub-img/output/xxx.png"],
  "errorMsg": ""
}
```

---

# 27. 开发阶段计划

## 阶段一：项目骨架搭建

预计时间：0.5 天。

交付内容：

- 初始化目录结构。
- 编写 `requirements.txt`。
- 编写 `app.py`。
- 编写配置文件。
- 编写基础模型。
- 编写本地 store。

验收标准：

- 项目可以启动。
- 页面可以打开。
- 目录结构清晰。
- 后续模块有明确位置。

---

## 阶段二：Gradio 三栏页面实现

预计时间：1 天。

交付内容：

- 左 / 中 / 右三栏布局（CSS Grid，见 `ui_design.md`）
- AI 创作工具台视觉风格（非默认 Gradio 表单）
- 深蓝主按钮、浅白卡片、轻阴影

验收标准：

- 符合 [ui_design.md](ui_design.md) 布局与视觉验收项
- 桌面端（≥1280px）显示稳定，左栏不挤压

---

## 阶段三：风格迁移表单实现

预计时间：1 天。

交付内容：

- HTML 工具卡片 2×3（图标 + 名称）
- 浅蓝虚线上传区、pill 数量选择
- 风格强度滑块、算力 / 工作流、重置
- 运营向短提示文案

验收标准：

- 风格迁移默认选中，工具可切换
- 无 `gr.Radio` 原生「单选框」展示
- 非开放工具提示「能力即将开放」

---

## 阶段四：任务提交和 mock 状态刷新

预计时间：1 天。

交付内容：

- 表单校验。
- 提交按钮防重复点击。
- 创建本地任务。
- mock 任务进度。
- 右侧卡片自动刷新。
- 已完成、进行中、失败卡片样式。

验收标准：

- 未上传图片不能提交。
- 超过 300 字不能提交。
- 提交后右侧新增任务。
- 任务状态自动从排队到完成。
- 完成后展示输出图。

---

## 阶段五：服务层封装

预计时间：0.5 天。

交付内容：

- FastAPI client。
- WebSocket client。
- MQ contract。
- OSS placeholder。
- ID generator。

验收标准：

- UI 不直接写 HTTP 请求。
- WebSocket 逻辑与 UI 解耦。
- MQ 消息结构说明清楚。
- OSS 接入点清楚。

---

## 阶段六：联调准备

预计时间：0.5 天。

交付内容：

- README
- UI 设计规范（`docs/ui_design.md`）
- API / WebSocket / MQ 文档
- 数据库表结构建议

验收标准：

- 后端可以按文档实现接口。
- imggen 可以按 MQ 契约消费消息。
- 前端可以切换 mock 和真实后端。

---

# 28. 总体工期预估

| 阶段 | 内容 | 时间 |
|---|---:|---:|
| 阶段一 | 项目骨架搭建 | 0.5 天 |
| 阶段二 | 三栏页面实现 | 1 天 |
| 阶段三 | 表单实现 | 1 天 |
| 阶段四 | mock 状态和任务记录 | 1 天 |
| 阶段五 | 服务层封装 | 0.5 天 |
| 阶段六 | 文档和联调准备 | 0.5 天 |

预计总工期：

```text
4.5 天左右
```

如果只做可演示 MVP：

```text
2 - 3 天
```

---

# 29. 验收标准

## 29.1 前端页面验收

以 **[docs/ui_design.md](ui_design.md) 第 9 节验收清单** 为准，摘要：

- 三栏 Grid 布局，左栏不挤压
- HTML 工具卡片，无 Gradio Radio 原生样式
- 上传区浅蓝虚线，中栏有空状态引导
- 右栏任务流 pills + 卡片
- 主按钮深蓝，白卡轻阴影
- 文案面向运营，无开发说明用语

## 29.2 交互验收

- 必填图片未上传时弹窗拦截。
- 文本超过 300 字时拦截。
- 提交时按钮置灰。
- 提交后右侧新增任务。
- 任务状态自动刷新。
- 已完成任务显示绿色。
- 进行中任务显示蓝色进度条。
- 失败任务显示红色错误信息。

## 29.3 架构验收

- UI 层、事件层、服务层、状态层分离。
- 前端不直接操作 RocketMQ。
- 前端不直接连接 imggen。
- ComfyUI 不在本项目实现。
- `taskId` 和 `innerTaskId` 边界清楚。
- 后端对接点注释清楚。

---

# 30. 最终结论

UcubMQDraw 的核心不是“做一个生图模型服务”，而是：

```text
做一个可视化、可调度、可管理、可追踪、可统计的 AI 生图业务中台。
```

它上接运营人员，下接 imggen 算力服务，中间通过 FastAPI、MySQL、OSS、RocketMQ 和 WebSocket 完成异步调度闭环。

当前阶段建议实施策略：

```text
前端 UI 先完整
任务状态先 mock
接口层先封装
WebSocket 先预留
RocketMQ 契约先定义
MySQL 和 OSS 接入点先标注
ComfyUI 推理永远由 imggen 独立负责
```

这样可以保证：

- 前端能先独立演示。
- 后端可以按契约逐步接入。
- imggen 不被业务逻辑污染。
- 业务数据和算力服务保持安全隔离。
- 项目后续扩展不会推倒重来。