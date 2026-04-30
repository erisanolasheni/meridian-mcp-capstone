"""HF Spaces: ``demo`` below; local run ``python app.py``. Env: OPENAI_API_KEY, optional LLM_BASE_URL / LLM_MODEL / MCP_URL."""

from meridian_chatbot.gradio_app import build_demo

demo = build_demo()

if __name__ == "__main__":
    from meridian_chatbot.gradio_app import main

    main()
