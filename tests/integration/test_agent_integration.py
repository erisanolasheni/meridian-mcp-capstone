"""Agent loop with MCP + LLM mocked (no network)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp import types as T
from pydantic import SecretStr

from meridian_chatbot.agent import chat_message, run_turn
from meridian_chatbot.config import Settings, get_settings

pytestmark = pytest.mark.integration


def _tool(name: str, schema: dict | None = None) -> T.Tool:
    return T.Tool(
        name=name,
        description=name,
        inputSchema=schema or {"type": "object", "properties": {"q": {"type": "string"}}},
    )


def _cm(mock_enter: AsyncMock, mock_exit: AsyncMock | None = None) -> MagicMock:
    m = MagicMock()
    m.__aenter__ = mock_enter
    m.__aexit__ = mock_exit or AsyncMock(return_value=False)
    return m


def _msg(content: str | None, *, tool_calls: list | None = None) -> MagicMock:
    m = MagicMock()
    m.content = content
    m.tool_calls = tool_calls
    return m


def _choice(msg: MagicMock) -> MagicMock:
    c = MagicMock()
    c.message = msg
    return MagicMock(choices=[c])


def _tc(name: str, args: str, tid: str = "call_1") -> MagicMock:
    tc = MagicMock()
    tc.id = tid
    tc.function.name = name
    tc.function.arguments = args
    return tc


def _patch_stack(session: AsyncMock, completions: AsyncMock):
    stream_cm = _cm(AsyncMock(return_value=(MagicMock(), MagicMock(), None)))
    sess_cm = _cm(AsyncMock(return_value=session))
    oai = MagicMock()
    oai.chat.completions.create = completions
    patches = [
        patch("meridian_chatbot.agent.streamablehttp_client", return_value=stream_cm),
        patch("meridian_chatbot.agent.ClientSession", return_value=sess_cm),
        patch("meridian_chatbot.agent.AsyncOpenAI", return_value=oai),
    ]
    return patches, oai


@pytest.fixture
def base_settings() -> Settings:
    return Settings(
        openai_api_key=SecretStr("sk-test"),
        mcp_url="https://example.com/mcp",
        max_tool_rounds=12,
        history_max_messages=40,
    )


@pytest.mark.asyncio
async def test_openrouter_base_url_on_client(base_settings: Settings):
    base_settings = base_settings.model_copy(update={"llm_base_url": "https://openrouter.ai/api/v1"})
    session = AsyncMock()
    session.initialize = AsyncMock()
    session.list_tools = AsyncMock(return_value=T.ListToolsResult(tools=[_tool("search_products")]))
    session.call_tool = AsyncMock()
    comp = AsyncMock(return_value=_choice(_msg("hi")))
    patches, _ = _patch_stack(session, comp)
    with patches[0], patches[1]:
        with patches[2] as mock_llm_ctor:
            await run_turn(base_settings, [], user="x")
    mock_llm_ctor.assert_called_once_with(api_key="sk-test", base_url="https://openrouter.ai/api/v1")


@pytest.mark.asyncio
async def test_reply_without_tools(base_settings: Settings):
    session = AsyncMock()
    session.initialize = AsyncMock()
    session.list_tools = AsyncMock(return_value=T.ListToolsResult(tools=[_tool("search_products")]))
    session.call_tool = AsyncMock()
    msg = _msg("Stock looks good.")
    comp = AsyncMock(return_value=_choice(msg))
    patches, _ = _patch_stack(session, comp)
    with patches[0], patches[1], patches[2]:
        text, out = await run_turn(base_settings, [], user="Which monitors?")
    assert text == "Stock looks good."
    assert out[-1]["role"] == "assistant"
    session.call_tool.assert_not_called()
    comp.assert_awaited_once()


@pytest.mark.asyncio
async def test_tool_round_then_text(base_settings: Settings):
    session = AsyncMock()
    session.initialize = AsyncMock()
    session.list_tools = AsyncMock(return_value=T.ListToolsResult(tools=[_tool("search_products")]))
    session.call_tool = AsyncMock(
        return_value=T.CallToolResult(
            content=[T.TextContent(type="text", text='[{"sku":"M1"}]')],
            isError=False,
        )
    )
    m1 = _msg(None, tool_calls=[_tc("search_products", '{"q":"mouse"}')])
    m2 = _msg("Found one SKU.")
    comp = AsyncMock(side_effect=[_choice(m1), _choice(m2)])
    patches, _ = _patch_stack(session, comp)
    with patches[0], patches[1], patches[2]:
        text, out = await run_turn(base_settings, [], user="Find a mouse")
    assert text == "Found one SKU."
    session.call_tool.assert_awaited_once_with("search_products", {"q": "mouse"})
    assert comp.await_count == 2


@pytest.mark.asyncio
async def test_bad_tool_arguments_json(base_settings: Settings):
    session = AsyncMock()
    session.initialize = AsyncMock()
    session.list_tools = AsyncMock(return_value=T.ListToolsResult(tools=[_tool("search_products")]))
    session.call_tool = AsyncMock()
    m1 = _msg(None, tool_calls=[_tc("search_products", "NOT_JSON")])
    m2 = _msg("Could not run that.")
    comp = AsyncMock(side_effect=[_choice(m1), _choice(m2)])
    patches, _ = _patch_stack(session, comp)
    with patches[0], patches[1], patches[2]:
        text, _ = await run_turn(base_settings, [], user="Search")
    session.call_tool.assert_not_called()
    assert text == "Could not run that."


@pytest.mark.asyncio
async def test_call_tool_exception(base_settings: Settings):
    session = AsyncMock()
    session.initialize = AsyncMock()
    session.list_tools = AsyncMock(return_value=T.ListToolsResult(tools=[_tool("search_products")]))
    session.call_tool = AsyncMock(side_effect=RuntimeError("boom"))
    m1 = _msg(None, tool_calls=[_tc("search_products", "{}")])
    m2 = _msg("Handled.")
    comp = AsyncMock(side_effect=[_choice(m1), _choice(m2)])
    patches, _ = _patch_stack(session, comp)
    with patches[0], patches[1], patches[2]:
        text, _ = await run_turn(base_settings, [], user="Go")
    assert text == "Handled."
    assert session.call_tool.await_count == 1


@pytest.mark.asyncio
async def test_max_tool_rounds_triggers_fallback(base_settings: Settings):
    base_settings = base_settings.model_copy(update={"max_tool_rounds": 2})
    session = AsyncMock()
    session.initialize = AsyncMock()
    session.list_tools = AsyncMock(return_value=T.ListToolsResult(tools=[_tool("t")]))
    session.call_tool = AsyncMock(
        return_value=T.CallToolResult(content=[T.TextContent(type="text", text="ok")], isError=False)
    )
    m = _msg(None, tool_calls=[_tc("t", "{}", tid="a")])
    comp = AsyncMock(side_effect=[_choice(m), _choice(m)])
    patches, _ = _patch_stack(session, comp)
    with patches[0], patches[1], patches[2]:
        text, out = await run_turn(base_settings, [], user="loop")
    assert "Too many tool steps" in text
    assert out[-1]["content"] == text


@pytest.mark.asyncio
async def test_history_tail_trim(base_settings: Settings):
    base_settings = base_settings.model_copy(update={"history_max_messages": 2})
    long_hist = [
        {"role": "user", "content": "a"},
        {"role": "assistant", "content": "b"},
        {"role": "user", "content": "c"},
        {"role": "assistant", "content": "d"},
    ]
    session = AsyncMock()
    session.initialize = AsyncMock()
    session.list_tools = AsyncMock(return_value=T.ListToolsResult(tools=[_tool("noop")]))
    msg = _msg("ok")
    comp = AsyncMock(return_value=_choice(msg))
    patches, _ = _patch_stack(session, comp)
    with patches[0], patches[1], patches[2]:
        _, out = await run_turn(base_settings, long_hist, user="e")
    # tail = last 2 history msgs + user + assistant reply
    assert out[0]["content"] == "c"
    assert out[1]["content"] == "d"
    assert out[2]["role"] == "user" and out[2]["content"] == "e"


def test_missing_api_key(base_settings: Settings):
    bad = base_settings.model_copy(update={"openai_api_key": None})
    import asyncio

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        asyncio.run(run_turn(bad, [], user="x"))


@pytest.mark.asyncio
async def test_chat_message_through_settings(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")
    get_settings.cache_clear()
    session = AsyncMock()
    session.initialize = AsyncMock()
    session.list_tools = AsyncMock(return_value=T.ListToolsResult(tools=[_tool("x")]))
    session.call_tool = AsyncMock()
    comp = AsyncMock(return_value=_choice(_msg("via env")))
    patches, _ = _patch_stack(session, comp)
    with patches[0], patches[1], patches[2]:
        text, st = await chat_message("hi", None)
    assert text == "via env"
    assert st[-1]["role"] == "assistant"
    get_settings.cache_clear()
