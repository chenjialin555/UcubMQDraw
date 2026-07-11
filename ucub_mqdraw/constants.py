TOOL_ITEMS = [
    "风格迁移",
    "局部重绘",
]

TOOL_CHOICES = TOOL_ITEMS

COMPUTE_TYPES = {
    "comfy_api并发版": "comfy_api",
    "comfy_gpt串行版": "comfy_gpt",
}

# 功能与工作流一一绑定，仅后端使用，不对用户暴露
TOOL_WORKFLOW_MAP = {
    "风格迁移": "style_transfer_v1.json",
    "局部重绘": "inpaint_v1.json",
}

TASK_FILTERS = ["全部", "进行中", "已完成", "收藏"]

COUNT_CHOICES = ["1张", "2张", "4张", "8张"]


def workflow_for_tool(tool_name: str) -> str:
    return TOOL_WORKFLOW_MAP[tool_name]
