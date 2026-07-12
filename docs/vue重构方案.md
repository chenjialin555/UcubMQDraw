# UcubMQDraw 开发规范

> 用 Vue3 + FastAPI 替换 Gradio。本文档是**总规范**，只讲原则和边界；细节见专题文档。

**文档入口** → [README.md](./README.md)

## 日常开发看这四份

| 文档 | 用途 |
|------|------|
| **本文档** | 总原则、架构、目录、开发规则 |
| [开发入门.md](./开发入门.md) | 启动、目录、主链路 |
| [新增工具开发指南.md](./新增工具开发指南.md) | **最常看**：新增工具改哪些文件 |
| [API接口.md](./API接口.md) | HTTP / WS 契约（**字段唯一权威**） |

---

## 一、开发人员只需记住 4 个概念

```text
1. 工具 tool      — 一种生图能力（风格迁移、局部重绘…）
2. 表单 form      — 用户填的参数
3. 任务 task      — 一次提交对应数据库一行
4. 状态 event     — WebSocket 推送任务事件，右栏自动刷新
```

---

## 二、正式版架构

```text
Vue 前端
  ├─ HTTP：创建、删除、再次生成、取消、收藏、查询历史
  └─ WebSocket：只接收任务事件通知

FastAPI 后端
  ├─ 写 MySQL（生产）/ SQLite（开发库）
  ├─ OSS 上传
  ├─ RocketMQ 投递 imggen
  └─ callback consumer → 更新 DB → WS 定向推送

RocketMQ  任务队列（不用 Redis List 替代）
Redis Pub/Sub（可选）  多实例 WebSocket 事件分发
```

**边界：**

- 前端只传 `toolKey` + `params`
- 后端 `tools/xxx.py` 负责校验、组装 MQ 参数
- **HTTP 负责业务命令，WebSocket 只推事件**
- 任务状态以 DB 为准，WS 重连后必须 `fetchTasks` 补齐

---

## 三、开发阶段

```text
阶段 1：Mock 主链路（db + 上传 + WS + 风格迁移）
阶段 2：局部重绘 + MaskEditor
阶段 3：OSS + RocketMQ，关闭 Mock
阶段 4：用户鉴权 + 定向 WS + 分页 + 删除/再次生成/取消
```

`USE_MOCK=true` 本地开发可跳过 MQ，但 WS 仍建议按 `user_id` 定向推送，便于与正式版一致。

---

## 四、最小目录结构

### 前端

```text
frontend/src/
├── api/          http.ts, task.ts, upload.ts
├── tools/        每个工具一个目录：Form + Preview(可选) + tool.ts
├── components/   ImageUploader, MaskEditor, TaskList, TaskCard
├── stores/       taskStore.ts
├── pages/        HomePage.vue
└── utils/        ws.ts
```

### 后端

```text
backend/app/
├── db.py
├── api/          task_api, upload_api, websocket_api
├── tools/        每个工具一个 .py + registry.py
├── services/     task_service, upload_service, mq_service, mock_task_runner, websocket_manager
└── models/       task_model.py
```

---

## 五、工具模块模式

（与 MVP 相同，见 [新增工具开发指南.md](./新增工具开发指南.md)）

---

## 六、任务主链路

```text
上传图 → tool.buildRequest() → POST /tasks
  → validate → 写 DB（含 user_id）→ RocketMQ / Mock
  → imggen 回调 → 幂等更新 DB
  → WS send_to_user → taskStore.upsertTask
```

状态与流转 → [details/任务状态与任务流转.md](./details/任务状态与任务流转.md)

---

## 七、三列 JSON 参数

| 阶段 | DB 列 | API 字段 |
|------|-------|----------|
| 用户提交 | `task_submit_params` | `taskSubmitParams` |
| 投递算力 | `task_dispatch_params` | 不返前端 |
| 算力回调 | `task_callback_params` | `taskCallbackParams` |

表结构 → [details/数据库存储设计.md](./details/数据库存储设计.md)

---

## 八、团队开发规则

```text
1. 所有生图能力统一叫 tool。
2. 前端每个 tool 一个目录：Form + Preview(可选) + tool.ts。
3. tool.ts 必须提供 createForm、validate、buildRequest。
4. 前端提交只传 toolKey + params。
5. 后端每个 tool 一个类：validate、build_task_dispatch_params。
6. MQ 参数仅后端组装；前端不传 innerTaskId / computeType。
7. 新增 tool 只改 frontend/src/tools 与 backend/app/tools。
8. 业务命令走 HTTP；WebSocket 只推事件，不在 WS 里删任务/再次生成。
9. 任务队列走 RocketMQ，不用 Redis List。
10. 联调先用 USE_MOCK=true。
```

---

## 九、技术选型

| 层 | 选型 |
|----|------|
| 前端 | Vue3 + Vite + TS + Pinia + Element Plus |
| 后端 | FastAPI + SQLAlchemy |
| 数据库 | MySQL（生产）/ SQLite（开发） |
| 文件 | 阿里云 OSS |
| 消息 | RocketMQ → imggen |
| 实时 | WebSocket（用户定向推送） |
| 多实例 WS | Redis Pub/Sub（可选） |

---

## 十、与旧 Gradio 的对应

| 旧代码 | 新方案 |
|--------|--------|
| `ucub_mqdraw/ui/*.py` | `frontend/src/tools/` |
| `store.py` | MySQL/SQLite + `taskStore` |
| `constants.TOOL_WORKFLOW_MAP` | 各 `tools/*.py` 组装 MQ 参数 |

历史完整方案 → [archive/完整版方案归档.md](./archive/完整版方案归档.md)
