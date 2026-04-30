from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from meridian_chatbot.gradio_app import handle_submit


async def _final(gen: AsyncGenerator[tuple[Any, Any, Any], None]) -> tuple[Any, Any, Any]:
    last: tuple[Any, Any, Any] | None = None
    async for row in gen:
        last = row
    assert last is not None
    return last


@pytest.mark.asyncio
async def test_handle_submit_skips_blank():
    h, s, u = await _final(handle_submit("   ", [{"role": "user", "content": "x"}], []))
    assert h == [{"role": "user", "content": "x"}]
    assert s == []


@pytest.mark.asyncio
@patch("meridian_chatbot.gradio_app.chat_message", new_callable=AsyncMock)
async def test_handle_submit_success(mock_chat: AsyncMock):
    mock_chat.return_value = ("ok", [{"role": "assistant", "content": "ok"}])
    h, st, _ = await _final(handle_submit("hi", None, None))
    assert h == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "ok"},
    ]
    assert st == [{"role": "assistant", "content": "ok"}]
    mock_chat.assert_awaited_once_with("hi", [])


@pytest.mark.asyncio
@patch("meridian_chatbot.gradio_app.chat_message", new_callable=AsyncMock)
async def test_handle_submit_error(mock_chat: AsyncMock):
    mock_chat.side_effect = RuntimeError("fail")
    h, st, _ = await _final(handle_submit("hi", [], []))
    assert len(h) == 2
    assert h[0]["role"] == "user"
    assert "fail" in h[1]["content"]
    assert st == []
