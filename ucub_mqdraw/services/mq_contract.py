"""
RocketMQ 消息契约说明。

注意：
当前 Gradio 前端不直接操作 MQ。
正式 MQ 生产和消费逻辑应放在 UcubMQDraw FastAPI 后端。

Topic:
- ucub_imggen_api_task: imggen-ComfyUI-API 并发版任务队列
- ucub_imggen_gpt_task: imggen-ComfyUI-GPT 串行版任务队列
- ucub_imggen_callback: imggen 统一回调队列

前置约束：
两条下发消息仅存算力执行参数，用户归属、权限、任务统计由 UcubMQDraw
业务中台靠 innerTaskId 映射管理；imggen 不解析任何业务属性。
"""

IMGGEN_API_TASK_TOPIC = "ucub_imggen_api_task"
IMGGEN_GPT_TASK_TOPIC = "ucub_imggen_gpt_task"
IMGGEN_CALLBACK_TOPIC = "ucub_imggen_callback"


def build_style_transfer_mq_message(
    inner_task_id: str,
    model_name: str,
    prompt: str,
    negative_prompt: str,
    width: int,
    height: int,
    batch_size: int,
    ref_image_list: list[str],
    timeout: int,
    workflow_json: str,
    style_strength: float,
    compute_type: str,
) -> dict:
    """
    风格迁移任务 MQ 消息（ucub_imggen_api_task / ucub_imggen_gpt_task 通用）。

    ref_image_list: 第 1 项=基底原图，第 2 项=风格参考图。
    """
    return {
        "innerTaskId": inner_task_id,
        "modelName": model_name,
        "prompt": prompt,
        "negativePrompt": negative_prompt,
        "width": width,
        "height": height,
        "batchSize": batch_size,
        "refImageList": ref_image_list,
        "timeout": timeout,
        "workflowJson": workflow_json,
        "styleStrength": style_strength,
        "computeType": compute_type,
    }


def build_inpaint_mq_message(
    inner_task_id: str,
    model_name: str,
    prompt: str,
    negative_prompt: str,
    width: int,
    height: int,
    batch_size: int,
    ref_image_list: list[str],
    mask_oss_url: str,
    timeout: int,
    workflow_json: str,
    mask_blur_radius: int,
    denoise_strength: float,
    compute_type: str,
) -> dict:
    """
    局部重绘任务 MQ 消息。

    ref_image_list: 仅填入待编辑基底原图。
    mask_oss_url: 前端画笔圈选后上传 OSS 的蒙版地址。
    """
    return {
        "innerTaskId": inner_task_id,
        "modelName": model_name,
        "prompt": prompt,
        "negativePrompt": negative_prompt,
        "width": width,
        "height": height,
        "batchSize": batch_size,
        "refImageList": ref_image_list,
        "maskOssUrl": mask_oss_url,
        "timeout": timeout,
        "workflowJson": workflow_json,
        "maskBlurRadius": mask_blur_radius,
        "denoiseStrength": denoise_strength,
        "computeType": compute_type,
    }


def build_imggen_callback_message(
    inner_task_id: str,
    status: str,
    cost_time: float,
    image_url_list: list[str],
    error_msg: str = "",
) -> dict:
    """imggen 统一回调消息（ucub_imggen_callback，两类任务共用）。"""
    return {
        "innerTaskId": inner_task_id,
        "status": status,
        "costTime": cost_time,
        "imageUrlList": image_url_list,
        "errorMsg": error_msg,
    }


# 兼容旧引用
def build_imggen_task_message(
    inner_task_id: str,
    model_name: str,
    prompt: str,
    negative_prompt: str,
    width: int,
    height: int,
    batch_size: int,
    ref_image_list: list[str],
    timeout: int,
    workflow_json: str,
) -> dict:
    return build_style_transfer_mq_message(
        inner_task_id=inner_task_id,
        model_name=model_name,
        prompt=prompt,
        negative_prompt=negative_prompt,
        width=width,
        height=height,
        batch_size=batch_size,
        ref_image_list=ref_image_list,
        timeout=timeout,
        workflow_json=workflow_json,
        style_strength=0.75,
        compute_type="comfy_api",
    )
