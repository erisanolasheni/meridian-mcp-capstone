# Bootcamp final MCP assessment — reference

Use this file during the timed window to stay aligned with **program requirements**. If the live brief or Google Form conflicts with anything here, **follow the assessors’ instructions**.

## Philosophy (program)

- Showcase technical competence and communication (“soft skills”) as if presenting to a client.
- Deliverables should look **deployment-ready**, not throwaway.
- **No retakes** for this final assessment.
- **Graduation**: both technical and behavioral assessments must succeed.

## Technical MCP assessment — core requirements

| Requirement | Expectation |
|-------------|-------------|
| **MCP** | Use an MCP server **that was previously created as part of your solution** (confirm at kickoff whether this means your own server, a provided endpoint, or both). |
| **Deployment** | Final product **hosted** so reviewers can use it live (not localhost-only). |
| **Submission** | **GitHub** repo + **Google Forms** at stated intervals. |

## Video submissions (program spec)

- **Three videos**, about **2–3 minutes each** (unless the Form specifies otherwise).
- **Video 1**: Scope the **business problem** and state **goals** from the shared requirements (before / as you start building).
- **Videos 2 & 3**: **Reasoning**, **walk through the codebase**, **demonstrate the working product**.
- **Recording**: Your **face** and **screen** visible (code + running app). Clarity beats polish—think teammate check-in.
- **AI tools**: Allowed as in real work; you must **own and explain every part** of the solution—unreviewed “AI slop” is unacceptable.

### Quick checklist per video

1. **Video 1 — Kickoff**: Problem for the business → success criteria → build order → what you will drop if time runs out.
2. **Video 2 — Mid-window**: What works now → key decisions → how you corrected or improved AI-generated code → blockers and mitigations.
3. **Video 3 — Wrap-up**: Short demo on the **hosted** app → thin architecture slice (how MCP + UI + LLM connect) → honest limits + next sprint improvements.

If a separate scenario brief asks for a longer “final pitch” (e.g. to leadership), **still satisfy the bootcamp length/recording rules first**, then extend only if the Form allows.

---

## Scenario addendum (Meridian-style brief — reference only)

These details come from the **customer-support chatbot** scenario you shared for modeling; wire URLs and tools **after** you confirm them against the live MCP during the assessment.

| Item | Value |
|------|--------|
| **MCP URL** | `https://order-mcp-74afyau24q-uc.a.run.app/mcp` (**no** trailing slash — `/mcp/` can redirect via plain HTTP and stall streaming clients) |
| **Transport** | Streamable HTTP |

Discover tools at runtime (for example MCP Inspector or `list_tools` from your integration). Chatbot behavior must follow **whatever tools and schemas** the server exposes.

### Cost / stack reminders (from scenario brief)

- Prefer a **small / flash / mini** tier model so per-conversation cost stays low.
- UI at least **Gradio or Streamlit** (or stronger framework if time permits).
- Minimum deploy target mentioned in scenario: **Hugging Face Spaces** (optional extras: Vercel, GCP, AWS, Azure).

---

## Test customers (fixture data)

Use these **only** for demos and automated tests against the assessment MCP. Treat like shared sandbox credentials—not secrets. The same table is copied in code as [`meridian_chatbot/bootcamp_fixtures.py`](../meridian_chatbot/bootcamp_fixtures.py) for opt-in live checks (`RUN_LIVE_MCP=1`, `tests/live/`).

| Email | PIN |
|-------|-----|
| donaldgarcia@example.net | 7912 |
| michellejames@example.com | 1520 |
| laurahenderson@example.org | 1488 |
| spenceamanda@example.org | 2535 |
| glee@example.net | 4582 |
| williamsthomas@example.net | 4811 |
| justin78@example.net | 9279 |
| jason31@example.com | 1434 |
| samuel81@example.com | 4257 |
| williamleon@example.net | 9928 |

---

## What this repo contains

- [`app.py`](../app.py) and [`meridian_chatbot/`](../meridian_chatbot/) — Gradio customer-support chatbot (OpenAI-compatible tool loop + MCP over streamable HTTP). See root [`README.md`](../README.md) and `requirements-chatbot.txt` / `requirements.txt`.

---

## What not to do during “prep only” phases

Until you deliberately start the build slice of the clock:

- Do **not** implement the full chatbot, CI deploy pipeline, or duplicate Meridian logic ahead of Video 1.
- Do **not** commit API keys or production secrets—use `.env` locally and platform secrets on deploy.

When you begin implementation, grow from this reference + recorded Video 1 plan.
