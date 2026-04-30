from __future__ import annotations

from unittest.mock import MagicMock, patch

from meridian_chatbot.gradio_app import LAUNCH_KWARGS, clear_outputs


def test_clear_outputs():
    assert clear_outputs() == ([], [], "")


@patch("meridian_chatbot.gradio_app.build_demo")
@patch("meridian_chatbot.gradio_app.get_settings")
def test_main_launches(mock_gs: MagicMock, mock_bd: MagicMock):
    import os

    from meridian_chatbot import gradio_app as ga

    demo = MagicMock()
    mock_bd.return_value = demo
    with patch.dict(os.environ, {"PORT": "8123"}, clear=False):
        ga.main()
    demo.launch.assert_called_once_with(
        server_name="0.0.0.0", server_port=8123, **LAUNCH_KWARGS
    )

