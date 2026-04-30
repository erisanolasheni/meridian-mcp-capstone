from __future__ import annotations

import json
import logging

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat.chat_completion_assistant_message_param import ChatCompletionAssistantMessageParam
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.chat.chat_completion_tool_message_param import ChatCompletionToolMessageParam

from meridian_chatbot.config import Settings, get_settings
from meridian_chatbot.http_utils import normalize_streamable_http_url
from meridian_chatbot.mcp_tooling import mcp_tools_to_openai_functions, tool_result_to_text
from meridian_chatbot.prompts import SYSTEM_PROMPT
from meridian_chatbot.types import ChatState

logger = logging.getLogger(__name__)


def _assistant_payload(msg: ChatCompletionMessage) -> ChatCompletionAssistantMessageParam:
    if not msg.tool_calls:
        return {"role": "assistant", "content": msg.content}
    return {
        "role": "assistant",
        "content": msg.content,
        "tool_calls": [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments or "{}"},
            }
            for tc in msg.tool_calls
        ],
    }


async def run_turn(
    settings: Settings,
    msgs: ChatState,
    *,
    user: str,
) -> tuple[str, ChatState]:
    key = settings.openai_api_key
    if not key or not key.get_secret_value().strip():
        raise RuntimeError("OPENAI_API_KEY is not set.")

    cap = settings.history_max_messages
    tail = msgs if len(msgs) <= cap else msgs[-cap:]
    user_msg: ChatCompletionMessageParam = {"role": "user", "content": user}
    working: list[ChatCompletionMessageParam] = [*tail, user_msg]

    mcp_u, _ = normalize_streamable_http_url(settings.mcp_url.strip())
    bu = (settings.llm_base_url or "").strip()
    oai = (
        AsyncOpenAI(api_key=key.get_secret_value(), base_url=bu) if bu else AsyncOpenAI(api_key=key.get_secret_value())
    )

    async with streamablehttp_client(
        mcp_u,
        timeout=settings.mcp_timeout,
        sse_read_timeout=settings.mcp_sse_read_timeout,
    ) as streams:
        read, write, _ = streams
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = mcp_tools_to_openai_functions((await session.list_tools()).tools)

            for _ in range(settings.max_tool_rounds):
                payload: list[ChatCompletionMessageParam] = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *working,
                ]
                resp = await oai.chat.completions.create(
                    model=settings.llm_model,
                    messages=payload,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.2,
                )
                choice = resp.choices[0].message

                if choice.tool_calls:
                    working.append(_assistant_payload(choice))
                    for tc in choice.tool_calls:
                        raw = tc.function.arguments or "{}"
                        try:
                            args: dict[str, object] = json.loads(raw) if raw.strip() else {}
                        except json.JSONDecodeError as e:
                            err: ChatCompletionToolMessageParam = {
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "content": json.dumps({"parse_error": str(e), "raw": raw[:500]}),
                            }
                            working.append(err)
                            continue
                        try:
                            out = tool_result_to_text(await session.call_tool(tc.function.name, args))
                        except Exception as e:
                            logger.exception("call_tool")
                            out = json.dumps({"error": str(e), "tool": tc.function.name})
                        tool_row: ChatCompletionToolMessageParam = {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": out,
                        }
                        working.append(tool_row)
                    continue

                text = (choice.content or "").strip()
                working.append({"role": "assistant", "content": text})
                return text, working

            fallback = "Too many tool steps in one reply—try a narrower question."
            working.append({"role": "assistant", "content": fallback})
            return fallback, working


async def chat_message(user_text: str, state: ChatState | None) -> tuple[str, ChatState]:
    s = get_settings()
    st: ChatState = list(state or [])
    return await run_turn(s, st, user=user_text.strip())
