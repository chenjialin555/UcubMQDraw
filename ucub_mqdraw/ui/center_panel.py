import gradio as gr


def _empty_preview_html() -> str:
    return """
    <div class="empty-preview-box">
        <div class="empty-preview-icon">🖼</div>
        <div class="empty-preview-title">上传底图后在这里预览</div>
        <div class="empty-preview-subtitle">支持 PNG / JPG / WEBP，建议使用高清图片</div>
    </div>
    """


def _mask_hint_html() -> str:
    return """
    <div class="empty-preview-box">
        <div class="empty-preview-icon">🖌</div>
        <div class="empty-preview-title">点击「画蒙版」开始圈选重绘区域</div>
        <div class="empty-preview-subtitle">白色画笔标记需要重绘的画面范围</div>
    </div>
    """


def build_center_panel() -> dict:
    with gr.Column(elem_id="center-panel"):
        gr.HTML('<div class="section-title">素材预览</div>')

        with gr.Column(elem_id="preview-wrap"):
            preview_empty = gr.HTML(_empty_preview_html(), elem_classes=["preview-empty"])
            main_preview = gr.Image(
                label=None,
                type="filepath",
                interactive=False,
                elem_id="main-preview",
                visible=False,
                height=420,
                buttons=[],
            )
            mask_editor = gr.ImageEditor(
                label=None,
                type="filepath",
                visible=False,
                elem_id="mask-editor",
                height=420,
                transforms=[],
                brush=gr.Brush(
                    default_size=24,
                    colors=["#FFFFFF"],
                    color_mode="fixed",
                ),
                eraser=gr.Eraser(default_size=20),
                buttons=[],
            )

        with gr.Row(elem_classes=["center-bottom-buttons"]):
            reupload_btn = gr.Button("重新上传")
            draw_mask_btn = gr.Button("画蒙版", visible=False, elem_classes=["mask-action-btn"])
            submit_btn = gr.Button(
                "立即迁移",
                elem_id="submit-btn",
                variant="primary",
            )

        submit_result = gr.Markdown("", elem_classes=["submit-result"])

    return {
        "preview_empty": preview_empty,
        "main_preview": main_preview,
        "mask_editor": mask_editor,
        "reupload_btn": reupload_btn,
        "draw_mask_btn": draw_mask_btn,
        "submit_btn": submit_btn,
        "submit_result": submit_result,
    }
