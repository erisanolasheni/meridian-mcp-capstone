"""Smoke tests for UI factory (no browser)."""

from __future__ import annotations

import pytest

from meridian_chatbot.gradio_app import build_demo

pytestmark = pytest.mark.integration


def test_build_demo():
    demo = build_demo()
    assert demo.__class__.__name__ == "Blocks"
