"""Real Meridian MCP + bootcamp fixture emails/PINs (network). Opt-in only."""

from __future__ import annotations

import os

import pytest
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from meridian_chatbot.bootcamp_fixtures import BOOTCAMP_CUSTOMERS
from meridian_chatbot.config import Settings
from meridian_chatbot.http_utils import normalize_streamable_http_url

pytestmark = [pytest.mark.live]

RUN_LIVE_MCP = os.environ.get("RUN_LIVE_MCP", "").strip().lower() in ("1", "true", "yes")


def _settings() -> Settings:
    return Settings()


@pytest.mark.asyncio
@pytest.mark.skipif(not RUN_LIVE_MCP, reason="Set RUN_LIVE_MCP=1 to verify fixtures against real MCP")
async def test_verify_bootcamp_pins_accepted_by_mcp() -> None:
    """Confirms the assessment server accepts PIN verification for every bootcamp row."""
    s = _settings()
    url, _ = normalize_streamable_http_url(s.mcp_url.strip())
    async with streamablehttp_client(
        url,
        timeout=s.mcp_timeout,
        sse_read_timeout=s.mcp_sse_read_timeout,
    ) as streams:
        read, write, _ = streams
        async with ClientSession(read, write) as session:
            await session.initialize()
            for email, pin in BOOTCAMP_CUSTOMERS:
                result = await session.call_tool(
                    "verify_customer_pin",
                    {"email": email, "pin": pin},
                )
                assert not result.isError, (
                    f"verify_customer_pin failed for {email}: "
                    f"{result.content!r} sc={result.structuredContent}"
                )


@pytest.mark.asyncio
@pytest.mark.skipif(not RUN_LIVE_MCP, reason="Set RUN_LIVE_MCP=1")
async def test_readonly_catalog_tools_respond() -> None:
    """Smoke: search_products runs (same catalog surface the chatbot uses)."""
    s = _settings()
    url, _ = normalize_streamable_http_url(s.mcp_url.strip())
    async with streamablehttp_client(
        url,
        timeout=s.mcp_timeout,
        sse_read_timeout=s.mcp_sse_read_timeout,
    ) as streams:
        read, write, _ = streams
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            names = {t.name for t in listed.tools}
            assert "search_products" in names
            r = await session.call_tool("search_products", {"query": "keyboard"})
            assert not r.isError, f"search_products: {r!r}"


@pytest.mark.asyncio
@pytest.mark.skipif(
    not (RUN_LIVE_MCP and os.environ.get("OPENAI_API_KEY", "").strip()),
    reason="Set RUN_LIVE_MCP=1 and OPENAI_API_KEY for one real agent turn",
)
async def test_agent_turn_with_fixture_user_prompt() -> None:
    """One real LLM+MCP turn using bootcamp wording (costs one completion)."""
    from pydantic import SecretStr

    from meridian_chatbot.agent import run_turn
    from meridian_chatbot.config import get_settings

    email, pin = BOOTCAMP_CUSTOMERS[0]
    get_settings.cache_clear()
    settings = Settings(openai_api_key=SecretStr(os.environ["OPENAI_API_KEY"]))
    msg = f"Verify my account {email} with PIN {pin} and say if it worked."
    reply, state = await run_turn(settings, [], user=msg)
    assert len(reply) > 0
    assert len(state) >= 2
    get_settings.cache_clear()
