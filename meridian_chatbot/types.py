"""Shared typing aliases (OpenAI + UI); avoid ``Any`` in public surfaces."""

from __future__ import annotations

from typing import Literal, TypeAlias, TypedDict

from openai.types.chat import ChatCompletionMessageParam

# OpenAI API uses JSON-Schema-like objects; values are JSON-serializable.
JsonDict: TypeAlias = dict[str, object]

# Full message list we persist for tool-calling (user / assistant / tool).
ChatState: TypeAlias = list[ChatCompletionMessageParam]


class GradioTextMessage(TypedDict):
    role: Literal["user", "assistant"]
    content: str
