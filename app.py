"""HF Spaces: ``python app.py``; local: same or ``python -m meridian_chatbot.gradio_app``.

Env: OPENAI_API_KEY, optional LLM_BASE_URL / LLM_MODEL / MCP_URL.
"""

import os

from meridian_chatbot.gradio_app import LAUNCH_KWARGS, build_demo

demo = build_demo()

if __name__ == "__main__":
    # Gradio 6 moved theme/css from Blocks() to launch().
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", "7860")),
        **LAUNCH_KWARGS,
    )
