# UcubMQDraw 文档导航

> 日常开发看短文档；**不知道从哪读** → [代码阅读指南.md](./代码阅读指南.md)。

## 日常开发必看

| 文档 | 用途 |
|------|------|
| [代码阅读指南.md](./代码阅读指南.md) | **推荐阅读顺序**、分期实现、暂时别先看什么 |
| [vue重构方案.md](./vue重构方案.md) | 项目整体规范、分期、目录结构 |
| [开发入门.md](./开发入门.md) | 启动、目录、主链路 |
| [新增工具开发指南.md](./新增工具开发指南.md) | **最常看**：新增工具改哪些文件 |
| [API接口.md](./API接口.md) | HTTP / WS 契约（**字段唯一权威**） |
| [ui_design.md](./ui_design.md) | 三栏布局、组件树、交互验收 |

## 阅读路径

### 新人

```text
1. 代码阅读指南.md
2. 开发入门.md
3. vue重构方案.md
4. 新增工具开发指南.md
5. API接口.md
```

### 只做前端工具

```text
1. 新增工具开发指南.md
2. API接口.md
3. ui_design.md
4. examples/前端工具模块示例.md
5. examples/前端HTTP封装示例.md
```

### 只做后端任务链路

```text
1. 开发入门.md
2. details/用户与鉴权设计.md
3. details/任务状态与任务流转.md  +  examples/任务状态与流转示例.md
4. details/RocketMQ对接设计.md      +  examples/RocketMQ对接示例.md
5. details/imggen-stub联调模式设计.md + examples/imggen-stub示例.md
6. details/WebSocket推送机制.md     +  examples/WebSocket推送示例.md
7. details/OSS上传设计.md           +  examples/OSS上传示例.md
```

## 专题细节（`details/`）

| 文档 | 内容 |
|------|------|
| [用户与鉴权设计.md](./details/用户与鉴权设计.md) | 注册登录、JWT、游客、任务 user_id 隔离 |
| [任务状态与任务流转.md](./details/任务状态与任务流转.md) | 状态定义、流转、前端展示 |
| [数据库存储设计.md](./details/数据库存储设计.md) | PostgreSQL 表结构、JSONB、ORM |
| [WebSocket推送机制.md](./details/WebSocket推送机制.md) | 用户定向推送、Redis Pub/Sub（Phase 3） |
| [OSS上传设计.md](./details/OSS上传设计.md) | 上传接口、OSS 配置（阿里云） |
| [RocketMQ对接设计.md](./details/RocketMQ对接设计.md) | Topic、Producer、Consumer（阿里云） |
| [imggen-stub联调模式设计.md](./details/imggen-stub联调模式设计.md) | 本地假 imggen，走真实 MQ 链路（**禁止业务侧 Mock**） |
| [部署与环境变量.md](./details/部署与环境变量.md) | Docker PostgreSQL/Redis、OSS、RocketMQ、.env |

## 示例代码（`examples/`）

| 文档 | 内容 |
|------|------|
| [HomePage完整示例.md](./examples/HomePage完整示例.md) | 首页三栏布局与提交流程 |
| [前端HTTP封装示例.md](./examples/前端HTTP封装示例.md) | axios http.ts、task.ts、upload.ts |
| [前端工具模块示例.md](./examples/前端工具模块示例.md) | style-transfer / inpaint tool.ts |
| [后端工具处理器示例.md](./examples/后端工具处理器示例.md) | StyleTransferTool / InpaintTool |
| [MaskEditor示例.md](./examples/MaskEditor示例.md) | 蒙版编辑与上传 |
| [OSS上传示例.md](./examples/OSS上传示例.md) | oss_client、upload_api、ImageUploader |
| [RocketMQ对接示例.md](./examples/RocketMQ对接示例.md) | Producer、Consumer、回调处理 |
| [imggen-stub示例.md](./examples/imggen-stub示例.md) | stub 目录、消费 task、投递 callback |
| [WebSocket推送示例.md](./examples/WebSocket推送示例.md) | **§二最小版** + 拆文件 ws/ + 分期增强 |
| [任务状态与流转示例.md](./examples/任务状态与流转示例.md) | TaskCard、状态机、callback 驱动 |

## 归档

| 文档 | 内容 |
|------|------|
| [归档与现行规范差异.md](./archive/归档与现行规范差异.md) | **先读本文**：归档中已废弃内容一览 |
| [features-to-tools术语对照.md](./archive/features-to-tools术语对照.md) | 旧 features 术语 → 现行 tools 术语 |
| [AI生成的项目计划书.md](./archive/AI生成的项目计划书.md) | Gradio 时代立项稿；**禁止作实现依据**（旧 Mock / `completed` 已删可复制代码） |
| [完整版方案归档.md](./archive/完整版方案归档.md) | 早期完整方案（若仍存在）；仅查历史背景 |

> `docs/archive/` **不会**合并进项目根目录 `总.md`，避免旧稿污染日常检索。

## 其他参考

| 文档 | 说明 |
|------|------|
| [mq_contract.md](./mq_contract.md) | imggen MQ 消息体字段（与 imggen 对齐） |

## 合并全文

项目根目录运行 `./merge-docs.sh` 或 `merge-docs.bat` 可生成 [总.md](../总.md)（**不含** `docs/archive/`，仅供离线阅读现行文档）。
