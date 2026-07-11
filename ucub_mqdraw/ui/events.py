import gradio as gr

from ucub_mqdraw.config import USE_MOCK
from ucub_mqdraw.constants import (
    COMPUTE_TYPES,
    COUNT_CHOICES,
    TOOL_ITEMS,
    workflow_for_tool,
)
from ucub_mqdraw.models import GenerationTask, InpaintForm, StyleTransferForm, TaskStatus
from ucub_mqdraw.services.api_client import GenerationApiClient
from ucub_mqdraw.services.mock_task_runner import start_mock_task
from ucub_mqdraw.store import add_task, update_task
from ucub_mqdraw.ui.center_panel import _empty_preview_html, _mask_hint_html
from ucub_mqdraw.ui.right_panel import render_task_cards
from ucub_mqdraw.ui.tool_grid import tool_notice_text
from ucub_mqdraw.utils.mask import mask_path_from_editor


api_client = GenerationApiClient()


def _tool_btn_class_updates(selected_index: int):
    updates = []
    for idx in range(len(TOOL_ITEMS)):
        if idx == selected_index:
            updates.append(gr.update(elem_classes=["tool-pick-btn", "tool-pick-active"]))
        else:
            updates.append(gr.update(elem_classes=["tool-pick-btn"]))
    return updates


def select_tool(tool_index: int, base_image_path=None):
    name = TOOL_ITEMS[tool_index]
    is_style = name == "风格迁移"
    has_image = bool(base_image_path)

    if not has_image:
        preview_html = _empty_preview_html() if is_style else _mask_hint_html()
        preview_empty_update = gr.update(value=preview_html, visible=True)
        main_preview_update = gr.update(visible=False)
    elif is_style:
        preview_empty_update = gr.update(visible=False)
        main_preview_update = gr.update(value=base_image_path, visible=True)
    else:
        preview_empty_update = gr.update(visible=False)
        main_preview_update = gr.update(value=base_image_path, visible=True)

    return (
        name,
        f'<div class="tool-notice">{tool_notice_text(name)}</div>',
        *_tool_btn_class_updates(tool_index),
        gr.update(value=f'<div class="form-title">{name}</div>'),
        gr.update(visible=is_style),
        gr.update(visible=is_style),
        gr.update(visible=not is_style),
        gr.update(visible=not is_style),
        gr.update(value="立即迁移" if is_style else "立即重绘"),
        preview_empty_update,
        main_preview_update,
        gr.update(visible=False, value=None),
    )


def _count_btn_updates(selected: str):
    updates = []
    for choice in COUNT_CHOICES:
        if choice == selected:
            updates.append(gr.update(elem_classes=["count-pill", "count-pill-active"]))
        else:
            updates.append(gr.update(elem_classes=["count-pill"]))
    return updates


def select_count(count: str):
    return count, *_count_btn_updates(count)


def on_strength_change(value: float) -> str:
    return f"{value:.2f}"


def on_denoise_change(value: float) -> str:
    return f"{value:.2f}"


def on_mask_blur_change(value: float) -> str:
    return str(int(value))


def reset_form():
    return (
        None,
        None,
        "2张",
        0.75,
        "0.75",
        0.8,
        "0.80",
        6,
        "6",
        "",
        "comfy_api并发版",
        *_count_btn_updates("2张"),
        gr.update(value=None, visible=False),
        gr.update(value=_empty_preview_html(), visible=True),
        gr.update(visible=False, value=None),
    )


def update_preview(base_image_path, tool_name):
    has_image = bool(base_image_path)
    is_style = tool_name == "风格迁移"

    if not has_image:
        empty_html = _empty_preview_html() if is_style else _mask_hint_html()
        return (
            gr.update(value=None, visible=False),
            gr.update(value=empty_html, visible=True),
            gr.update(visible=False, value=None),
        )

    if is_style:
        return (
            gr.update(value=base_image_path, visible=True),
            gr.update(visible=False),
            gr.update(visible=False, value=None),
        )

    return (
        gr.update(value=base_image_path, visible=True),
        gr.update(visible=False),
        gr.update(visible=False, value=None),
    )


def open_mask_editor(base_image_path):
    if not base_image_path:
        raise gr.Error("请先上传底图")

    return (
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(
            visible=True,
            value={
                "background": base_image_path,
                "layers": [],
                "composite": None,
            },
        ),
    )


def reupload_base(tool_name):
    empty_html = _empty_preview_html() if tool_name == "风格迁移" else _mask_hint_html()
    return (
        None,
        gr.update(value=None, visible=False),
        gr.update(value=empty_html, visible=True),
        gr.update(visible=False, value=None),
    )


def validate_style_form(form: StyleTransferForm) -> None:
    if not form.base_image_path:
        raise gr.Error("请先上传底图")

    if not form.style_image_path:
        raise gr.Error("请先上传风格参考图")

    if form.description and len(form.description) > 300:
        raise gr.Error("补充描述不能超过 300 字")


def validate_inpaint_form(form: InpaintForm) -> None:
    if not form.base_image_path:
        raise gr.Error("请先上传底图")

    if not mask_path_from_editor(form.mask_editor_value):
        raise gr.Error("请先点击「画蒙版」并圈选重绘区域")

    if form.description and len(form.description) > 300:
        raise gr.Error("补充描述不能超过 300 字")


def submit_task(
    base_image_path,
    style_image_path,
    generation_count,
    style_strength,
    denoise_strength,
    mask_blur_radius,
    description,
    compute_type,
    tool_name,
    mask_editor_value,
):
    workflow_template = workflow_for_tool(tool_name)

    if tool_name == "风格迁移":
        form = StyleTransferForm(
            base_image_path=base_image_path,
            style_image_path=style_image_path,
            generation_count=generation_count,
            style_strength=style_strength,
            description=description or "",
            compute_type=compute_type,
            workflow_template=workflow_template,
            tool_name=tool_name,
        )
        validate_style_form(form)

        task = GenerationTask(
            status=TaskStatus.CREATED,
            task_type=tool_name,
            tool=tool_name,
            compute_type=COMPUTE_TYPES.get(compute_type, compute_type),
            workflow_template=workflow_template,
            description=form.description,
            input_preview=form.base_image_path or "",
        )
        task.request_payload = api_client.build_style_transfer_payload(task.task_id, form)
        submit_api = lambda: api_client.submit_style_transfer(task.task_id, form)
    else:
        form = InpaintForm(
            base_image_path=base_image_path,
            mask_editor_value=mask_editor_value,
            denoise_strength=denoise_strength,
            mask_blur_radius=int(mask_blur_radius),
            description=description or "",
            compute_type=compute_type,
            workflow_template=workflow_template,
            tool_name=tool_name,
        )
        validate_inpaint_form(form)

        task = GenerationTask(
            status=TaskStatus.CREATED,
            task_type=tool_name,
            tool=tool_name,
            compute_type=COMPUTE_TYPES.get(compute_type, compute_type),
            workflow_template=workflow_template,
            description=form.description,
            input_preview=form.base_image_path or "",
        )
        task.request_payload = api_client.build_inpaint_payload(task.task_id, form)
        submit_api = lambda: api_client.submit_inpaint(task.task_id, form)

    add_task(task)

    if USE_MOCK:
        update_task(task.task_id, status=TaskStatus.QUEUED, progress=5)
        start_mock_task(task.task_id)
        message = f"任务已创建 · {task.task_id[-8:]}"
    else:
        try:
            data = submit_api()
            update_task(task.task_id, status=TaskStatus.QUEUED, progress=5)
            message = f"已提交 · {data.get('taskId') or task.task_id}"
        except Exception as exc:
            update_task(
                task.task_id,
                status=TaskStatus.FAILED,
                error_message=str(exc),
            )
            message = f"提交失败 · {exc}"

    return gr.update(interactive=True), render_task_cards("全部"), message


def set_submit_disabled():
    return gr.update(interactive=False)


def set_submit_enabled():
    return gr.update(interactive=True)


def set_record_filter(filter_name: str):
    return filter_name, render_task_cards(filter_name)


def refresh_record_cards(filter_name: str):
    return render_task_cards(filter_name)
