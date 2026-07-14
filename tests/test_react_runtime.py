from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_SHARED = ROOT / "examples" / "_shared" / "src"
REACT_RUNTIME = ROOT / "examples" / "react-runtime" / "src"
sys.path[:0] = [str(EXAMPLE_SHARED), str(REACT_RUNTIME)]

from react_runtime.plugins import reactor as reactor_module  # noqa: E402
from react_runtime.plugins.mcp import McpPlugin  # noqa: E402
from react_runtime.plugins.reactor import ReactorConfig, ReactorPlugin  # noqa: E402


class FakeRuntime:
    def __init__(self, plugins: dict[str, Any]) -> None:
        self.plugins = plugins

    def get_plugin(self, name: str) -> Any:
        return self.plugins[name]


def test_chat_fallback_only_handles_plain_messages_when_enabled() -> None:
    plugin = ReactorPlugin(cast(Any, FakeRuntime({})))
    plugin._config_data = {"chat_mode": True}
    plugin._run_react = AsyncMock()  # type: ignore[method-assign]

    plain_ctx = SimpleNamespace(event=SimpleNamespace(text="  hello  "))
    command_ctx = SimpleNamespace(event=SimpleNamespace(text="/ask hello"))

    asyncio.run(plugin.chat_fallback(cast(Any, plain_ctx)))
    asyncio.run(plugin.chat_fallback(cast(Any, command_ctx)))

    plugin._run_react.assert_awaited_once_with(plain_ctx, "hello")


def test_reactor_silent_action_does_not_reply_in_onebot_chat(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    memory = SimpleNamespace(state={"notes": []}, config={"trace_limit": 3})
    tools = SimpleNamespace(describe_tools=lambda: "(no local tools)")
    mcp = SimpleNamespace(describe_tools=lambda: "(no MCP tools)")
    runtime = FakeRuntime({"memory": memory, "tools": tools, "mcp": mcp})
    plugin = ReactorPlugin(cast(Any, runtime))
    plugin._config_data = {"max_turns": 1}
    plugin._config_object = ReactorConfig(max_turns=1)
    replies: list[str] = []

    async def fake_chat_json(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"thought": "background chatter", "silent": True}

    async def reply(message: str) -> None:
        replies.append(message)

    monkeypatch.setattr(reactor_module, "chat_json", fake_chat_json)
    ctx = SimpleNamespace(
        runtime=runtime,
        event=SimpleNamespace(adapter="onebot11"),
        reply=reply,
    )

    asyncio.run(plugin._run_react(cast(Any, ctx), "hello everyone"))

    assert replies == []
    assert memory.state["traces"][-1]["final"] == ""


def test_mcp_text_input_is_normalized_to_an_argument_object() -> None:
    calls: list[tuple[str, dict[str, Any]]] = []

    class FakeClient:
        async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
            calls.append((name, arguments))
            return "ok"

    plugin = McpPlugin(cast(Any, FakeRuntime({})))
    plugin.state["client"] = {"browser": FakeClient()}

    result = asyncio.run(plugin.call_tool("browser.open", "https://example.test"))

    assert result == "ok"
    assert calls == [("open", {"input": "https://example.test"})]
