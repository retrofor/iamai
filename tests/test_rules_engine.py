from __future__ import annotations

import asyncio
from pathlib import Path

from iamai import (
    Context,
    Event,
    Message,
    Plugin,
    Runtime,
    channel_id_is,
    field,
    none_of,
    platform_is,
    raw_field,
    ruleset,
    state_field,
    text_equals,
    user_id_is,
    when_all,
    when_any,
    word_in,
)
from iamai.adapter import Adapter
from iamai.plugin import BoundHandler, HandlerSpec


class DummyAdapter(Adapter):
    name = "dummy"

    async def start(self) -> None:
        return None

    async def send_message(
        self,
        message: Message,
        *,
        event: Event | None = None,
        target: object | None = None,
    ) -> object:
        return None


class DummyPlugin(Plugin):
    name = "dummy-plugin"


async def _evaluate(rule: object, ctx: Context) -> tuple[bool, dict[str, object]]:
    return await rule.evaluate(ctx.runtime, ctx, {})  # type: ignore[attr-defined]


def _make_context(tmp_path: Path) -> Context:
    runtime = Runtime(
        {
            "runtime": {"adapters": []},
            "adapter": {},
            "plugin": {},
            "state": {},
            "__meta__": {"root_dir": str(tmp_path)},
        },
        base_path=tmp_path,
    )
    adapter = DummyAdapter(runtime)
    plugin = DummyPlugin(runtime)
    plugin.state["phase"] = "open"
    runtime.state["ops"] = {"enabled": True}
    event = Event(
        id="evt-1",
        adapter="dummy",
        platform="qq",
        type="message",
        detail_type="group",
        user_id="42",
        channel_id="100",
        guild_id="100",
        message=Message("Deploy service alpha"),
        raw={"message_type": "group", "sender": {"role": "admin"}, "score": 7},
    )
    handler = BoundHandler(
        plugin, HandlerSpec(func_name="handle", kind="message"), lambda ctx: None
    )
    return Context(
        runtime=runtime,
        adapter=adapter,
        plugin=plugin,
        event=event,
        handler=handler,
        matches={"command": "deploy"},
    )


def test_field_rules_support_dotted_paths_and_capture(tmp_path: Path) -> None:
    ctx = _make_context(tmp_path)
    rule = when_all(
        platform_is("qq"),
        user_id_is(42),
        channel_id_is("100"),
        raw_field("sender.role", equals="admin", capture_as="role"),
        raw_field("score", ge=5),
        field("event.type", source="context", equals="message"),
    )

    ok, payload = asyncio.run(_evaluate(rule, ctx))

    assert ok is True
    assert payload["role"] == "admin"


def test_text_rules_and_negative_composition(tmp_path: Path) -> None:
    ctx = _make_context(tmp_path)
    rule = when_any(text_equals("deploy service alpha", ignore_case=True), word_in("rollback"))
    guard = none_of(word_in("danger"))

    assert asyncio.run(_evaluate(rule & guard, ctx))[0] is True


def test_state_and_shared_state_field_rules(tmp_path: Path) -> None:
    ctx = _make_context(tmp_path)
    rule = state_field("phase", equals="open") & field(
        "ops.enabled",
        source="shared_state",
        equals=True,
    )

    assert asyncio.run(_evaluate(rule, ctx))[0] is True


def test_ruleset_returns_first_priority_match_and_payload(tmp_path: Path) -> None:
    ctx = _make_context(tmp_path)
    routing = (
        ruleset("router")
        .when("fallback", text_equals("anything"), priority=50)
        .when("deploy", word_in("deploy").with_payload(intent="deploy"), priority=10)
        .when(
            "admin",
            raw_field("sender.role", equals="admin").with_payload(role="admin"),
            priority=20,
        )
    )

    ok, payload = asyncio.run(_evaluate(routing.as_rule(), ctx))

    assert ok is True
    assert payload["ruleset"] == ["deploy"]
    assert payload["intent"] == "deploy"


def test_ruleset_can_collect_all_matches(tmp_path: Path) -> None:
    ctx = _make_context(tmp_path)
    routing = (
        ruleset("router")
        .when("deploy", word_in("deploy"), priority=10)
        .when("admin", raw_field("sender.role", equals="admin"), priority=20)
    )

    ok, payload = asyncio.run(_evaluate(routing.as_rule(first=False), ctx))

    assert ok is True
    assert payload["ruleset"] == ["deploy", "admin"]
