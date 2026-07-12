# features → tools 术语对照

> 早期归档与 Gradio 时代使用 `features/`；**现行 Vue 重构统一为 `tools/`**。
> 读归档代码或旧讨论时，按本表 mentally 替换即可。

---

## 一、目录与命名

| 归档（旧） | 现行（新） | 说明 |
|-----------|-----------|------|
| `frontend/src/features/` | `frontend/src/tools/` | 每个生图能力一个子目录 |
| `features/style_transfer/` | `tools/style-transfer/` | 目录名 kebab-case |
| `FeatureSelector` | `ToolSelector` | 左栏工具选择组件 |
| `featureKey` | `toolKey` | API 与 store 字段 |
| `featureName` | `toolName` | 展示名 |
| `XxxFeature` | `XxxTool` | 工具模块导出对象 |
| `feature.ts` | `tool.ts` | 单工具入口文件 |

---

## 二、后端对应

| 归档（旧） | 现行（新） |
|-----------|-----------|
| `feature_key` | `tool_key` |
| `FeatureHandler` | `XxxTool`（如 `StyleTransferTool`） |
| `features/` 包 | `tools/` 包 |

数据库列名以 [数据库存储设计.md](../details/数据库存储设计.md) 为准：`tool_key` 写入 `generation_tasks`。

---

## 三、API 请求体

归档可能写：

```json
{
  "featureKey": "style_transfer",
  "params": { }
}
```

现行统一为：

```json
{
  "toolKey": "style_transfer",
  "params": { }
}
```

权威定义 → [API接口.md](../API接口.md#四创建任务)。

---

## 四、阅读归档时的转换规则

1. 看到 `features` → 想 `tools`
2. 看到 `featureKey` → 想 `toolKey`
3. 看到 `completed` 状态 → 想 `succeeded`
4. 看到 WS 广播 → 想 `send_to_user(user_id, ...)`
5. 看到 `USE_LOCAL_STORAGE` → **忽略**，现行一律 OSS

---

## 五、相关文档

- 新增工具步骤 → [新增工具开发指南.md](../新增工具开发指南.md)
- 前端模块示例 → [前端工具模块示例.md](../examples/前端工具模块示例.md)
- 后端处理器示例 → [后端工具处理器示例.md](../examples/后端工具处理器示例.md)
- 归档过时策略 → [归档与现行规范差异.md](./归档与现行规范差异.md)
