from ucub_mqdraw.constants import TOOL_ITEMS


def render_tool_grid(active_tool: str = "风格迁移") -> str:
    cards = []
    for name in TOOL_ITEMS:
        active_class = " active" if name == active_tool else ""
        cards.append(
            f"""
            <div class="tool-card{active_class}">
                <div class="tool-name">{name}</div>
            </div>
            """
        )

    return f'<div class="tool-grid">{"".join(cards)}</div>'


def tool_notice_text(tool_name: str) -> str:
    notices = {
        "风格迁移": "上传底图和风格参考图，即可生成同风格图片",
        "局部重绘": "上传底图后，在中间预览区点击「画蒙版」圈选重绘区域",
    }
    return notices.get(tool_name, "该工具暂未开放")
