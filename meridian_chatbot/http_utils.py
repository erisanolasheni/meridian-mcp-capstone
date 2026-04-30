from __future__ import annotations


def normalize_streamable_http_url(url: str) -> tuple[str, list[str]]:
    u = url.strip()
    warns: list[str] = []
    base, sep, q = u.partition("?")
    if base.endswith("/"):
        base = base.rstrip("/")
        warns.append("Stripped trailing slash on MCP URL (avoids redirect issues on Cloud Run).")
    return base + (sep + q if sep else ""), warns
