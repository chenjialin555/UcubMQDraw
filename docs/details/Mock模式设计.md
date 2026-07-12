# Mock 模式设计

## 一、何时启用

```env
USE_MOCK=true
```

开发联调 imggen 之前，**始终先用 Mock 跑通主链路**。

## 二、与真实模式的差异

| 环节 | Mock | 真实（正式版） |
|------|------|----------------|
| MQ 投递 | 跳过 | `mq_service.send()` → RocketMQ |
| Callback Consumer | 不启动 | 监听 callback topic |
| 进度来源 | 后台线程模拟 | imggen 回调 |
| 输出图 | 固定 mock 图 URL | `task_callback_params.imageUrlList` |
| WS 推送 | 建议仍 `send_to_user` | 按 `user_id` 定向推送 |

**Mock 不用 Redis List 模拟队列**；任务队列正式版仍走 RocketMQ。

## 三、触发时机

`task_service.create_task` 成功写库后：

```python
await ws.send_task_event(user_id, "task.created", task)
update_status(task_id, "dispatching", 5)

if settings.USE_MOCK:
    update_status(task_id, "queued", 10)
    start_mock_task(task_id)
else:
    mq_service.send(task_dispatch_params, tool_key=tool.key)
    task = update_status(task_id, "queued", 10)
    await ws.send_task_event(user_id, "task.updated", task)
```

## 四、模拟进度

```python
steps = [
    ("queued", 10),
    ("dispatching", 20),
    ("running", 40),
    ("running", 60),
    ("running", 80),
    ("succeeded", 100),
]

for status, progress in steps:
    time.sleep(1)
    if status == "succeeded":
        task = mark_succeeded(
            task_id=task_id,
            task_callback_params={
                "status": "success",
                "imageUrlList": ["/static/mock-output.png"],
                "costTime": 6.5,
            },
            cost_time=6.5,
        )
        ws.send_task_event(task.user_id, "task.succeeded", task)
    else:
        task = update_status(task_id, status, progress)
        ws.send_task_event(task.user_id, "task.updated", task)
```

终态使用 `succeeded`（不是 `completed`）。

## 五、前端表现

```text
POST /tasks 成功
  → 右栏立即出现新任务（queued）
  → 约 7 秒内进度条走完
  → succeeded 后显示 mock 输出图
```

## 六、切换到真实模式

```text
1. 配置 RocketMQ 环境变量
2. USE_MOCK=false
3. 确认 imggen 能消费 task topic
4. 确认 callback consumer 能收到消息
5. callback 更新 DB 后 send_to_user 推 WS
6. 提交真实任务，观察 DB 与 WS 更新
```

## 七、调试建议

```text
□ Mock 跑通后再接 MQ
□ Network 看 POST /tasks 的 params 是否正确
□ 后端日志看 task_dispatch_params 是否组装正确
□ WS 面板看 task.updated / task.succeeded 是否推送
□ 断线重连后 fetchTasks 能否补齐状态
```
