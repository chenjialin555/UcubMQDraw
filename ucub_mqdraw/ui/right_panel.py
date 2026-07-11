import html

from ucub_mqdraw.models import TaskStatus
from ucub_mqdraw.store import RUNNING_STATUSES, list_tasks


def _empty_record_html() -> str:
    return """
    <div class="empty-record">
        <div class="empty-record-icon">✨</div>
        <div class="empty-record-title">暂无创作记录</div>
        <div class="empty-record-sub">提交任务后会自动显示生成进度</div>
    </div>
    """


def _status_badge(status: TaskStatus) -> str:
    if status == TaskStatus.COMPLETED:
        return '<span class="status-badge status-success">已完成</span>'

    if status in RUNNING_STATUSES:
        return '<span class="status-badge status-running">进行中</span>'

    if status == TaskStatus.FAILED:
        return '<span class="status-badge status-failed">失败</span>'

    return '<span class="status-badge">未知</span>'


def render_task_cards(filter_type: str = "全部") -> str:
    tasks = list_tasks(filter_type)

    if not tasks:
        return _empty_record_html()

    cards = []

    for task in tasks:
        desc = html.escape(task.description or "—")
        task_type = html.escape(task.task_type)
        task_id_tail = html.escape(task.task_id[-8:])

        header = f"""
        <div class="task-card">
            <div class="task-card-header">
                <div>{_status_badge(task.status)}</div>
                <div class="task-id">#{task_id_tail}</div>
            </div>
            <div class="task-type">{task_type}</div>
            <div class="task-time">{html.escape(task.created_at)}</div>
            <div class="task-desc">{desc}</div>
        """

        if task.status == TaskStatus.COMPLETED:
            input_html = (
                f'<img class="thumb-img" src="{html.escape(task.input_preview)}" />'
                if task.input_preview and task.input_preview.startswith(("http", "/"))
                else '<div class="thumb-placeholder">输入</div>'
            )
            output_html = (
                f'<img class="thumb-img" src="{html.escape(task.output_preview)}" />'
                if task.output_preview
                else '<div class="thumb-placeholder">输出</div>'
            )

            body = f"""
                <div class="thumb-row">
                    {input_html}
                    {output_html}
                </div>
                <div class="task-actions">
                    <button class="mini-btn">收藏</button>
                    <button class="mini-btn">下载</button>
                    <button class="mini-btn">更多</button>
                </div>
            </div>
            """

        elif task.status in RUNNING_STATUSES:
            body = f"""
                <div style="margin-top:10px;font-size:12px;color:#1d4ed8;">
                    {task.progress}%
                </div>
                <div class="progress-bar">
                    <div class="progress-inner" style="width:{task.progress}%;"></div>
                </div>
                <div class="task-actions">
                    <button class="mini-btn">取消</button>
                </div>
            </div>
            """

        elif task.status == TaskStatus.FAILED:
            error = html.escape(task.error_message or "未知错误")
            body = f"""
                <div class="error-message">{error}</div>
                <div class="task-actions">
                    <button class="mini-btn">重跑</button>
                </div>
            </div>
            """

        else:
            body = "</div>"

        cards.append(header + body)

    return "\n".join(cards)
