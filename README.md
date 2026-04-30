# Meridian MCP capstone

Gradio chatbot + OpenAI-compatible tool loop + Meridian MCP (streamable HTTP).

**Source:** [github.com/erisanolasheni/meridian-mcp-capstone](https://github.com/erisanolasheni/meridian-mcp-capstone) — SSH clone: `git@github.com:erisanolasheni/meridian-mcp-capstone.git`

## Run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-chatbot.txt
cp .env.example .env
python app.py
```

HF Space: secrets `OPENAI_API_KEY`, optionally `LLM_BASE_URL`, `LLM_MODEL`, `MCP_URL`. Entry: `app.py` → `demo`.

Spaces install dependencies from **`requirements.txt`** at the repo root (it includes **`requirements-chatbot.txt`**).

### Deploy from GitHub Actions → Hugging Face

1. On [Hugging Face](https://huggingface.co/new-space), create a **Space** (SDK **Gradio**). Note the repo id: `YOUR_USER/YOUR_SPACE`.
2. Create a **fine-grained** or **write** token with access to that Space ([tokens](https://huggingface.co/settings/tokens)).
3. In your GitHub repo: **Settings → Secrets and variables → Actions**
   - **Secret:** `HF_TOKEN` — paste the Hugging Face token.
   - **Variables:** `HF_SPACE_REPO_ID` — e.g. `YOUR_USER/YOUR_SPACE`.
4. Push to **`main`** (or run workflow **Deploy Hugging Face Space** manually). The workflow uploads **`app.py`**, **`meridian_chatbot/`**, requirements, and a Space **`README.md`** built from [`docs/hf-space-README.md`](docs/hf-space-README.md).

Until `HF_TOKEN` and `HF_SPACE_REPO_ID` are set, the deploy workflow **does not run** (so CI stays green).

MCP URL: no trailing slash (`…/mcp`). Test users: `docs/bootcamp-mcp-assessment.md`.

```bash
pip install -r requirements-chatbot-dev.txt
pytest                              # fails under 100% line+branch on meridian_chatbot; HTML → htmlcov/
pytest tests/ -m "not integration"  # skip integration
pytest tests/integration -m integration
```

New code under `meridian_chatbot/` must include tests so coverage stays at **100%** (CI/local matches `pytest.ini`).

**Bootcamp data vs app behavior:** default tests use mocks. To check the **real** MCP accepts the doc’s emails/PINs and that catalog tools match the server (`RUN_LIVE_MCP=1`). For one **real LLM + MCP** turn with fixture wording, set `RUN_LIVE_MCP=1` and `OPENAI_API_KEY` (see `tests/live/test_mcp_bootcamp_data.py`). Fixture list is also in `meridian_chatbot/bootcamp_fixtures.py` (keep aligned with `docs/bootcamp-mcp-assessment.md`).
