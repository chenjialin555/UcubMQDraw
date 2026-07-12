# UcubMQDraw 简化版开发规范

> 用 Vue3 + FastAPI 替换 Gradio。本文档是**总规范**，只讲原则和边界；细节见专题文档。

**文档入口** → [README.md](./README.md)

## 日常开发看这四份

| 文档 | 用途 |
|------|------|
| **本文档** | 总原则、MVP、目录、开发规则 |
| [开发入门.md](./开发入门.md) | 启动、目录、主链路 |
| [新增工具开发指南.md](./新增工具开发指南.md) | **最常看**：新增工具改哪些文件 |
| [API接口.md](./API接口.md) | HTTP / WS 契约（字段唯一权威） |

---

## 一、开发人员只需记住 4 个概念

```text
1. 工具 tool      — 一种生图能力（风格迁移、局部重绘…）
2. 表单 form      — 用户填的参数
3. 任务 task      — 一次提交对应数据库一行
4. 状态 update    — WebSocket 推送进度，右栏自动刷新
```

代码里用 `tools/` 目录，不要记 FeatureDefinition、Handler Registry 等名词。

---

## 二、第一版 MVP

```text
✅ 上传图片、创建任务、任务列表、WebSocket 更新
✅ 风格迁移、局部重绘
✅ Mock 模式、SQLite 持久化
```

## 三、第二版再做

```text
❌ 收藏 / 重跑 / 取消
❌ 多用户 / 权限 / 文生图 UI
❌ PostgreSQL 迁移、复杂 MaskEditor
```

工具数量 **≤ 3** 时，HomePage 可用 `v-if` 切换表单。示例见 [examples/HomePage完整示例.md](./examples/HomePage完整示例.md)。

---

## 四、整体架构

```text
用户 → Vue3（tools/ + taskStore）
         ↓ HTTP              ↓ WebSocket
       FastAPI → SQLite / OSS / RocketMQ → imggen
```

**边界：**

- 前端只传 `toolKey` + `params`
- 后端 `tools/xxx.py` 负责校验、组装下发 JSON

---

## 五、最小目录结构

### 前端

```text
frontend/src/
├── api/          task.ts, upload.ts
├── tools/        每个工具一个目录：Form + Preview(可选) + tool.ts
├── components/   ImageUploader, MaskEditor, TaskList, TaskCard
├── stores/       taskStore.ts
├── pages/        HomePage.vue
└── utils/        ws.ts
```

### 后端

```text
backend/app/
├── db.py         engine + Session（第一版合并）
├── api/          task_api, upload_api, websocket_api
├── tools/        每个工具一个 .py + registry.py
├── services/     task_service, upload_service, mq_service, mock_task_runner, websocket_manager
└── models/       task_model.py
```

---

## 六、工具模块模式

### 前端：一个工具 = 一个目录

| 文件 | 职责 |
|------|------|
| `XxxForm.vue` | 左栏表单 |
| `XxxPreview.vue` | 中栏预览（可选） |
| `tool.ts` | `createForm` / `validate` / `buildRequest` |

`validate` 返回字符串，空 = 通过。完整示例 → [examples/前端工具模块示例.md](./examples/前端工具模块示例.md)

### 后端：一个工具 = 一个处理器

```python
class XxxTool:
    key = "xxx"
    def validate(self, params: dict) -> None: ...
    def build_task_dispatch_params(self, task_id, inner_task_id, params) -> dict: ...
```

完整示例 → [examples/后端工具处理器示例.md](./examples/后端工具处理器示例.md)

---

## 七、任务主链路

```text
上传图 → tool.buildRequest() → POST /tasks
  → validate → 写 DB → Mock/MQ
  → imggen 回调 → WS → taskStore.upsertTask
```

状态与流转细节 → [details/任务状态与任务流转.md](./details/任务状态与任务流转.md)

---

## 八、三列 JSON 参数（原则）

| 阶段 | DB 列 | API 字段 |
|------|-------|----------|
| 用户提交 | `task_submit_params` | `taskSubmitParams` |
| 投递算力 | `task_dispatch_params` | 不返前端 |
| 算力回调 | `task_callback_params` | `taskCallbackParams` |

表结构、ORM → [details/数据库存储设计.md](./details/数据库存储设计.md)

---

## 九、团队开发规则

```text
1. 所有生图能力统一叫 tool。
2. 前端每个 tool 一个目录：Form + Preview(可选) + tool.ts。
3. tool.ts 必须提供 createForm、validate、buildRequest。
4. 前端提交只传 toolKey + params。
5. 后端每个 tool 一个类：validate、build_task_dispatch_params。
6. MQ Topic、innerTaskId、modelName 等 imggen 参数仅后端组装（无 workflow 字段）。
7. 新增 tool 只改 frontend/src/tools 与 backend/app/tools。
8. 第一版不做收藏、重跑、取消。
9. 联调先用 USE_MOCK=true。
```

---

## 十、新增工具 Checklist

```text
前端：tools/xxx/XxxForm.vue + tool.ts + tools/index.ts
后端：tools/xxx.py + tools/registry.py
不改：task_service、task_api、taskStore、WS/MQ 公共代码
```

完整步骤 → [新增工具开发指南.md](./新增工具开发指南.md)

---

## 十一、推荐开发顺序

```text
阶段 1：Mock 主链路（db + 上传 + WS + 风格迁移）
阶段 2：局部重绘 + MaskEditor
阶段 3：OSS + RocketMQ，关闭 Mock
```

---

## 十二、技术选型

| 层 | 选型 |
|----|------|
| 前端 | Vue3 + Vite + TS + Pinia + Element Plus |
| 后端 | FastAPI + SQLAlchemy + SQLite |
| 文件 | 阿里云 OSS（开发与生产统一） |
| 消息 | RocketMQ（Mock 跳过） |
| 实时 | WebSocket |

专题：OSS / MQ / Mock / 部署 → [details/](./details/)

---

## 十三、与旧 Gradio 的对应

| 旧代码 | 新方案 |
|--------|--------|
| `ucub_mqdraw/ui/*.py` | `frontend/src/tools/` |
| `store.py` | SQLite + `taskStore` |
| `constants.TOOL_WORKFLOW_MAP` | 各 `tools/*.py` 按 toolKey 组装 imggen MQ 参数 |

历史完整方案 → [archive/完整版方案归档.md](./archive/完整版方案归档.md)（仅对照，非日常入口）
