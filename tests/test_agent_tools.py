from __future__ import annotations

import asyncio
from typing import Any

import pytest
from iamai.agent import AgentError, AgentTrace, Tool, ToolRegistry


def test_tool_registry_keeps_legacy_registration_compatible() -> None:
    tools = ToolRegistry()
    tools.register("Echo", "Echo input.", lambda payload: payload)

    metadata = tools.list_tools()

    assert metadata == [
        {
            "name": "echo",
            "description": "Echo input.",
            "permission_name": "echo",
            "input_schema": None,
            "audit_fields": [],
            "requires_approval": False,
            "runtime_capabilities": [],
        }
    ]
    assert asyncio.run(tools.call("echo", "hello")) == "hello"


def test_tool_registry_records_metadata_and_trace() -> None:
    tools = ToolRegistry()
    tools.register(
        "web_search",
        "Search the web.",
        lambda payload: {"result": payload["query"]},
        permission_name="web.search",
        input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
        audit_fields=("query",),
        runtime_capabilities=("network:http",),
    )
    trace = AgentTrace("demo")

    result = asyncio.run(tools.call("web_search", {"query": "iamai", "secret": "x"}, trace=trace))

    assert result == {"result": "iamai"}
    assert tools.list_tools()[0]["permission_name"] == "web.search"
    assert trace.events[0].metadata["outcome"] == "started"
    assert trace.events[0].input == {"query": "iamai"}
    assert trace.events[-1].metadata["outcome"] == "ok"


def test_tool_registry_blocks_unapproved_tool_and_allows_callback() -> None:
    tools = ToolRegistry()
    tools.register(
        "deploy",
        "Deploy a target.",
        lambda payload: f"deployed {payload['target']}",
        permission_name="deploy.write",
        audit_fields=("target",),
        requires_approval=True,
    )
    trace = AgentTrace("deploy")

    with pytest.raises(AgentError, match="requires approval"):
        asyncio.run(tools.call("deploy", {"target": "prod"}, trace=trace))

    async def approve(tool: Tool, payload: Any) -> bool:
        return tool.permission_name == "deploy.write" and payload["target"] == "prod"

    result = asyncio.run(
        tools.call("deploy", {"target": "prod"}, trace=trace, approval_callback=approve)
    )

    assert result == "deployed prod"
    assert any(event.metadata.get("outcome") == "denied" for event in trace.events)
    assert trace.events[-1].metadata["outcome"] == "ok"
