# UcubMQDraw 文档导航

> 日常开发看短文档；遇到具体问题查专题；需要复制代码看 examples。

## 日常开发必看

| 文档 | 用途 |
|------|------|
| [vue重构方案.md](./vue重构方案.md) | 项目整体规范、MVP 范围、目录结构、开发规则 |
| [开发入门.md](./开发入门.md) | 启动项目、目录说明、主链路 |
| [新增工具开发指南.md](./新增工具开发指南.md) | **最常看**：新增一个生图工具该改哪些文件 |
| [API接口.md](./API接口.md) | 前后端 HTTP / WebSocket 契约（**字段唯一权威**） |
| [ui_design.md](./ui_design.md) | 三栏布局、组件树、CSS Token、交互验收 |

## 阅读路径

### 新人

```text
1. 开发入门.md
2. vue重构方案.md
3. 新增工具开发指南.md
4. API接口.md
5. ui_design.md（做前端页面时）
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
2. details/任务状态与任务流转.md  +  examples/任务状态与流转示例.md
3. details/RocketMQ对接设计.md      +  examples/RocketMQ对接示例.md
4. details/WebSocket推送机制.md     +  examples/WebSocket推送示例.md
5. details/OSS上传设计.md           +  examples/OSS上传示例.md
```

## 专题细节（`details/`）

| 文档 | 内容 |
|------|------|
| [任务状态与任务流转.md](./details/任务状态与任务流转.md) | 状态定义、流转、前端展示 |
| [数据库存储设计.md](./details/数据库存储设计.md) | 表结构、三列 JSON、ORM |
| [WebSocket推送机制.md](./details/WebSocket推送机制.md) | 用户定向推送、事件类型、多实例 Redis Pub/Sub |
| [OSS上传设计.md](./details/OSS上传设计.md) | 上传接口、OSS 配置 |
| [RocketMQ对接设计.md](./details/RocketMQ对接设计.md) | Topic、Producer、Consumer |
| [Mock模式设计.md](./details/Mock模式设计.md) | 开发联调、模拟进度 |
| [部署与环境变量.md](./details/部署与环境变量.md) | .env、CORS、Nginx |

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
| [WebSocket推送示例.md](./examples/WebSocket推送示例.md) | ws.ts、websocket_manager、正式版 taskStore |
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
