import os
from typing import Optional


def upload_to_oss_placeholder(local_path: Optional[str]) -> Optional[str]:
    """
    OSS 接入点。

    当前阶段只返回模拟 OSS 路径。
    正式阶段这里应上传本地临时文件到 OSS，并返回可访问 URL。

    注意：
    MQ 消息中不传图片二进制，只传 OSS 地址。
    """
    if not local_path:
        return None

    filename = os.path.basename(local_path)
    return f"oss://ucub-img/ref/{filename}"


def upload_mask_to_oss_placeholder(local_path: Optional[str], task_id: str) -> Optional[str]:
    if not local_path:
        return None

    suffix = task_id.replace("task_", "")[-8:]
    return f"oss://ucub-img/mask/mask_{suffix}.png"
