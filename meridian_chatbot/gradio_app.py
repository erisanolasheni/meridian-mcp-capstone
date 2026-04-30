from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator

import gradio as gr
from gradio.themes import GoogleFont

from meridian_chatbot.agent import chat_message
from meridian_chatbot.config import get_settings
from meridian_chatbot.types import ChatState, GradioTextMessage

logger = logging.getLogger(__name__)

# Interim assistant bubble while MCP + LLM run (replaced by the real reply on the next yield).
_TYPING_ASSISTANT_HTML = (
    '<span class="meridian-typing" aria-live="polite" aria-busy="true" '
    'aria-label="Assistant is preparing a response">'
    '<span class="meridian-typing-dot"></span>'
    '<span class="meridian-typing-dot"></span>'
    '<span class="meridian-typing-dot"></span>'
    "</span>"
)

_THEME = gr.themes.Soft(
    primary_hue=gr.themes.colors.slate,
    secondary_hue=gr.themes.colors.sky,
    neutral_hue=gr.themes.colors.stone,
    font=(
        GoogleFont("Inter", weights=(400, 500, 600)),
        "ui-sans-serif",
        "system-ui",
        "sans-serif",
    ),
).set(
    body_background_fill="*neutral_50",
    body_background_fill_dark="*neutral_950",
    shadow_drop="0 2px 8px rgba(15, 23, 42, 0.06)",
    shadow_drop_lg="0 12px 40px rgba(15, 23, 42, 0.08)",
    layout_gap="0.875rem",
    input_radius="14px",
    container_radius="16px",
    block_radius="14px",
    chatbot_text_size="*text_md",
    panel_background_fill="*neutral_50",
    panel_background_fill_dark="*neutral_900",
)

_CSS = """
/* ---- Page chrome (SPA-like canvas) ---- */
body {
  background-image:
    radial-gradient(ellipse 100% 90% at 50% -30%, color-mix(in srgb, var(--color-accent) 18%, transparent), transparent 55%),
    radial-gradient(ellipse 70% 45% at 100% 10%, color-mix(in srgb, var(--color-accent-soft) 25%, transparent), transparent 50%),
    radial-gradient(ellipse 55% 40% at 0% 80%, color-mix(in srgb, var(--border-color-accent-subdued) 35%, transparent), transparent 55%) !important;
  background-color: var(--body-background-fill) !important;
  min-height: 100vh;
}

.meridian-wrap {
  max-width: 920px;
  margin: 0 auto;
  padding: clamp(1rem, 4vw, 2rem) clamp(0.75rem, 3vw, 1.25rem) 2.5rem;
  position: relative;
}

/* Shell border only — chat bubbles stay Gradio-native (no overrides on .bubble) */
.meridian-card {
  border-radius: 20px;
  border: 1px solid var(--border-color-primary);
  background: color-mix(in srgb, var(--background-fill-primary) 92%, transparent);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: var(--shadow-drop-lg);
  overflow: hidden;
}

/* ---- Top app bar ---- */
.meridian-topbar {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 1rem;
  flex-wrap: wrap;
  padding: 1.1rem 1.25rem 1rem;
  border-bottom: 1px solid var(--border-color-primary);
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--background-fill-secondary) 65%, transparent) 0%,
    transparent 100%
  );
}
.meridian-brand {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  min-width: 0;
}
.meridian-logo {
  flex-shrink: 0;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 14px;
  background: linear-gradient(145deg, var(--color-accent) 0%, color-mix(in srgb, var(--color-accent-soft) 75%, var(--color-accent)) 100%);
  box-shadow: 0 4px 14px color-mix(in srgb, var(--color-accent) 35%, transparent);
}
.meridian-brand-text h1 {
  font-size: 1.125rem;
  font-weight: 650;
  letter-spacing: -0.03em;
  margin: 0;
  line-height: 1.25;
  color: var(--body-text-color);
}
.meridian-brand-text p {
  font-size: 0.78rem;
  font-weight: 500;
  margin: 0.2rem 0 0;
  color: var(--body-text-color-subdued);
  letter-spacing: 0.01em;
}
/* ---- Chat surface ---- */
.meridian-chat-section {
  padding: 0;
  background: var(--background-fill-primary);
}
.meridian-chat-wrap {
  border-radius: 0;
  overflow: hidden;
  border-bottom: 1px solid var(--border-color-primary);
  background: linear-gradient(180deg, var(--background-fill-secondary) 0%, var(--background-fill-primary) 18%);
  min-height: min(520px, calc(100vh - 260px));
}
/* Avoid stacking theme block shadow on top of card shadow only */
.meridian-chat-wrap .block,
.meridian-chat-wrap #meridian-chatbot {
  box-shadow: none !important;
}
.meridian-chat-wrap [class*="message-row"],
.meridian-chat-wrap [class*="message"] {
  padding-top: 0.35rem;
  padding-bottom: 0.35rem;
}

/* ---- Composer dock ---- */
.meridian-composer {
  padding: 1rem 1.15rem 1.2rem;
  background: linear-gradient(180deg, var(--background-fill-primary) 0%, var(--background-fill-secondary) 100%);
}
.meridian-input-row {
  align-items: stretch !important;
  gap: 0.65rem !important;
  flex-wrap: nowrap !important;
}
.meridian-input-row textarea,
.meridian-input-row input {
  font-size: 0.9375rem !important;
  line-height: 1.45 !important;
  padding: 0.65rem 1rem !important;
  border-radius: 14px !important;
  transition: box-shadow 0.15s ease !important;
}
.meridian-input-row textarea:focus,
.meridian-input-row input:focus {
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-accent) 28%, transparent) !important;
  outline: none !important;
}
.meridian-input-row button {
  border-radius: 14px !important;
  font-weight: 600 !important;
  letter-spacing: 0.01em !important;
}

/* ---- Typing dots ---- */
.meridian-typing {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  min-height: 1.25em;
}
.meridian-typing-dot {
  display: inline-block;
  width: 0.42em;
  height: 0.42em;
  border-radius: 999px;
  background: var(--body-text-color-subdued);
  animation: meridian-typing-pulse 1.15s ease-in-out infinite;
}
.meridian-typing-dot:nth-child(2) { animation-delay: 0.18s; }
.meridian-typing-dot:nth-child(3) { animation-delay: 0.36s; }
@keyframes meridian-typing-pulse {
  0%, 70%, 100% { transform: translateY(0); opacity: 0.35; }
  35% { transform: translateY(-4px); opacity: 1; }
}
"""


def clear_outputs() -> tuple[list[GradioTextMessage], ChatState, str]:
    return [], [], ""


async def handle_submit(
    text: str,
    hist: list[GradioTextMessage] | None,
    st: ChatState | None,
) -> AsyncGenerator[tuple[list[GradioTextMessage] | None, ChatState | None, object], None]:
    """Yield after the user message so the bubble appears before MCP/LLM finish."""
    text = (text or "").strip()
    if not text:
        yield hist, st, gr.update()
        return

    hist = list(hist or [])
    hist.append(GradioTextMessage(role="user", content=text))
    yield hist, st, gr.update(value="")

    hist.append(GradioTextMessage(role="assistant", content=_TYPING_ASSISTANT_HTML))
    yield hist, st, gr.update(value="")

    try:
        reply, st = await chat_message(text, st or [])
    except Exception as e:
        logger.exception("chat_message")
        hist[-1] = GradioTextMessage(role="assistant", content=f"**Error:** {e!s}")
        yield hist, st or [], gr.update(value="")
        return

    hist[-1] = GradioTextMessage(role="assistant", content=reply)
    yield hist, st, gr.update(value="")


def build_demo() -> gr.Blocks:
    with gr.Blocks(
        title="Meridian Support",
        theme=_THEME,
        css=_CSS,
        fill_height=True,
    ) as demo:
        ctx = gr.State([])

        with gr.Column(elem_classes=["meridian-wrap"]):
            with gr.Column(elem_classes=["meridian-card"]):
                gr.HTML(
                    '<header class="meridian-topbar">'
                    '<div class="meridian-brand">'
                    '<span class="meridian-logo" aria-hidden="true"></span>'
                    '<div class="meridian-brand-text">'
                    "<h1>Meridian Electronics</h1>"
                    "<p>Customer support · Orders &amp; product answers</p>"
                    "</div></div>"
                    "</header>"
                )

                with gr.Column(elem_classes=["meridian-chat-section"], scale=1):
                    with gr.Column(elem_classes=["meridian-chat-wrap"]):
                        chat = gr.Chatbot(
                            elem_id="meridian-chatbot",
                            label="Conversation",
                            show_label=False,
                            height="min(560px, calc(100vh - 240px))",
                            layout="bubble",
                            buttons=["copy"],
                            feedback_options=[],
                            placeholder=(
                                "<p style=\"opacity:0.72;margin:0;font-size:0.95rem;\">"
                                "Ask about products, availability, or your orders.</p>"
                            ),
                            autoscroll=True,
                            resizable=True,
                        )

                with gr.Column(elem_classes=["meridian-composer"]):
                    with gr.Row(elem_classes=["meridian-input-row"]):
                        msg = gr.Textbox(
                            elem_id="meridian-prompt",
                            placeholder="Message Meridian support…",
                            show_label=False,
                            scale=6,
                            container=False,
                            lines=1,
                        )
                        go = gr.Button("Send", variant="primary", scale=1, min_width=104)
                        clear = gr.Button("Clear", variant="secondary", scale=1, min_width=92)

        go.click(
            handle_submit,
            [msg, chat, ctx],
            [chat, ctx, msg],
            show_progress="full",
            show_progress_on=chat,
        )
        msg.submit(
            handle_submit,
            [msg, chat, ctx],
            [chat, ctx, msg],
            show_progress="full",
            show_progress_on=chat,
        )
        clear.click(clear_outputs, None, [chat, ctx, msg])

    return demo


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    get_settings()
    demo = build_demo()
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", "7860")))


if __name__ == "__main__":  # pragma: no cover
    main()
