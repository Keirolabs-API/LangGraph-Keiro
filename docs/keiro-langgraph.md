# Keiro × LangGraph — Full Documentation

This document is the complete reference for the Keiro × LangGraph integration.
For the quick start, see the root [`README.md`](../README.md).

---

## 1. Overview

**Keiro** is a web-data platform that exposes search, research, extraction, and
Q&A as metered API endpoints (credits per call) plus a set of free API-discovery
endpoints. It is reachable two ways:

- a **REST API** at `https://api.keirolabs.cloud/api/v2/*` (direct HTTP), and
- a **remote MCP server** at `https://kierolabs.space/mcp/api` (Streamable HTTP)
  that surfaces the same capabilities as MCP tools.

**LangGraph** is a framework for building stateful, multi-actor agents. Its
`prebuilt.create_react_agent` produces a ReAct-style agent that reasons, picks a
tool, observes the result, and repeats until it can answer.

**This integration** loads Keiro's MCP tools through
`langchain_mcp_adapters`' `MultiServerMCPClient` and hands them to
`create_react_agent`, so a LangGraph agent can search the web, research a topic,
extract a page, or ask a direct question — without you writing any tool plumbing.

The four data tools deduct Keiro credits per call; the eight discovery/utility
tools are free. All tools are read-only.

---

## 2. Architecture

```text
            your code
               |
               v
   build_keiro_agent(model)
               |   loads tools via MCP
               v
   MultiServerMCPClient  ── streamable_http ──>  Keiro MCP server
   (langchain_mcp_adapters)                       https://kierolabs.space/mcp/api
   get_tools() -> list of BaseTool                       |
   hand tools to create_react_agent                      | proxies to
               |                                         v
               v                                  Keiro v2 REST API
   LangGraph ReAct agent  ── tool calls ──>      https://api.keirolabs.cloud/api/v2/*
   (reason -> act -> observe -> answer)                 |
                                                       v
                                                 credits deducted
```

- The agent never sees Keiro's REST surface directly; it only sees MCP tools.
- Auth is a single `Authorization: Bearer keiro_…` header attached by the MCP
  client to every `tools/list` and `tools/call`. `initialize` needs no auth.
- The LLM (your `model`) decides which tool to call; Keiro executes it and
  returns structured data the agent reads.

---

## 3. The Keiro MCP tools (what the agent calls)

These are the tools `build_keiro_agent` loads. Credit estimates are approximate
because the MCP server may compose underlying v2 calls; see §4 for exact
per-endpoint billing.

### `web_search` — structured web results  · ~1–2 credits
Fast, structured search results. Good first move for factual lookups.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| `query` | string | yes | — | 1–500 chars |
| `maxResults` | integer | no | 20 | max 50 |
| `country` | string | no | — | ISO country code, e.g. `US` |
| `language` | string | no | — | ISO language code, e.g. `en` |

### `web_research` — deep multi-source research + synthesis  · ~3–5 credits
Searches the web and pulls clean page text from the top results in one call.
Best for RAG, summarization, and research agents.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| `query` | string | yes | — | 1–500 chars |
| `maxResults` | integer | no | 3 | pages to scrape, max 5 |
| `mode` | string | no | `ai` | `ai` \| `deep` \| `medium` \| `light` (extraction depth) |
| `json_schema` | object | no | — | structured-extraction schema |
| `objective` | string | no | — | natural-language extraction goal |
| `max_chars` | integer | no | 7000 | per-source cap (1000–50000) |
| `noCache` | boolean | no | false | bypass cache for fresh results |

### `extract_url` — structured extraction from a URL  · ~1–3 credits
Pulls clean, parsed content from a specific URL. Supports JSON-schema
extraction.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| `url` | string | yes | — | URL to extract from |
| `mode` | string | no | `light` | `ai` \| `deep` \| `medium` \| `light` |
| `json_schema` | object | no | — | structured-extraction schema (medium/deep only) |
| `objective` | string | no | — | what to extract |
| `includeMedia` | boolean | no | false | include images |
| `expand_content` | boolean | no | false | return full page, not excerpt |
| `max_chars` | integer | no | 7000 | 1000–50000 |

### `answer` — direct Q&A with web search + AI synthesis  · ~5 credits
One-shot: searches the web and synthesizes a cited answer. Returns a concise
sourced response.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| `query` | string | yes | — | the question |

### Free discovery / utility tools  · 0 credits

| Tool | Purpose |
|------|---------|
| `list_endpoints` | list all Keiro v2 endpoints with summaries |
| `get_endpoint` | full details for one endpoint (params, credits, rate limits) |
| `get_rate_limits` | per-tier rate limits for every endpoint |
| `get_auth` | auth methods, header format, error codes |
| `generate_code` | ready-to-use cURL / Python / JS snippets for an endpoint |
| `get_mcp_tools` | list the available MCP tools (this surface) |
| `suggest_schema` | suggest a JSON schema for `extract_url` from a description or template |
| `check_credits` | credit cost per endpoint and current tier pricing |

The agent can call these to introspect Keiro at runtime — e.g. ask it "how many
credits does web_research cost and what's my rate limit?" and it will use
`get_endpoint` / `get_rate_limits`.

---

## 4. The underlying Keiro v2 REST endpoints

The MCP tools proxy to these. Credits are billed here. Prices below are **full
price**; paid tiers get 50% off during public beta (enterprise = custom).

| ID | Name | Path | Credits (full / discounted) | Latency |
|----|------|------|----------------------------|---------|
| `v2-fast` | Fast | `POST /api/v2/search/fast` | 1 / 0.5 per query | ~1 s |
| `v2-search-content` | Search + Content | `POST /api/v2/search/content` | 3 / 1.5 per query | ~3 s |
| `v2-data` | Data | `POST /api/v2/data` | 2 / 1 per query | ~2 s |
| `v2-batch` | Batch | `POST /api/v2/search/batch` | 1 / 0.5 per query | async (poll) |

### `v2-fast` — always-fresh multi-engine search
First-result-wins search over Keiro's proxy network, ~1 s. Stays reliable under
load.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| `query` | string | yes | — | 1–500 chars |
| `maxResults` | integer | no | 20 | max 50 |
| `mode` | string | no | `ai` | `ai` \| `deep` \| `medium` \| `light` |
| `noCache` | boolean | no | false | bypass cache |
| `includeMedia` | boolean | no | false | include images |

### `v2-search-content` — search + clean page text in one call
Searches and scrapes top results. Ideal for RAG / research agents.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| `query` | string | yes | — | 1–500 chars |
| `maxResults` | integer | no | 3 | pages, max 5 |
| `mode` | string | no | `ai` | `ai` \| `deep` \| `medium` \| `light` |
| `noCache` | boolean | no | false | bypass cache |
| `includeMedia` | boolean | no | false | include images |
| `embeddings.enabled` | boolean | no | false | generate vector embeddings per chunk |
| `embeddings.dimensions` | integer | no | 768 | 384 \| 512 \| 768 \| 1024 (Matryoshka) |
| `embeddings.chunkSize` | integer | no | 500 | chars per chunk, 100–2000 |

### `v2-data` — structured extraction from any URL
Clean, parsed content from one or many URLs. **Gated on the Free tier** (needs
Starter+).

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| `url` | string | no | — | single URL |
| `urls` | array | no | — | many URLs |
| `query` | string | no | — | search alternative to url/urls |

### `v2-batch` — thousands of queries, processed async
Submit a job, poll `GET /api/v2/search/batch/:id` for results. Jobs expire after
1 hour. Automatic retries on Keiro's infrastructure. **Gated on Free.**

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| `queries` | array | yes | — | 1–10,000 queries, each 1–500 chars |
| `maxResults` | integer | no | 10 | per query, max 50 |

---

## 5. Authentication

Keiro v2 uses **only** the `Authorization: Bearer <token>` header. (The legacy
v1 API put `apiKey` in the body — do not mix the two.)

Two token types:

| Type | Format | Source | Expires? |
|------|--------|--------|----------|
| API key | `keiro_<opaque>` | Keiro dashboard → API Keys | No (opaque, rotate manually) |
| JWT | `eyJ…` | OAuth login (Google/GitHub) | Yes (`iat`/`exp` claims) |

This integration uses an **API key**. Provide it via the `KEIRO_API_KEY`
environment variable (loaded from `.env` by `run.sh`, or prompted by `setup.sh`).

The server config in `keiro_langgraph.py` builds the header:

```python
{"Authorization": f"Bearer {key}"}
```

`initialize` (the MCP handshake) runs without auth; every `tools/list` and
`tools/call` requires the header.

### Error codes

| Status | Code | Meaning |
|--------|------|---------|
| 401 | `MISSING_AUTH` | no `Authorization: Bearer` header |
| 401 | `INVALID_API_KEY` | bad key |
| 401 | `INVALID_TOKEN` | invalid/expired JWT |

### Best practices
- Always HTTPS. Never send keys over plain HTTP.
- Store the key in an env var (`KEIRO_API_KEY`), never hardcode it.
- Rotate keys from the dashboard regularly.
- `keiro_` keys do not expire; JWTs do — refresh them if you switch to JWT auth.

---

## 6. Tiers & credits

| Tier | Min credits | Notes |
|------|-------------|-------|
| Free | 0 | `v2-data` and `v2-batch` gated; full-price credits |
| Starter | 1,000 | all endpoints; 50% beta discount |
| Pro | 15,000 | all endpoints; 50% beta discount |
| Startup | 50,000 | all endpoints; 50% beta discount |
| Enterprise | custom | custom pricing & limits |

During public beta, paid tiers get **50% off** every call. Credit costs per
endpoint per tier (from `check_credits` / `get_endpoint`):

| Endpoint | Free | Starter | Pro | Startup | Enterprise |
|----------|------|---------|-----|---------|------------|
| `v2-fast` | 1 | 0.5 | 0.5 | 0.5 | 0.5 |
| `v2-search-content` | 3 | 1.5 | 1.5 | 1.5 | 1.5 |
| `v2-data` | 2 (gated) | 1 | 1 | 1 | 1 |
| `v2-batch` | 1 (gated) | 0.5 | 0.5 | 0.5 | 0.5 |

---

## 7. Rate limits

`null` / `gated` = not available on that tier. Batch submit limits are **per
hour**; everything else is **per minute**.

| Endpoint | Free | Starter | Pro | Startup | Enterprise |
|----------|------|---------|-----|---------|------------|
| `v2-fast` | 10/min | 50/min | 150/min | 300/min | 1000/min |
| `v2-search-content` | 5/min | 25/min | 75/min | 150/min | 500/min |
| `v2-data` | gated | 10/min | 20/min | 40/min | 120/min |
| `v2-batch` (submit) | gated | 5/hour | 12/hour | 25/hour | 200/hour |
| `v2-batch` (poll) | gated | 50/min | 125/min | 250/min | 1000/min |

The agent calls tools on demand, so under heavy use keep these in mind —
especially on the Free tier, where `v2-fast` is ~1 req / 6 s.

---

## 8. Install & setup (one command)

```bash
./setup.sh
```

What it does, in order:

1. Creates a `.venv` (reuses it if present) with `${PYTHON:-python3}`.
2. Upgrades pip, then installs `langgraph langchain-mcp-adapters langchain-openai`.
3. Copies `.env.example` → `.env` if `.env` doesn't exist.
4. Prompts for `KEIRO_API_KEY` and `OPENAI_API_KEY` **only if missing or blank**,
   writing them into `.env`.
5. Runs the no-network self-check (`keiro_langgraph.py check`) — asserts the
   config and auth-header logic, makes zero HTTP calls, needs no deps.

Re-running `./setup.sh` is idempotent: it won't clobber existing keys.

### Prerequisites
- Python 3.10+
- A Keiro API key (`keiro_…`) from the [Keiro dashboard](https://kierolabs.space) → API Keys
- An OpenAI API key for the ReAct agent's LLM

---

## 9. Running the agent

### Via the helper (loads `.env` for you)
```bash
./run.sh "What changed in the EU AI Act this month?"
```

### Directly
```bash
source .venv/bin/activate
export KEIRO_API_KEY=keiro_... OPENAI_API_KEY=sk-...
python keiro-integration/keiro_langgraph.py "latest news on X"
```

### Just the self-check (no network, no deps)
```bash
python keiro-integration/keiro_langgraph.py check
```

`keiro_langgraph.py` CLI:
- `check` — run `_self_check()` (config + auth-header assertions).
- any other args — joined into one query and run through `demo()` (loads tools,
  builds an OpenAI-backed ReAct agent, prints the final answer).
- no args — defaults to `check`.

Each call to a paid tool costs Keiro credits plus your LLM spend.

---

## 10. Using the integration in your own graph

### Default agent (all Keiro tools)
```python
import asyncio
from langchain_openai import ChatOpenAI
from keiro_langgraph import build_keiro_agent  # put keiro-integration/ on sys.path

async def main():
    agent = await build_keiro_agent(ChatOpenAI(model="gpt-4o-mini"))
    r = await agent.ainvoke({"messages": [{"role": "user", "content": "latest news on X"}]})
    print(r["messages"][-1].content)

asyncio.run(main())
```

### Pick a subset of tools
```python
from keiro_langgraph import build_keiro_client

async def main():
    client = await build_keiro_client()
    tools = await client.get_tools()
    wanted = {"web_search", "answer"}            # only the cheap ones
    tools = [t for t in tools if t.name in wanted]

    from langgraph.prebuilt import create_react_agent
    from langchain_openai import ChatOpenAI
    agent = create_react_agent(ChatOpenAI(model="gpt-4o-mini"), tools)
    ...
```

### Use a different LLM
`build_keiro_agent(model, api_key=None)` takes any `BaseChatModel`. Swap in
Anthropic, Mistral, a local Ollama model, etc. — anything LangGraph's
`create_react_agent` accepts.

### Pass the key explicitly (don't read env)
```python
agent = await build_keiro_agent(model, api_key="keiro_...")
```

---

## 11. API reference

### `keiro_server_config(api_key: str | None = None) -> dict`
Returns the server block for `MultiServerMCPClient`. Raises `RuntimeError` if no
key is found (no `api_key` arg and no `KEIRO_API_KEY` env var) — it never sends a
blank header.

```python
{
  "transport": "streamable_http",
  "url": "https://kierolabs.space/mcp/api",
  "headers": {"Authorization": "Bearer keiro_..."},
}
```

### `build_keiro_client(api_key: str | None = None) -> MultiServerMCPClient`
A connected client. Call `await client.get_tools()` to get the LangChain tools.
Imports `langchain_mcp_adapters` lazily, so importing `keiro_langgraph` is cheap.

### `build_keiro_agent(model, api_key: str | None = None) -> CompiledStateGraph`
Loads Keiro's tools and returns a `create_react_agent` graph. `await
agent.ainvoke({"messages": [...]})` returns `{"messages": [...]}`.

### `demo(query: str, api_key: str | None = None) -> str`
End-to-end convenience: builds an OpenAI (`gpt-4o-mini`) ReAct agent and returns
the final answer string. Used by the CLI.

### `_self_check() -> None`
Asserts the config dict shape, the auth header, and that a missing key raises.
No network, no deps. Run via `python keiro_langgraph.py check`.

---

## 12. Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| `KEIRO_API_KEY not set` | run `./setup.sh`, or `export KEIRO_API_KEY=keiro_…`; ensure `run.sh` can read `.env`. |
| `401 MISSING_AUTH` | header not sent — config built without a key; check env / `.env`. |
| `401 INVALID_API_KEY` | wrong/expired/disabled key — regenerate in the dashboard; must start with `keiro_`. |
| `401 INVALID_TOKEN` | only if using a JWT — it expired, re-auth. |
| `tools/list` returns empty | the auth header isn't reaching Keiro; confirm a non-blank `KEIRO_API_KEY`. |
| `v2-data` / `v2-batch` errors on Free tier | those endpoints are gated — upgrade to Starter+. |
| Rate-limit (`429`) | back off; check §7. Free is ~1 `v2-fast` req / 6 s. |
| LLM errors | `OPENAI_API_KEY` missing/invalid, or `gpt-4o-mini` (the default in `demo()`) isn't on your account. |
| Unexpected credit deductions | only `web_search`, `web_research`, `extract_url`, `answer` cost credits; the 8 discovery tools are free. |
| `ModuleNotFoundError: langchain_mcp_adapters` | run `./setup.sh` (or `pip install langchain-mcp-adapters`). |

---

## 13. Security

- `.gitignore` excludes `.env` and `.venv` — keys are never committed.
- The key is read from an env var, never hardcoded in source.
- All traffic is HTTPS.
- `keiro_server_config` refuses to build a header with a missing/blank key rather
  than silently sending an empty Bearer.
- Rotate keys from the dashboard; treat `keiro_…` like any other secret.

---

## 14. Limitations & notes

- All Keiro tools are **read-only** — no mutation, no writes.
- MCP tool credit estimates (§3) are approximate; exact billing happens at the
  v2 endpoint layer (§4). Use `check_credits` / `get_endpoint` for the truth.
- The integration uses the **MCP server** (`kierolabs.space/mcp/api`); direct
  REST calls would go to `api.keirolabs.cloud/api/v2/*` — a different host. The
  MCP server proxies to the REST API for you.
- `extract_url` JSON-schema extraction works only in `medium`/`deep` modes.
- `v2-batch` jobs expire after 1 hour; poll `GET /api/v2/search/batch/:id`.
- LangGraph and its ecosystem pin their own versions; `setup.sh` installs the
  latest compatible releases. Pin versions if you need reproducibility.

---

## 15. File layout

```text
.
├── README.md                      # quick start (links here)
├── LANGGRAPH_README.md            # upstream LangGraph README (preserved)
├── setup.sh                       # one-command install + setup
├── run.sh                         # load .env, run the agent
├── .env.example                   # KEIRO_API_KEY / OPENAI_API_KEY template
├── keiro-integration/
│   ├── keiro_langgraph.py         # config, client, agent, demo, self-check
│   └── README.md                  # short integration-only readme
└── docs/
    └── keiro-langgraph.md         # this file
```

`libs/`, `examples/`, and the rest of the repo are the vendored upstream
LangGraph monorepo, included so the integration is self-contained.