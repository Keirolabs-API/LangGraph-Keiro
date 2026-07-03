# Keiro × LangGraph

Wire [Keiro](https://kierolabs.space)'s remote MCP server into a LangGraph
ReAct agent. Keiro gives your agent 4 web tools (cost credits per call) plus 8
free docs/utility tools — all read-only.

> **Full documentation** — architecture, every tool & endpoint, params, credits,
> rate limits, auth, troubleshooting: see [`docs/keiro-langgraph.md`](docs/keiro-langgraph.md).

| Tool | Credits | Purpose |
|------|---------|---------|
| `web_search` | ~1–2 | structured web results |
| `web_research` | ~3–5 | deep multi-source research + synthesis |
| `extract_url` | ~1–3 | structured extraction from a URL (JSON schema) |
| `answer` | ~5 | direct Q&A, web search + AI synthesis |
| `list_endpoints`, `get_endpoint`, `get_rate_limits`, `get_auth`, `generate_code`, `get_mcp_tools`, `suggest_schema`, `check_credits` | free | Keiro API discovery |

## Endpoint / auth

- URL: `https://kierolabs.space/mcp/api`
- Transport: Streamable HTTP
- Header: `Authorization: Bearer keiro_<key>` — `KEIRO_API_KEY` env var

`initialize` runs without auth; every `tools/list` and `tools/call` needs the
header.

## Prerequisites

- Python 3.10+
- A Keiro API key (starts with `keiro_`) from the [Keiro dashboard](https://kierolabs.space) → API Keys
- An OpenAI API key (the ReAct agent's LLM) — or set `OPENAI_API_KEY`

## One-command install + setup

```bash
git clone https://github.com/Keirolabs-API/LangGraph-Keiro && cd LangGraph-Keiro && ./setup.sh
```

This clones the repo, then `setup.sh` creates a `.venv`, installs
`langgraph langchain-mcp-adapters langchain-openai`, writes a `.env` from
`.env.example` (prompting for your Keiro and OpenAI keys), and runs a wiring
self-check. No network calls in the check — it only asserts the config/auth
header logic. Re-running `./setup.sh` is idempotent and won't clobber existing
keys.

## Run a query

```bash
./run.sh "What changed in the EU AI Act this month?"
```

`run.sh` loads `.env` and invokes `keiro-integration/keiro_langgraph.py`.
Costs Keiro credits (the four API tools deduct per call) + your LLM spend.

## Use in your own graph

```python
import asyncio
from langchain_openai import ChatOpenAI
from keiro_langgraph import build_keiro_agent  # add keiro-integration/ to sys.path

async def main():
    agent = await build_keiro_agent(ChatOpenAI(model="gpt-4o-mini"))
    r = await agent.ainvoke({"messages": [{"role": "user", "content": "latest news on X"}]})
    print(r["messages"][-1].content)

asyncio.run(main())
```

`build_keiro_agent` loads Keiro's MCP tools via `langchain_mcp_adapters`
`MultiServerMCPClient` and hands them to LangGraph's `create_react_agent`.

## Verify the wiring without network or deps

```bash
python keiro-integration/keiro_langgraph.py check
```

## Troubleshooting

- `KEIRO_API_KEY not set` — run `./setup.sh`, or `export KEIRO_API_KEY=keiro_...` and ensure `run.sh` can read `.env`.
- `401 / Unauthorized` from Keiro — the key is wrong, expired, or missing the `keiro_` prefix.
- `tools/list` empty — the `Authorization: Bearer …` header isn't reaching Keiro; confirm `.env` has a non-empty `KEIRO_API_KEY`.
- LLM errors — `OPENAI_API_KEY` missing/invalid, or the model name in `keiro_langgraph.py` (`gpt-4o-mini` by default) isn't available to your key.
- Credit deductions you didn't expect — only `web_search`, `web_research`, `extract_url`, and `answer` cost credits; the 8 discovery tools are free.

## Files

- `keiro-integration/keiro_langgraph.py` — server config, client + agent builders, demo, self-check.
- `keiro-integration/README.md` — short integration-only README.
- `setup.sh` / `run.sh` / `.env.example` — install/run helpers.
- `libs/`, `docs/`, `examples/` — the upstream LangGraph monorepo (vendored so the integration is self-contained).

## License

See `LICENSE`.