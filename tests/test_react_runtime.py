from __future__ import annotations

import asyncio
import sys
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_SHARED = ROOT / "examples" / "_shared" / "src"
REACT_RUNTIME = ROOT / "examples" / "react-runtime" / "src"
sys.path[:0] = [str(EXAMPLE_SHARED), str(REACT_RUNTIME)]

from react_runtime.plugins import reactor as reactor_module  # noqa: E402
from react_runtime.plugins.mcp import McpPlugin  # noqa: E402
from react_runtime.plugins.memory import MemoryPlugin  # noqa: E402
from react_runtime.plugins.reactor import ReactorConfig, ReactorPlugin  # noqa: E402
from react_runtime.plugins.tools import ToolsPlugin  # noqa: E402


class FakeSessions:
    def session_key(self, ctx: Any) -> str:
        event = ctx.event
        return f"{event.adapter}:{event.channel_id}:{event.user_id}"


class FakeRuntime:
    def __init__(self, plugins: dict[str, Any]) -> None:
        self.plugins = plugins
        self.sessions = FakeSessions()

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
    traces: list[dict[str, Any]] = []
    memory = SimpleNamespace(
        state={},
        config={"trace_limit": 3},
        notes_for=lambda _: [],
        traces_for=lambda _: traces,
    )
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
        event=SimpleNamespace(adapter="onebot11", channel_id="room-1", user_id="alice"),
        reply=reply,
    )

    asyncio.run(plugin._run_react(cast(Any, ctx), "hello everyone"))

    assert replies == []
    assert traces[-1]["final"] == ""


def test_reactor_memory_is_scoped_to_the_current_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = FakeRuntime({})
    memory = MemoryPlugin(cast(Any, runtime))
    tools = ToolsPlugin(cast(Any, runtime))
    mcp = SimpleNamespace(describe_tools=lambda: "(no MCP tools)")
    runtime.plugins = {"memory": memory, "tools": tools, "mcp": mcp}
    plugin = ReactorPlugin(cast(Any, runtime))
    plugin._config_data = {"max_turns": 1}
    plugin._config_object = ReactorConfig(max_turns=1)
    prompts: list[str] = []

    def context(channel_id: str) -> SimpleNamespace:
        return SimpleNamespace(
            runtime=runtime,
            event=SimpleNamespace(adapter="onebot11", channel_id=channel_id, user_id="alice"),
            reply=AsyncMock(),
        )

    group_a = context("group-a")
    group_b = context("group-b")
    tools._remember("group-a-secret", cast(Any, group_a))

    async def fake_chat_json(*args: Any, **kwargs: Any) -> dict[str, Any]:
        prompts.append(args[1][1]["content"])
        return {"thought": "done", "silent": True}

    monkeypatch.setattr(reactor_module, "chat_json", fake_chat_json)
    asyncio.run(plugin._run_react(cast(Any, group_b), "hello"))
    asyncio.run(plugin._run_react(cast(Any, group_a), "hello"))

    assert "group-a-secret" not in prompts[0]
    assert "group-a-secret" in prompts[1]


def test_reactor_memory_evicts_least_recently_used_sessions() -> None:
    runtime = FakeRuntime({})
    memory = MemoryPlugin(cast(Any, runtime))
    memory._config_data = {"session_limit": 2}

    def context(user_id: str) -> SimpleNamespace:
        return SimpleNamespace(
            runtime=runtime,
            event=SimpleNamespace(adapter="onebot11", channel_id="room-1", user_id=user_id),
        )

    alice = context("alice")
    bob = context("bob")
    carol = context("carol")
    memory.notes_for(cast(Any, alice)).append("keep me")
    memory.session_state(cast(Any, bob))
    memory.session_state(cast(Any, alice))
    memory.session_state(cast(Any, carol))

    sessions = cast(dict[str, dict[str, Any]], memory.state["sessions"])
    assert list(sessions) == ["onebot11:room-1:alice", "onebot11:room-1:carol"]
    assert memory.notes_for(cast(Any, alice)) == ["keep me"]


@pytest.mark.parametrize(
    "field", ["note_limit", "note_length_limit", "trace_limit", "session_limit"]
)
def test_reactor_memory_rejects_zero_limits(field: str) -> None:
    with pytest.raises(ValidationError):
        MemoryPlugin.config_model.model_validate({field: 0})


def test_reactor_clips_persisted_notes() -> None:
    runtime = FakeRuntime({})
    memory = MemoryPlugin(cast(Any, runtime))
    tools = ToolsPlugin(cast(Any, runtime))
    runtime.plugins = {"memory": memory, "tools": tools}
    ctx = SimpleNamespace(
        runtime=runtime,
        event=SimpleNamespace(adapter="onebot11", channel_id="room-1", user_id="alice"),
    )

    result = tools._remember("n" * 5_000, cast(Any, ctx))

    assert len(memory.notes_for(cast(Any, ctx))[-1]) == 1_000
    assert len(result.removeprefix("Stored note: ")) == 1_000


@pytest.mark.parametrize("max_turns", [0, 21])
def test_reactor_rejects_unbounded_turn_counts(max_turns: int) -> None:
    with pytest.raises(ValidationError):
        ReactorConfig(max_turns=max_turns)


def test_reactor_clips_persisted_trace_payloads(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = FakeRuntime({})
    memory = MemoryPlugin(cast(Any, runtime))
    tools = SimpleNamespace(
        describe_tools=lambda: "large - returns a large result",
        run_tool=AsyncMock(return_value="o" * 10_000),
    )
    mcp = SimpleNamespace(describe_tools=lambda: "(no MCP tools)")
    runtime.plugins = {"memory": memory, "tools": tools, "mcp": mcp}
    plugin = ReactorPlugin(cast(Any, runtime))
    plugin._config_data = {"max_turns": 2}
    plugin._config_object = ReactorConfig(max_turns=2)
    responses: Iterator[dict[str, Any]] = iter(
        [
            {"thought": "use tool", "tool": "large", "input": "i" * 5_000},
            {"thought": "done", "silent": True},
        ]
    )

    async def fake_chat_json(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return next(responses)

    monkeypatch.setattr(reactor_module, "chat_json", fake_chat_json)
    ctx = SimpleNamespace(
        runtime=runtime,
        event=SimpleNamespace(adapter="onebot11", channel_id="room-1", user_id="alice"),
        reply=AsyncMock(),
    )

    asyncio.run(plugin._run_react(cast(Any, ctx), "q" * 5_000))

    stored = memory.traces_for(cast(Any, ctx))[-1]
    tool_event = next(event for event in stored["agent_trace"]["events"] if event["kind"] == "tool")
    assert len(stored["question"]) == 2_000
    assert len(tool_event["input"]) == 1_000
    assert len(tool_event["output"]) == 4_000


def test_reactor_invalid_action_returns_an_explicit_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = FakeRuntime({})
    memory = MemoryPlugin(cast(Any, runtime))
    tools = SimpleNamespace(describe_tools=lambda: "(no local tools)")
    mcp = SimpleNamespace(describe_tools=lambda: "(no MCP tools)")
    runtime.plugins = {"memory": memory, "tools": tools, "mcp": mcp}
    plugin = ReactorPlugin(cast(Any, runtime))
    plugin._config_data = {"max_turns": 1}
    plugin._config_object = ReactorConfig(max_turns=1)
    replies: list[str] = []

    async def fake_chat_json(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"thought": "missing action"}

    async def reply(message: str) -> None:
        replies.append(message)

    monkeypatch.setattr(reactor_module, "chat_json", fake_chat_json)
    ctx = SimpleNamespace(
        runtime=runtime,
        event=SimpleNamespace(adapter="onebot11", channel_id="room-1", user_id="alice"),
        reply=reply,
    )

    asyncio.run(plugin._run_react(cast(Any, ctx), "hello"))

    assert replies == ["The model returned an invalid action. Please try again."]
    assert "invalid action" in memory.traces_for(cast(Any, ctx))[-1]["trace"][-1]


def test_reactor_rejects_conflicting_actions(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = FakeRuntime({})
    memory = MemoryPlugin(cast(Any, runtime))
    tools = SimpleNamespace(describe_tools=lambda: "(no local tools)")
    mcp = SimpleNamespace(describe_tools=lambda: "(no MCP tools)")
    runtime.plugins = {"memory": memory, "tools": tools, "mcp": mcp}
    plugin = ReactorPlugin(cast(Any, runtime))
    plugin._config_data = {"max_turns": 1}
    plugin._config_object = ReactorConfig(max_turns=1)
    replies: list[str] = []

    async def fake_chat_json(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"thought": "ambiguous", "reply": "hello", "silent": True}

    async def reply(message: str) -> None:
        replies.append(message)

    monkeypatch.setattr(reactor_module, "chat_json", fake_chat_json)
    ctx = SimpleNamespace(
        runtime=runtime,
        event=SimpleNamespace(adapter="onebot11", channel_id="room-1", user_id="alice"),
        reply=reply,
    )

    asyncio.run(plugin._run_react(cast(Any, ctx), "hello"))

    assert replies == ["The model returned an invalid action. Please try again."]


def test_reactor_declares_all_required_plugins() -> None:
    assert ReactorPlugin.requires == ("mcp", "memory", "tools")


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
