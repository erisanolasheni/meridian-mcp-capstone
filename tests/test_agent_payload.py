from __future__ import annotations

from unittest.mock import MagicMock

from meridian_chatbot.agent import _assistant_payload


def test_assistant_payload_text_only():
    m = MagicMock()
    m.content = "x"
    m.tool_calls = None
    assert _assistant_payload(m) == {"role": "assistant", "content": "x"}


def test_assistant_payload_with_calls():
    tc = MagicMock()
    tc.id = "1"
    tc.function.name = "t"
    tc.function.arguments = "{}"
    m = MagicMock()
    m.content = None
    m.tool_calls = [tc]
    d = _assistant_payload(m)
    assert d["role"] == "assistant"
    assert len(d["tool_calls"]) == 1
    assert d["tool_calls"][0]["function"]["name"] == "t"
