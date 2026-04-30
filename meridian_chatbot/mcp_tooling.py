from __future__ import annotations

import json

from mcp import types as T
from openai.types.chat import ChatCompletionFunctionToolParam
from openai.types.shared_params import FunctionDefinition

from meridian_chatbot.types import JsonDict


def tool_result_to_text(result: T.CallToolResult) -> str:
    if result.structuredContent is not None:
        return json.dumps(result.structuredContent, default=str, indent=2)
    parts = [_block(b) for b in result.content]
    body = "\n".join(parts) if parts else ""
    if result.isError:
        return f"Tool error: {body}" if body else "Tool error."
    return body or "{}"


def _block(b: T.ContentBlock) -> str:
    if isinstance(b, T.TextContent):
        return b.text
    if isinstance(b, T.ImageContent):
        return f"[image/{b.mimeType}]"
    if isinstance(b, T.AudioContent):
        return f"[audio/{b.mimeType}]"
    if isinstance(b, T.ResourceLink):
        return f"[resource {b.uri}]"
    if isinstance(b, T.EmbeddedResource):
        return f"[embedded {b.type}]"
    return json.dumps(b.model_dump(), default=str)


def mcp_tools_to_openai_functions(tools: list[T.Tool]) -> list[ChatCompletionFunctionToolParam]:
    out: list[ChatCompletionFunctionToolParam] = []
    for t in tools:
        schema: JsonDict = t.inputSchema if t.inputSchema else {}
        params: JsonDict = _clean_schema(schema) if schema else {"type": "object", "properties": {}}
        desc = ((t.description or "").strip() or f"`{t.name}`")[:8000]
        fn: FunctionDefinition = {"name": t.name, "description": desc, "parameters": params}
        out.append({"type": "function", "function": fn})
    return out


def _clean_schema(schema: JsonDict) -> JsonDict:
    raw: dict[str, object] = json.loads(json.dumps(schema))
    for k in list(raw.keys()):
        if k.startswith("$") or k in ("exclusiveMinimum", "exclusiveMaximum"):
            del raw[k]
    if raw.get("type") != "object" and "properties" not in raw:
        return {"type": "object", "properties": {}}
    return raw
