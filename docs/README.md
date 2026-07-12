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
5. details/WebSocket推送机制.md     +  examples/WebSocket推送示例.md
6. details/OSS上传设计.md           +  examples/OSS上传示例.md
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
| [Mock模式设计.md](./details/Mock模式设计.md) | 开发联调、模拟进度 |
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
| [WebSocket推送示例.md](./examples/WebSocket推送示例.md) | **§二最小版** + 拆文件 ws/ + 分期增强 |
| [任务状态与流转示例.md](./examples/任务状态与流转示例.md) | TaskCard、状态机、Mock 步进 |

## 归档

| 文档 | 内容 |
|------|------|
| [完整版方案归档.md](./archive/完整版方案归档.md) | 早期 3000+ 行完整方案，**仅查历史背景** |
| [归档与现行规范差异.md](./archive/归档与现行规范差异.md) | 归档中已废弃或被现行规范替代的内容 |
| [features-to-tools术语对照.md](./archive/features-to-tools术语对照.md) | 旧 features 术语 → 现行 tools 术语 |

> 读归档前请先读「归档与现行规范差异」和「features-to-tools术语对照」。

## 其他参考

| 文档 | 说明 |
|------|------|
| [mq_contract.md](./mq_contract.md) | imggen MQ 消息体字段（与 imggen 对齐） |
| [AI生成的项目计划书.md](./AI生成的项目计划书.md) | 立项背景与 Gradio 时代规划（非日常入口） |

## 合并全文

项目根目录运行 `merge-docs.bat` 可生成 [总.md](../总.md)（全部 docs 合并版，仅供离线阅读）。
