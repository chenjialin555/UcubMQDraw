# Mock 模式设计

## 一、何时启用

```env
USE_MOCK=true
```

开发联调 imggen 之前，**始终先用 Mock 跑通主链路**。

## 二、与真实模式的差异

| 环节 | Mock | 真实 |
|------|------|------|
| MQ 投递 | 跳过 | `mq_service.send()` |
| Callback Consumer | 不启动 | 监听 callback topic |
| 进度来源 | 后台线程模拟 | imggen 回调 |
| 输出图 | 固定 mock 图 URL | `task_callback_params.imageUrlList` |

## 三、触发时机

`task_service.create_task` 成功写库后：

```python
if settings.USE_MOCK:
    update_task_status(task_id, "queued", 5)
    start_mock_task(task_id)
else:
    mq_service.send(task_dispatch_params, tool_key=tool.key)
    update_task_status(task_id, "queued", 5)
```

## 四、模拟进度

`mock_task_runner.py` 在后台线程执行：

```python
steps = [
    ("queued", 5),
    ("dispatching", 15),
    ("running", 30),
    ("running", 50),
    ("running", 75),
    ("running", 90),
    ("completed", 100),
]

for status, progress in steps:
    time.sleep(1)
    task = update_status(task_id, status, progress)
    if status == "completed":
        task = update_result(
            task_id=task_id,
            task_callback_params={
                "status": "success",
                "imageUrlList": ["/static/mock-output.png"],
                "costTime": 6.5,
            },
            cost_time=6.5,
        )
    websocket_manager.broadcast_task_update(task)
```

## 五、前端表现

```text
POST /tasks 成功
  → 右栏立即出现新任务（queued）
  → 约 7 秒内进度条走完
  → completed 后显示 mock 输出图
```

## 六、Mock 输出图

准备一张占位图：`static/mock-output.png`，与 `main.py` 静态挂载路径一致。

## 七、切换到真实模式

```text
1. 配置 RocketMQ 环境变量
2. USE_MOCK=false
3. 确认 imggen 能消费 task topic
4. 确认 callback consumer 能收到消息
5. 提交真实任务，观察 DB 与 WS 更新
```

## 八、调试建议

```text
□ Mock 跑通后再接 MQ
□ Network 看 POST /tasks 的 params 是否正确
□ 后端日志看 task_dispatch_params 是否组装正确
□ WS 面板看 task_update 是否推送
```
