import gradio as gr

from ucub_mqdraw.constants import COUNT_CHOICES
from ucub_mqdraw.ui import events
from ucub_mqdraw.ui.center_panel import build_center_panel
from ucub_mqdraw.ui.left_panel import build_left_panel
from ucub_mqdraw.ui.right_panel import render_task_cards

# 代码变更后递增，触发浏览器自动刷新，避免 Gradio fn_index 缓存错位
APP_UI_VERSION = "20260711-6"


def build_app() -> gr.Blocks:
    with gr.Blocks(title="UcubMQDraw 优卡普 AI 生图调度中台") as demo:
        current_filter = gr.State("全部")

        with gr.Column(elem_id="main-shell"):
            with gr.Row(elem_id="three-column-row"):
                left = build_left_panel()
                center = build_center_panel()
                right = build_right_panel()

        bind_events(left, center, right, current_filter)
        register_version_guard(demo)

    return demo


def build_right_panel() -> dict:
    with gr.Column(elem_id="right-panel"):
        with gr.Row(elem_classes=["record-header-row"]):
            gr.HTML(
                """
                <div class="record-header">
                    <div class="section-title" style="margin-bottom:0;">创作记录</div>
                </div>
                """,
                container=False,
                scale=4,
            )
            refresh_btn = gr.Button("刷新", size="sm", scale=0, min_width=64)

        with gr.Row(elem_classes=["record-tabs"]):
            filter_all_btn = gr.Button("全部", size="sm", elem_classes=["record-pill", "record-pill-active"])
            filter_running_btn = gr.Button("进行中", size="sm", elem_classes=["record-pill"])
            filter_done_btn = gr.Button("已完成", size="sm", elem_classes=["record-pill"])
            filter_fav_btn = gr.Button("收藏", size="sm", elem_classes=["record-pill"])

        task_cards = gr.HTML(render_task_cards("全部"))

    return {
        "refresh_btn": refresh_btn,
        "filter_all_btn": filter_all_btn,
        "filter_running_btn": filter_running_btn,
        "filter_done_btn": filter_done_btn,
        "filter_fav_btn": filter_fav_btn,
        "task_cards": task_cards,
    }


def register_version_guard(demo: gr.Blocks) -> None:
    demo.load(
        fn=None,
        js=f"""() => {{
            const version = "{APP_UI_VERSION}";
            const key = "ucub_mqdraw_ui_version";
            const prev = window.sessionStorage.getItem(key);
            window.sessionStorage.setItem(key, version);
            if (prev && prev !== version) {{
                window.location.reload();
            }}
        }}""",
    )


def _make_select_tool_handler(index: int):
    def handler(base_image_path):
        return events.select_tool(index, base_image_path)

    return handler


def _make_count_handler(count: str):
    def handler():
        return events.select_count(count)

    return handler


def bind_events(left, center, right, current_filter):
    tool_outputs = [
        left["tool_state"],
        left["tool_notice"],
        *left["tool_buttons"],
        left["form_title"],
        left["style_ref_col"],
        left["style_fields"],
        left["inpaint_fields"],
        center["draw_mask_btn"],
        center["submit_btn"],
        center["preview_empty"],
        center["main_preview"],
        center["mask_editor"],
    ]

    for idx, btn in enumerate(left["tool_buttons"]):
        btn.click(
            fn=_make_select_tool_handler(idx),
            inputs=left["base_image"],
            outputs=tool_outputs,
        )

    count_outputs = [left["count_state"], *left["count_buttons"]]
    for idx, btn in enumerate(left["count_buttons"]):
        btn.click(
            fn=_make_count_handler(COUNT_CHOICES[idx]),
            outputs=count_outputs,
        )

    left["strength"].change(
        fn=events.on_strength_change,
        inputs=left["strength"],
        outputs=left["strength_value"],
    )

    left["denoise_strength"].change(
        fn=events.on_denoise_change,
        inputs=left["denoise_strength"],
        outputs=left["denoise_value"],
    )

    left["mask_blur_radius"].change(
        fn=events.on_mask_blur_change,
        inputs=left["mask_blur_radius"],
        outputs=left["mask_blur_value"],
    )

    left["base_image"].change(
        fn=events.update_preview,
        inputs=[left["base_image"], left["tool_state"]],
        outputs=[
            center["main_preview"],
            center["preview_empty"],
            center["mask_editor"],
        ],
    )

    reset_outputs = [
        left["base_image"],
        left["style_image"],
        left["count_state"],
        left["strength"],
        left["strength_value"],
        left["denoise_strength"],
        left["denoise_value"],
        left["mask_blur_radius"],
        left["mask_blur_value"],
        left["description"],
        left["compute_type"],
        *left["count_buttons"],
        center["main_preview"],
        center["preview_empty"],
        center["mask_editor"],
    ]

    left["reset_btn"].click(
        fn=events.reset_form,
        outputs=reset_outputs,
    )

    center["reupload_btn"].click(
        fn=events.reupload_base,
        inputs=left["tool_state"],
        outputs=[
            left["base_image"],
            center["main_preview"],
            center["preview_empty"],
            center["mask_editor"],
        ],
    )

    center["draw_mask_btn"].click(
        fn=events.open_mask_editor,
        inputs=left["base_image"],
        outputs=[
            center["preview_empty"],
            center["main_preview"],
            center["mask_editor"],
        ],
    )

    submit_chain = center["submit_btn"].click(
        fn=events.set_submit_disabled,
        outputs=center["submit_btn"],
    )

    submit_chain.then(
        fn=events.submit_task,
        inputs=[
            left["base_image"],
            left["style_image"],
            left["count_state"],
            left["strength"],
            left["denoise_strength"],
            left["mask_blur_radius"],
            left["description"],
            left["compute_type"],
            left["tool_state"],
            center["mask_editor"],
        ],
        outputs=[
            center["submit_btn"],
            right["task_cards"],
            center["submit_result"],
        ],
    ).then(
        fn=events.set_submit_enabled,
        outputs=center["submit_btn"],
    )

    right["refresh_btn"].click(
        fn=events.refresh_record_cards,
        inputs=current_filter,
        outputs=right["task_cards"],
    )

    right["filter_all_btn"].click(
        fn=lambda: events.set_record_filter("全部"),
        outputs=[current_filter, right["task_cards"]],
    )

    right["filter_running_btn"].click(
        fn=lambda: events.set_record_filter("进行中"),
        outputs=[current_filter, right["task_cards"]],
    )

    right["filter_done_btn"].click(
        fn=lambda: events.set_record_filter("已完成"),
        outputs=[current_filter, right["task_cards"]],
    )

    right["filter_fav_btn"].click(
        fn=lambda: events.set_record_filter("收藏"),
        outputs=[current_filter, right["task_cards"]],
    )
