import json

from unittest.mock import MagicMock

from mcp import types as mcp_types

from meridian_chatbot.mcp_tooling import mcp_tools_to_openai_functions, tool_result_to_text


def test_tool_result_prefers_structured_content() -> None:
    res = mcp_types.CallToolResult(
        content=[],
        structuredContent={"ok": True, "sku": "ABC"},
        isError=False,
    )
    assert '"sku"' in tool_result_to_text(res)


def test_tool_result_text_from_blocks() -> None:
    res = mcp_types.CallToolResult(
        content=[mcp_types.TextContent(type="text", text="hello")],
        structuredContent=None,
        isError=False,
    )
    assert tool_result_to_text(res) == "hello"


def test_mcp_tools_to_openai_functions_shape() -> None:
    tools = [
        mcp_types.Tool(
            name="demo_tool",
            description="Demo",
            inputSchema={
                "type": "object",
                "properties": {"x": {"type": "integer"}},
                "required": ["x"],
            },
        )
    ]
    oai = mcp_tools_to_openai_functions(tools)
    assert len(oai) == 1
    assert oai[0]["type"] == "function"
    assert oai[0]["function"]["name"] == "demo_tool"
    params = oai[0]["function"]["parameters"]
    assert params["type"] == "object"
    assert "x" in params["properties"]


def test_sanitize_drops_dollar_keys() -> None:
    tools = [
        mcp_types.Tool(
            name="t",
            description="",
            inputSchema={"type": "object", "$schema": "https://json-schema.org/draft/2020-12/schema"},
        )
    ]
    oai = mcp_tools_to_openai_functions(tools)
    dumped = json.dumps(oai[0]["function"]["parameters"])
    assert "$schema" not in dumped


def test_clean_schema_non_object_root() -> None:
    tools = [
        mcp_types.Tool(name="t", description="", inputSchema={"type": "string"}),
    ]
    params = mcp_tools_to_openai_functions(tools)[0]["function"]["parameters"]
    assert params == {"type": "object", "properties": {}}


def test_tool_result_error_empty() -> None:
    res = mcp_types.CallToolResult(content=[], structuredContent=None, isError=True)
    assert tool_result_to_text(res) == "Tool error."


def test_blocks_image_audio_resource_embedded() -> None:
    img = mcp_types.ImageContent(type="image", data="x", mimeType="image/png")
    aud = mcp_types.AudioContent(type="audio", data="y", mimeType="audio/wav")
    link = mcp_types.ResourceLink(type="resource_link", uri="http://u.test", name="n")
    emb = mcp_types.EmbeddedResource(
        type="resource",
        resource=mcp_types.TextResourceContents(uri="http://r.test", text="t"),
    )
    raw = mcp_types.CallToolResult(content=[img, aud, link, emb], isError=False)
    out = tool_result_to_text(raw)
    assert "[image/image/png]" in out and "[audio/audio/wav]" in out
    assert "[resource http://u.test" in out  # AnyUrl may normalize trailing slash
    assert "[embedded resource]" in out


def test_unknown_content_block_json_fallback() -> None:
    raw = mcp_types.CallToolResult.model_construct(
        content=[MagicMock()],
        structuredContent=None,
        isError=False,
    )
    out = tool_result_to_text(raw)
    assert len(out) > 0 and "MagicMock" in out
