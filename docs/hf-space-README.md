---
title: Meridian Support
emoji: 💬
colorFrom: gray
colorTo: blue
sdk: gradio
sdk_version: "6.0.0"
app_file: app.py
pinned: false
---

# Meridian Electronics — Customer support

Gradio chatbot wired to Meridian’s **MCP** (streamable HTTP) and an **OpenAI-compatible** API for tool calling.

## Space secrets

Configure under **Settings → Secrets**:

| Secret | Required | Notes |
|--------|----------|--------|
| `OPENAI_API_KEY` | Yes | Your provider key (OpenAI, OpenRouter, etc.). |
| `LLM_BASE_URL` | No | Override API base URL (e.g. Open Router). |
| `LLM_MODEL` or `OPENAI_MODEL` | No | Model id. |
| `MCP_URL` | No | Defaults to the assessment MCP if unset. Use **`…/mcp`** with **no** trailing slash. |

Demo/test customers (shared sandbox email / PIN pairs) are listed in the GitHub repo under **`docs/bootcamp-mcp-assessment.md`**.

*Application files sync from GitHub (`main`) via CI — see the repo root README.*
