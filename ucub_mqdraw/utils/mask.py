from typing import Any, Optional


def mask_path_from_editor(editor_value: Optional[dict[str, Any]]) -> Optional[str]:
    """
    从 ImageEditor 返回值中提取蒙版本地路径。
    优先 composite，其次取最后一层绘制图层。
    """
    if not editor_value:
        return None

    composite = editor_value.get("composite")
    if isinstance(composite, str) and composite:
        return composite

    layers = editor_value.get("layers") or []
    for layer in reversed(layers):
        if isinstance(layer, str) and layer:
            return layer

    return None
