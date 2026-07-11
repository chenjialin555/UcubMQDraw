import gradio as gr

from ucub_mqdraw.config import GRADIO_SERVER_NAME, GRADIO_SERVER_PORT, USE_MOCK
from ucub_mqdraw.services.websocket_client import start_websocket_listener
from ucub_mqdraw.ui.layout import build_app
from ucub_mqdraw.ui.styles import CUSTOM_CSS


def main():
    if not USE_MOCK:
        start_websocket_listener()

    demo = build_app()

    demo.queue(default_concurrency_limit=20).launch(
        server_name=GRADIO_SERVER_NAME,
        server_port=GRADIO_SERVER_PORT,
        footer_links=[],
        css=CUSTOM_CSS,
        theme=gr.themes.Soft(),
    )


if __name__ == "__main__":
    main()
