from meridian_chatbot.http_utils import normalize_streamable_http_url


def test_strips_trailing_slash_and_warns() -> None:
    url, warns = normalize_streamable_http_url("https://example.com/mcp/")
    assert url == "https://example.com/mcp"
    assert any("trailing" in w.lower() for w in warns)


def test_preserves_query_string() -> None:
    url, _ = normalize_streamable_http_url("https://example.com/mcp?foo=1")
    assert url == "https://example.com/mcp?foo=1"
