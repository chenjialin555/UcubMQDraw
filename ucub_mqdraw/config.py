import os

from dotenv import load_dotenv

load_dotenv()

BACKEND_HTTP_BASE = os.getenv("UCUB_MQDRAW_HTTP_BASE", "http://127.0.0.1:8000")
BACKEND_WS_URL = os.getenv(
    "UCUB_MQDRAW_WS_URL",
    "ws://127.0.0.1:8000/api/v1/images/generations/tasks/ws",
)

TASK_CREATE_API = f"{BACKEND_HTTP_BASE}/api/v1/images/generations/tasks"

USE_MOCK = os.getenv("UCUB_MQDRAW_USE_MOCK", "true").lower() in {"1", "true", "yes"}

GRADIO_SERVER_NAME = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0")
GRADIO_SERVER_PORT = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
