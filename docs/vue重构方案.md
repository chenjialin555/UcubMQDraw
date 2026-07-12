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
Vue + FastAPI + PostgreSQL + Redis(Docker) + OSS(阿里云) + RocketMQ(阿里云) + JWT + WebSocket 定向推送
```

边界：

- 轻量账号：手机号 / 邮箱 + 密码，JWT 7 天
- 游客可选：`user_guest_public`，前端 localStorage 过滤任务
- 任务按 `user_id` 隔离；WS 从 token 解析用户

详见 [details/用户与鉴权设计.md](./details/用户与鉴权设计.md)。

---

## 三、正式版分三期

> **架构方向是正式版，实现按三期推进。** 详见 [代码阅读指南.md](./代码阅读指南.md)。

### Phase 1：可读正式版

```text
用户：register / login / guest / me + JWT + tasks.user_id
任务：POST 创建、GET 列表、GET 单条
WS：token 鉴权、send_to_user、最小 onmessage + 断线重连
工具：风格迁移、局部重绘（Mock 主链路）
```

### Phase 2：体验增强

```text
改昵称 / 改密码
DELETE / rerun / cancel / favorite
游客 guest_task_ids、WS 拆文件、心跳
局部重绘 MaskEditor 完善
```

### Phase 3：生产增强

```text
OSS + RocketMQ 关 Mock
Redis Pub/Sub 多实例 WS
登录限流、refreshToken、分页与筛选完善
```

### 原 Mock 联调阶段（与 Phase 并行）

```text
阶段 A：Mock 主链路（db + 上传 + WS + 风格迁移）
阶段 B：局部重绘
阶段 C：接 OSS + MQ
```

`USE_MOCK=true` 本地可跳过 MQ；WS 仍建议 `send_to_user`。

---

## 四、最小目录结构

### 前端

```text
frontend/src/
├── api/          http.ts, auth.ts, task.ts, upload.ts
├── ws/           taskWsMessages / taskWsHandlers / taskWsClient
├── tools/        每个工具一个目录
├── stores/       authStore.ts, taskStore.ts
├── components/   TaskList, TaskCard, …
├── pages/        HomePage.vue
└── bootstrap.ts  # Phase 1：guest → connect WS
```

### 后端

```text
backend/app/
├── db.py
├── api/          auth_api, task_api, upload_api, websocket_api
├── tools/        每个工具一个 .py + registry.py
├── services/     task_service, upload_service, mq_service, mock_task_runner, websocket_manager
└── models/       task_model.py
```

### 基础设施（项目根）

```text
docker-compose.yml              # PostgreSQL + Redis（本地 Docker）
docker/postgres/init/01_init.sql
backend/.env.example
```

```text
本机：Vue、FastAPI
Docker：PostgreSQL、Redis
阿里云：OSS、RocketMQ
```

详见 [details/部署与环境变量.md](./details/部署与环境变量.md)。

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
| 数据库 | PostgreSQL（开发 Docker / 生产云 PG） |
| 缓存/WS 总线 | Redis（本地 Docker，非任务队列） |
| 文件 | 阿里云 OSS |
| 消息 | RocketMQ → imggen |
| 实时 | WebSocket（JWT + 用户定向推送） |
| 鉴权 | JWT（passlib bcrypt + python-jose） |
| 多实例 WS | Redis Pub/Sub（可选） |

---

## 十、与旧 Gradio 的对应

| 旧代码 | 新方案 |
|--------|--------|
| `ucub_mqdraw/ui/*.py` | `frontend/src/tools/` |
| `store.py` | PostgreSQL + `taskStore` |
| `constants.TOOL_WORKFLOW_MAP` | 各 `tools/*.py` 组装 MQ 参数 |

历史完整方案 → [archive/完整版方案归档.md](./archive/完整版方案归档.md)
