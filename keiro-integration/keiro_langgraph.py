"""Keiro + LangGraph integration.

Wires Keiro's remote MCP server (web_search, web_research, extract_url,
answer, + 8 free docs/utility tools) into a LangGraph ReAct agent via
`langchain_mcp_adapters`.

Keiro endpoint: https://kierolabs.space/mcp/api  (Streamable HTTP)
Auth:           Authorization: Bearer keiro_<key>  (KEIRO_API_KEY env var)

Install:
    pip install langgraph langchain-mcp-adapters langchain-openai

Run a one-shot query:
    KEIRO_API_KEY=keiro_... OPENAI_API_KEY=... \
        python -m keiro_langgraph "latest news on X"
"""

from __future__ import annotations

import os
import sys

KEIRO_MCP_URL = "https://kierolabs.space/mcp/api"


def keiro_server_config(api_key: str | None = None) -> dict:
    """Server block for `MultiServerMCPClient`. Pure — no heavy deps.

    Keiro speaks Streamable HTTP and wants the dashboard key in a Bearer
    header. `langchain_mcp_adapters` calls this transport `streamable_http`.
    """
    key = api_key or os.environ.get("KEIRO_API_KEY")
    if not key:
        raise RuntimeError(
            "KEIRO_API_KEY not set — create a key (starts with keiro_) in the "
            "Keiro dashboard under API Keys, then export KEIRO_API_KEY=keiro_..."
        )
    return {
        "transport": "streamable_http",
        "url": KEIRO_MCP_URL,
        "headers": {"Authorization": f"Bearer {key}"},
    }


async def build_keiro_client(api_key: str | None = None):
    """A connected `MultiServerMCPClient` for Keiro. Call `await client.get_tools()`."""
    from langchain_mcp_adapters.client import MultiServerMCPClient

    return MultiServerMCPClient({"keirolabs": keiro_server_config(api_key)})


async def build_keiro_agent(model, api_key: str | None = None):
    """Load Keiro's MCP tools and wrap a LangGraph ReAct agent around them."""
    from langgraph.prebuilt import create_react_agent

    client = await build_keiro_client(api_key)
    tools = await client.get_tools()
    return create_react_agent(model, tools)


async def demo(query: str, api_key: str | None = None) -> str:
    """End-to-end: load tools, build an OpenAI-backed ReAct agent, answer `query`.

    Costs Keiro credits (the four API tools deduct per call) + your LLM spend.
    """
    from langchain_openai import ChatOpenAI

    model = ChatOpenAI(model="gpt-4o-mini")
    agent = await build_keiro_agent(model, api_key)
    result = await agent.ainvoke({"messages": [{"role": "user", "content": query}]})
    return result["messages"][-1].content


def _self_check() -> None:
    """Smallest thing that fails if the wiring logic breaks. No network, no deps."""
    cfg = keiro_server_config(api_key="keiro_test")
    assert cfg["transport"] == "streamable_http", cfg
    assert cfg["url"] == KEIRO_MCP_URL, cfg
    assert cfg["headers"] == {"Authorization": "Bearer keiro_test"}, cfg

    # Missing key must raise, not silently send a blank header.
    import os as _os
    saved = _os.environ.pop("KEIRO_API_KEY", None)
    try:
        try:
            keiro_server_config(api_key=None)
            raise AssertionError("expected RuntimeError when KEIRO_API_KEY unset")
        except RuntimeError:
            pass
    finally:
        if saved is not None:
            _os.environ["KEIRO_API_KEY"] = saved
    print("self-check ok")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        _self_check()
    elif len(sys.argv) > 1:
        import asyncio

        print(asyncio.run(demo(" ".join(sys.argv[1:]))))
    else:
        _self_check()