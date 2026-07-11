from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from ucub_mqdraw.utils.id_generator import generate_task_id


class TaskStatus(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    DISPATCHING = "dispatching"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class GenerationTask:
    task_id: str = field(default_factory=generate_task_id)
    status: TaskStatus = TaskStatus.CREATED
    progress: int = 0
    task_type: str = "风格迁移"
    tool: str = "风格迁移"
    compute_type: str = "comfy_api"
    workflow_template: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    description: str = ""
    favorite: bool = False
    input_preview: str = ""
    output_preview: str = ""
    error_message: str = ""
    cost_time: Optional[float] = None
    request_payload: dict = field(default_factory=dict)


@dataclass
class StyleTransferForm:
    base_image_path: Optional[str]
    style_image_path: Optional[str]
    generation_count: str
    style_strength: float
    description: str
    compute_type: str
    workflow_template: str
    tool_name: str


@dataclass
class InpaintForm:
    base_image_path: Optional[str]
    mask_editor_value: Optional[dict[str, Any]]
    denoise_strength: float
    mask_blur_radius: int
    description: str
    compute_type: str
    workflow_template: str
    tool_name: str
