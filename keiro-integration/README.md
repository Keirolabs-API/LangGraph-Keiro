# Keiro × LangGraph

Wire [Keiro](https://kierolabs.space)'s remote MCP server into a LangGraph
ReAct agent. Keiro gives your agent 4 web tools (cost credits per call) plus 8
free docs/utility tools — all read-only.

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

## Install

```bash
pip install langgraph langchain-mcp-adapters langchain-openai
```

## Use in your own graph

```python
import asyncio
from langchain_openai import ChatOpenAI
from keiro_langgraph import build_keiro_agent

async def main():
    agent = await build_keiro_agent(ChatOpenAI(model="gpt-4o-mini"))
    r = await agent.ainvoke({"messages": [{"role": "user", "content": "What changed in the EU AI Act this month?"}]})
    print(r["messages"][-1].content)

asyncio.run(main())
```

`build_keiro_agent` loads Keiro's MCP tools via `langchain_mcp_adapters`
`MultiServerMCPClient` and hands them to LangGraph's `create_react_agent`.

## Run the demo

```bash
KEIRO_API_KEY=keiro_... OPENAI_API_KEY=sk-... \
    python keiro_langgraph.py "latest news on X"
```

Costs Keiro credits + LLM spend.

## Verify the wiring without network or deps

```bash
python keiro_langgraph.py check   # self-check: config + auth header
```