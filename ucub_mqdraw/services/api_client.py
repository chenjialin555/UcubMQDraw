import requests

from ucub_mqdraw.config import TASK_CREATE_API
from ucub_mqdraw.constants import COMPUTE_TYPES
from ucub_mqdraw.models import InpaintForm, StyleTransferForm
from ucub_mqdraw.utils.image import upload_mask_to_oss_placeholder, upload_to_oss_placeholder
from ucub_mqdraw.utils.mask import mask_path_from_editor


class GenerationApiClient:
    """
    UcubMQDraw FastAPI 接口客户端。

    注意：
    这里不直接调用 imggen。
    这里也不直接投递 RocketMQ。
    Gradio 前端只提交业务任务给 UcubMQDraw 后端。
    """

    def build_style_transfer_payload(self, task_id: str, form: StyleTransferForm) -> dict:
        compute_type = COMPUTE_TYPES.get(form.compute_type, form.compute_type)

        return {
            "taskId": task_id,
            "userId": "op_demo_user",
            "modelName": "SDXL/Flux",
            "prompt": form.description or "风格迁移",
            "negativePrompt": "模糊，水印，低画质",
            "width": 1024,
            "height": 1024,
            "batchSize": int(form.generation_count.replace("张", "")),
            "refImageList": [
                upload_to_oss_placeholder(form.base_image_path),
                upload_to_oss_placeholder(form.style_image_path),
            ],
            "timeout": 300,
            "computeType": compute_type,
            "workflowTemplate": form.workflow_template,
            "workflowJson": "",
            "extra": {
                "tool": form.tool_name,
                "styleStrength": float(form.style_strength),
                "bizScene": "style_transfer",
            },
        }

    def build_inpaint_payload(self, task_id: str, form: InpaintForm) -> dict:
        compute_type = COMPUTE_TYPES.get(form.compute_type, form.compute_type)
        mask_path = mask_path_from_editor(form.mask_editor_value)

        return {
            "taskId": task_id,
            "userId": "op_demo_user",
            "modelName": "SDXL/Flux",
            "prompt": form.description or "局部重绘",
            "negativePrompt": "色差严重、破损、脏污",
            "width": 1024,
            "height": 1024,
            "batchSize": 1,
            "refImageList": [upload_to_oss_placeholder(form.base_image_path)],
            "maskOssUrl": upload_mask_to_oss_placeholder(mask_path, task_id),
            "timeout": 300,
            "computeType": compute_type,
            "workflowTemplate": form.workflow_template,
            "workflowJson": "",
            "extra": {
                "tool": form.tool_name,
                "maskBlurRadius": int(form.mask_blur_radius),
                "denoiseStrength": float(form.denoise_strength),
                "bizScene": "inpaint",
            },
        }

    def submit_style_transfer(self, task_id: str, form: StyleTransferForm) -> dict:
        payload = self.build_style_transfer_payload(task_id, form)
        return self._post_task(payload)

    def submit_inpaint(self, task_id: str, form: InpaintForm) -> dict:
        payload = self.build_inpaint_payload(task_id, form)
        return self._post_task(payload)

    def _post_task(self, payload: dict) -> dict:
        response = requests.post(
            TASK_CREATE_API,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def get_task(self, task_id: str) -> dict:
        response = requests.get(
            f"{TASK_CREATE_API}/{task_id}",
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def retry_task(self, task_id: str) -> dict:
        response = requests.post(
            f"{TASK_CREATE_API}/{task_id}/retry",
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
