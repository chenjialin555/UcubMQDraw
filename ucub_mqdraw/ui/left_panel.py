import gradio as gr

from ucub_mqdraw.constants import (
    COMPUTE_TYPES,
    COUNT_CHOICES,
    TOOL_ITEMS,
)
from ucub_mqdraw.ui.tool_grid import tool_notice_text


def _tool_btn_classes(index: int) -> list[str]:
    classes = ["tool-pick-btn"]
    if index == 0:
        classes.append("tool-pick-active")
    return classes


def build_left_panel() -> dict:
    tool_buttons: list[gr.Button] = []
    count_buttons: list[gr.Button] = []

    with gr.Column(elem_id="left-panel"):
        gr.HTML('<div class="section-title">UcubMQDraw</div>')

        tool_state = gr.State("风格迁移")
        count_state = gr.State("2张")

        gr.HTML('<div class="subsection-label">创作工具</div>')

        with gr.Row(elem_classes=["tool-btn-row", "tool-btn-row-2"]):
            for idx, name in enumerate(TOOL_ITEMS):
                tool_buttons.append(
                    gr.Button(name, elem_classes=_tool_btn_classes(idx), scale=1)
                )

        tool_notice = gr.HTML(
            f'<div class="tool-notice">{tool_notice_text("风格迁移")}</div>'
        )

        with gr.Column(elem_id="tool-form", elem_classes=["form-card"]):
            with gr.Row(elem_classes=["form-title-row"]):
                form_title = gr.HTML(
                    '<div class="form-title">风格迁移</div>',
                    container=False,
                )
                reset_btn = gr.Button("重置", size="sm", scale=0, min_width=60)

            with gr.Row(elem_classes=["image-upload-row"]):
                base_image = gr.Image(
                    label="底图",
                    type="filepath",
                    height=140,
                    elem_id="base-upload",
                    interactive=True,
                    sources=["upload"],
                    buttons=[],
                    show_label=True,
                    scale=1,
                )
                with gr.Column(scale=1, visible=True) as style_ref_col:
                    style_image = gr.Image(
                        label="风格参考",
                        type="filepath",
                        height=140,
                        elem_id="style-upload",
                        interactive=True,
                        sources=["upload"],
                        buttons=[],
                        show_label=True,
                    )

            with gr.Column(visible=True, elem_classes=["style-only-fields"]) as style_fields:
                gr.HTML('<div class="field-label">数量</div>')
                with gr.Row(elem_classes=["count-pills"]):
                    for choice in COUNT_CHOICES:
                        classes = ["count-pill"]
                        if choice == "2张":
                            classes.append("count-pill-active")
                        count_buttons.append(
                            gr.Button(choice, elem_classes=classes, size="sm")
                        )

                with gr.Row(elem_classes=["strength-row"]):
                    strength = gr.Slider(
                        minimum=0,
                        maximum=1,
                        value=0.75,
                        step=0.01,
                        label="风格强度",
                        scale=7,
                    )
                    strength_value = gr.Textbox(
                        value="0.75",
                        label=" ",
                        interactive=False,
                        scale=1,
                        min_width=60,
                    )

            with gr.Column(visible=False, elem_classes=["inpaint-only-fields"]) as inpaint_fields:
                with gr.Row(elem_classes=["strength-row"]):
                    denoise_strength = gr.Slider(
                        minimum=0,
                        maximum=1,
                        value=0.8,
                        step=0.01,
                        label="重绘强度",
                        scale=7,
                    )
                    denoise_value = gr.Textbox(
                        value="0.80",
                        label=" ",
                        interactive=False,
                        scale=1,
                        min_width=60,
                    )

                with gr.Row(elem_classes=["strength-row"]):
                    mask_blur_radius = gr.Slider(
                        minimum=0,
                        maximum=20,
                        value=6,
                        step=1,
                        label="蒙版羽化",
                        scale=7,
                    )
                    mask_blur_value = gr.Textbox(
                        value="6",
                        label=" ",
                        interactive=False,
                        scale=1,
                        min_width=60,
                    )

            description = gr.Textbox(
                label="补充描述",
                placeholder="可选 · 最多 300 字",
                lines=2,
                max_length=300,
            )

            compute_type = gr.Dropdown(
                choices=list(COMPUTE_TYPES.keys()),
                value="comfy_api并发版",
                label="算力",
            )

    return {
        "tool_state": tool_state,
        "tool_buttons": tool_buttons,
        "tool_notice": tool_notice,
        "form_title": form_title,
        "style_ref_col": style_ref_col,
        "style_fields": style_fields,
        "inpaint_fields": inpaint_fields,
        "count_state": count_state,
        "count_buttons": count_buttons,
        "reset_btn": reset_btn,
        "base_image": base_image,
        "style_image": style_image,
        "strength": strength,
        "strength_value": strength_value,
        "denoise_strength": denoise_strength,
        "denoise_value": denoise_value,
        "mask_blur_radius": mask_blur_radius,
        "mask_blur_value": mask_blur_value,
        "description": description,
        "compute_type": compute_type,
    }
