"""Composable event matching rules for iamai handlers."""

from __future__ import annotations

import re
from collections.abc import Awaitable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field as dataclass_field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Literal

RulePayload = dict[str, Any]
RuleResult = bool | Mapping[str, Any] | tuple[bool, Mapping[str, Any] | None] | None
RuleCallback = Callable[..., RuleResult | Awaitable[RuleResult]]
RuleSource = Literal["event", "raw", "state", "shared_state", "matches", "context"]
_MISSING = object()

__all__ = [
    "FieldCondition",
    "FieldOp",
    "Rule",
    "RuleCallback",
    "RuleCase",
    "RuleMatch",
    "RulePayload",
    "RuleResult",
    "RuleSource",
    "Ruleset",
    "adapter_is",
    "all_of",
    "allow",
    "any_of",
    "channel_id_is",
    "contains",
    "deny",
    "detail_type_is",
    "endswith",
    "ensure_rule",
    "event_type_is",
    "field",
    "fullmatch",
    "guild_id_is",
    "group_message",
    "match_fields",
    "none_of",
    "platform_is",
    "predicate",
    "private_message",
    "raw_field",
    "regex",
    "rule",
    "ruleset",
    "startswith",
    "state_field",
    "text_equals",
    "user_id_is",
    "when_all",
    "when_any",
    "word_in",
]


class FieldOp(str, Enum):
    """Supported operators for dotted-path field rules."""

    EXISTS = "exists"
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IN = "in"
    CONTAINS = "contains"
    STARTSWITH = "startswith"
    ENDSWITH = "endswith"
    REGEX = "regex"
    GT = "gt"
    GE = "ge"
    LT = "lt"
    LE = "le"


@dataclass(frozen=True, slots=True)
class FieldCondition:
    """One field comparison used by ``field`` and ``match_fields``."""

    path: str | Sequence[str]
    op: FieldOp = FieldOp.EXISTS
    value: Any = _MISSING
    source: RuleSource = "event"
    capture_as: str | None = None
    flags: int = 0


@dataclass(frozen=True, slots=True)
class Rule:
    """Composable async rule predicate that may also return match payloads."""

    _executor: Callable[["Runtime", "Context", dict[Any, Any]], Any]
    name: str = "rule"

    async def evaluate(
        self,
        runtime: "Runtime",
        ctx: "Context",
        cache: dict[Any, Any],
    ) -> tuple[bool, RulePayload]:
        """Return whether the rule matches and any extracted match payload."""
        result = await self._executor(runtime, ctx, cache)
        return _normalize_rule_result(result)

    def __and__(self, other: Any) -> "Rule":
        """Return a rule that requires both rules to match."""
        other_rule = ensure_rule(other)

        async def _executor(
            runtime: "Runtime", ctx: "Context", cache: dict[Any, Any]
        ) -> tuple[bool, RulePayload]:
            ok_left, matches_left = await self.evaluate(runtime, ctx, cache)
            if not ok_left:
                return False, {}
            ok_right, matches_right = await other_rule.evaluate(runtime, ctx, cache)
            if not ok_right:
                return False, {}
            merged = dict(matches_left)
            merged.update(matches_right)
            return True, merged

        return Rule(_executor, name=f"({self.name}&{other_rule.name})")

    def __or__(self, other: Any) -> "Rule":
        """Return a rule that matches when either rule matches."""
        other_rule = ensure_rule(other)

        async def _executor(
            runtime: "Runtime", ctx: "Context", cache: dict[Any, Any]
        ) -> tuple[bool, RulePayload]:
            ok_left, matches_left = await self.evaluate(runtime, ctx, cache)
            if ok_left:
                return True, matches_left
            return await other_rule.evaluate(runtime, ctx, cache)

        return Rule(_executor, name=f"({self.name}|{other_rule.name})")

    def __invert__(self) -> "Rule":
        """Return a rule that negates this rule and discards match payloads."""

        async def _executor(
            runtime: "Runtime", ctx: "Context", cache: dict[Any, Any]
        ) -> tuple[bool, RulePayload]:
            ok, _ = await self.evaluate(runtime, ctx, cache)
            return (not ok), {}

        return Rule(_executor, name=f"~{self.name}")

    def named(self, name: str) -> "Rule":
        """Return this rule with a display name useful in traces and rulesets."""

        return Rule(self._executor, name=str(name))

    def with_payload(self, **payload: Any) -> "Rule":
        """Merge static payload values into a successful rule result."""

        async def _executor(
            runtime: "Runtime", ctx: "Context", cache: dict[Any, Any]
        ) -> tuple[bool, RulePayload]:
            ok, matches = await self.evaluate(runtime, ctx, cache)
            if not ok:
                return False, {}
            merged = dict(matches)
            merged.update(payload)
            return True, merged

        return Rule(_executor, name=self.name)


@dataclass(frozen=True, slots=True)
class RuleCase:
    """One named rule inside a ``Ruleset``."""

    name: str
    rule: Rule
    priority: int = 100


@dataclass(frozen=True, slots=True)
class RuleMatch:
    """Result produced by ``Ruleset`` evaluation."""

    name: str
    priority: int
    payload: RulePayload = dataclass_field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Ruleset:
    """A priority-ordered collection of named rules.

    This mirrors rule-engine style rulesets without changing iamai handler
    dispatch. Use it inside a single handler rule when you need explainable,
    named branches.
    """

    name: str
    cases: tuple[RuleCase, ...] = ()

    def when(self, name: str, condition: Any, *, priority: int = 100) -> "Ruleset":
        """Return a new ruleset with one named case appended."""

        case = RuleCase(str(name), ensure_rule(condition), int(priority))
        return Ruleset(self.name, (*self.cases, case))

    def as_rule(self, *, first: bool = True, capture_as: str = "ruleset") -> Rule:
        """Convert this ruleset into a single rule.

        When ``first`` is true, evaluation stops at the first matching case.
        Otherwise all matching cases are evaluated and returned.
        """

        async def _executor(
            runtime: "Runtime", ctx: "Context", cache: dict[Any, Any]
        ) -> tuple[bool, RulePayload]:
            matches: list[RuleMatch] = []
            payload: RulePayload = {}
            for case in self._ordered_cases():
                ok, case_payload = await case.rule.evaluate(runtime, ctx, cache)
                if not ok:
                    continue
                match = RuleMatch(case.name, case.priority, case_payload)
                matches.append(match)
                payload.update(case_payload)
                if first:
                    break
            if not matches:
                return False, {}
            payload[capture_as] = [match.name for match in matches]
            payload[f"{capture_as}_matches"] = matches
            return True, payload

        return Rule(_executor, name=self.name)

    async def evaluate(
        self,
        runtime: "Runtime",
        ctx: "Context",
        cache: dict[Any, Any],
        *,
        first: bool = False,
    ) -> list[RuleMatch]:
        """Evaluate the ruleset directly and return matched cases."""

        matches: list[RuleMatch] = []
        for case in self._ordered_cases():
            ok, payload = await case.rule.evaluate(runtime, ctx, cache)
            if ok:
                matches.append(RuleMatch(case.name, case.priority, payload))
                if first:
                    break
        return matches

    def _ordered_cases(self) -> tuple[RuleCase, ...]:
        return tuple(sorted(self.cases, key=lambda item: (item.priority, item.name)))


def rule(func: RuleCallback) -> Rule:
    """Wrap a callable as a dependency-injected event matching rule."""

    async def _executor(runtime: "Runtime", ctx: "Context", cache: dict[Any, Any]) -> Any:
        return await runtime._invoke_callable(func, ctx, cache=cache)

    return Rule(_executor, name=getattr(func, "__name__", "rule"))


def ensure_rule(value: Any) -> Rule:
    """Coerce a ``Rule`` or callable into a ``Rule`` instance."""

    if isinstance(value, Rule):
        return value
    if callable(value):
        return rule(value)
    raise TypeError(f"unsupported rule value: {value!r}")


def all_of(*values: Any) -> Rule:
    """Create a rule that matches only when every child rule matches."""

    current = allow()
    for value in values:
        current = current & ensure_rule(value)
    return current


def any_of(*values: Any) -> Rule:
    """Create a rule that matches when at least one child rule matches."""

    if not values:
        return deny()
    current = ensure_rule(values[0])
    for value in values[1:]:
        current = current | ensure_rule(value)
    return current


def when_all(*values: Any) -> Rule:
    """Alias for ``all_of`` inspired by ruleset engines."""

    return all_of(*values)


def when_any(*values: Any) -> Rule:
    """Alias for ``any_of`` inspired by ruleset engines."""

    return any_of(*values)


def none_of(*values: Any) -> Rule:
    """Create a rule that matches only when none of the child rules match."""

    return ~any_of(*values)


def ruleset(name: str = "ruleset") -> Ruleset:
    """Create an empty named ruleset."""

    return Ruleset(str(name))


def allow() -> Rule:
    """Create a rule that always matches."""

    return rule(lambda: True)


def deny() -> Rule:
    """Create a rule that never matches."""

    return rule(lambda: False)


def adapter_is(*names: str) -> Rule:
    """Match events emitted by one of the selected adapters."""

    allowed = {str(name) for name in names}
    return rule(lambda event: event.adapter in allowed)


def event_type_is(*names: str) -> Rule:
    """Match events whose normalized event type is in ``names``."""

    allowed = {str(name) for name in names}
    return rule(lambda event: event.type in allowed)


def detail_type_is(*names: str) -> Rule:
    """Match events whose normalized detail type is in ``names``."""

    allowed = {str(name) for name in names}
    return rule(lambda event: event.detail_type in allowed)


def platform_is(*names: str) -> Rule:
    """Match events emitted by one of the selected platforms."""

    allowed = {str(name) for name in names}
    return rule(lambda event: event.platform in allowed)


def user_id_is(*values: str | int) -> Rule:
    """Match events whose ``user_id`` is in ``values``."""

    allowed = {str(value) for value in values}
    return rule(lambda event: event.user_id in allowed)


def channel_id_is(*values: str | int) -> Rule:
    """Match events whose ``channel_id`` is in ``values``."""

    allowed = {str(value) for value in values}
    return rule(lambda event: event.channel_id in allowed)


def guild_id_is(*values: str | int) -> Rule:
    """Match events whose ``guild_id`` is in ``values``."""

    allowed = {str(value) for value in values}
    return rule(lambda event: event.guild_id in allowed)


def startswith(*prefixes: str) -> Rule:
    """Match message text that starts with one of ``prefixes``."""

    items = tuple(str(prefix) for prefix in prefixes)
    return rule(lambda event: event.text.startswith(items))


def endswith(*suffixes: str) -> Rule:
    """Match message text that ends with one of ``suffixes``."""

    items = tuple(str(suffix) for suffix in suffixes)
    return rule(lambda event: event.text.endswith(items))


def contains(*tokens: str, require_all: bool = False) -> Rule:
    """Match message text containing any token, or every token if requested."""

    items = tuple(str(token) for token in tokens)

    def _check(event: Any) -> bool:
        if require_all:
            return all(token in event.text for token in items)
        return any(token in event.text for token in items)

    return rule(_check)


def regex(pattern: str, *, flags: int = 0) -> Rule:
    """Match message text with ``re.search`` and expose named groups."""

    compiled = re.compile(pattern, flags)

    def _check(event: Any) -> dict[str, Any] | bool:
        match = compiled.search(event.text)
        if match is None:
            return False
        payload: dict[str, Any] = {"regex": match}
        payload.update(match.groupdict())
        return payload

    return rule(_check)


def fullmatch(pattern: str, *, flags: int = 0) -> Rule:
    """Match stripped message text with ``re.fullmatch`` and expose groups."""

    compiled = re.compile(pattern, flags)

    def _check(event: Any) -> dict[str, Any] | bool:
        match = compiled.fullmatch(event.text.strip())
        if match is None:
            return False
        payload: dict[str, Any] = {"regex": match}
        payload.update(match.groupdict())
        return payload

    return rule(_check)


def text_equals(*values: str, ignore_case: bool = False, strip: bool = True) -> Rule:
    """Match message text exactly against one of ``values``."""

    expected = tuple(
        _normalize_text(value, ignore_case=ignore_case, strip=strip) for value in values
    )

    def _check(event: Any) -> bool:
        actual = _normalize_text(event.text, ignore_case=ignore_case, strip=strip)
        return actual in expected

    return rule(_check)


def word_in(*words: str, ignore_case: bool = True) -> Rule:
    """Match whole words in message text."""

    flags = re.IGNORECASE if ignore_case else 0
    escaped = "|".join(re.escape(word) for word in words)
    return regex(rf"\b(?:{escaped})\b", flags=flags) if escaped else deny()


def field(
    path: str | Sequence[str],
    *,
    source: RuleSource = "event",
    exists: bool | None = None,
    equals: Any = _MISSING,
    not_equals: Any = _MISSING,
    in_: Iterable[Any] | None = None,
    contains: Any = _MISSING,
    startswith: str | tuple[str, ...] | None = None,
    endswith: str | tuple[str, ...] | None = None,
    regex: str | re.Pattern[str] | None = None,
    gt: Any = _MISSING,
    ge: Any = _MISSING,
    lt: Any = _MISSING,
    le: Any = _MISSING,
    capture_as: str | None = None,
    flags: int = 0,
) -> Rule:
    """Match a dotted path on event/raw/state/shared_state/matches/context.

    Multiple comparisons are combined with logical AND. When ``capture_as`` is
    provided, the resolved value is exposed in the rule payload.
    """

    conditions: list[FieldCondition] = []
    if exists is not None:
        conditions.append(FieldCondition(path, FieldOp.EXISTS, exists, source, capture_as, flags))
    if equals is not _MISSING:
        conditions.append(FieldCondition(path, FieldOp.EQUALS, equals, source, capture_as, flags))
    if not_equals is not _MISSING:
        conditions.append(
            FieldCondition(path, FieldOp.NOT_EQUALS, not_equals, source, capture_as, flags)
        )
    if in_ is not None:
        conditions.append(FieldCondition(path, FieldOp.IN, tuple(in_), source, capture_as, flags))
    if contains is not _MISSING:
        conditions.append(
            FieldCondition(path, FieldOp.CONTAINS, contains, source, capture_as, flags)
        )
    if startswith is not None:
        conditions.append(
            FieldCondition(path, FieldOp.STARTSWITH, startswith, source, capture_as, flags)
        )
    if endswith is not None:
        conditions.append(
            FieldCondition(path, FieldOp.ENDSWITH, endswith, source, capture_as, flags)
        )
    if regex is not None:
        conditions.append(FieldCondition(path, FieldOp.REGEX, regex, source, capture_as, flags))
    if gt is not _MISSING:
        conditions.append(FieldCondition(path, FieldOp.GT, gt, source, capture_as, flags))
    if ge is not _MISSING:
        conditions.append(FieldCondition(path, FieldOp.GE, ge, source, capture_as, flags))
    if lt is not _MISSING:
        conditions.append(FieldCondition(path, FieldOp.LT, lt, source, capture_as, flags))
    if le is not _MISSING:
        conditions.append(FieldCondition(path, FieldOp.LE, le, source, capture_as, flags))
    if not conditions:
        conditions.append(FieldCondition(path, FieldOp.EXISTS, True, source, capture_as, flags))
    return match_fields(*conditions)


def raw_field(path: str | Sequence[str], **kwargs: Any) -> Rule:
    """Match a dotted path inside ``event.raw``."""

    return field(path, source="raw", **kwargs)


def state_field(path: str | Sequence[str], **kwargs: Any) -> Rule:
    """Match a dotted path inside the current plugin state."""

    return field(path, source="state", **kwargs)


def match_fields(*conditions: FieldCondition) -> Rule:
    """Create a rule that requires every field condition to match."""

    items = tuple(conditions)

    def _check(ctx: "Context") -> RuleResult:
        payload: RulePayload = {}
        for condition in items:
            value = _resolve_source_path(ctx, condition.source, condition.path)
            ok, match_payload = _evaluate_condition(condition, value)
            if not ok:
                return False
            payload.update(match_payload)
        return payload or True

    return rule(_check)


def private_message() -> Rule:
    """Match OneBot-style private message events."""

    return rule(lambda event: _message_type(event) == "private")


def group_message() -> Rule:
    """Match OneBot-style group message events."""

    return rule(lambda event: _message_type(event) == "group")


def predicate(func: Callable[..., Any]) -> Rule:
    """Alias for ``rule`` that reads naturally in decorator arguments."""

    return ensure_rule(func)


def _normalize_text(value: Any, *, ignore_case: bool, strip: bool) -> str:
    text = str(value)
    if strip:
        text = text.strip()
    return text.casefold() if ignore_case else text


def _resolve_source_path(ctx: "Context", source: RuleSource, path: str | Sequence[str]) -> Any:
    if source == "event":
        root: Any = ctx.event
    elif source == "raw":
        root = ctx.event.raw
    elif source == "state":
        root = ctx.state
    elif source == "shared_state":
        root = ctx.shared_state
    elif source == "matches":
        root = ctx.matches
    elif source == "context":
        root = ctx
    return _resolve_path(root, path)


def _resolve_path(root: Any, path: str | Sequence[str]) -> Any:
    parts = path.split(".") if isinstance(path, str) else list(path)
    current = root
    for part in parts:
        key = str(part)
        if isinstance(current, Mapping):
            if key not in current:
                return _MISSING
            current = current[key]
            continue
        if isinstance(current, Sequence) and not isinstance(current, (str, bytes, bytearray)):
            try:
                current = current[int(key)]
                continue
            except (ValueError, IndexError):
                return _MISSING
        if not hasattr(current, key):
            return _MISSING
        current = getattr(current, key)
    return current


def _evaluate_condition(condition: FieldCondition, value: Any) -> tuple[bool, RulePayload]:
    exists = value is not _MISSING
    if condition.op == FieldOp.EXISTS:
        ok = exists is bool(condition.value)
        return _condition_result(condition, value, ok)
    if not exists:
        return False, {}
    if condition.op == FieldOp.EQUALS:
        ok = value == condition.value
    elif condition.op == FieldOp.NOT_EQUALS:
        ok = value != condition.value
    elif condition.op == FieldOp.IN:
        ok = value in condition.value
    elif condition.op == FieldOp.CONTAINS:
        ok = condition.value in value
    elif condition.op == FieldOp.STARTSWITH:
        ok = str(value).startswith(condition.value)
    elif condition.op == FieldOp.ENDSWITH:
        ok = str(value).endswith(condition.value)
    elif condition.op == FieldOp.REGEX:
        compiled = _compile_pattern(condition.value, flags=condition.flags)
        match = compiled.search(str(value))
        if match is None:
            return False, {}
        payload: RulePayload = {"regex": match, **match.groupdict()}
        if condition.capture_as:
            payload[condition.capture_as] = value
        return True, payload
    elif condition.op == FieldOp.GT:
        ok = value > condition.value
    elif condition.op == FieldOp.GE:
        ok = value >= condition.value
    elif condition.op == FieldOp.LT:
        ok = value < condition.value
    elif condition.op == FieldOp.LE:
        ok = value <= condition.value
    return _condition_result(condition, value, ok)


def _condition_result(condition: FieldCondition, value: Any, ok: bool) -> tuple[bool, RulePayload]:
    if not ok:
        return False, {}
    if condition.capture_as is None or value is _MISSING:
        return True, {}
    return True, {condition.capture_as: value}


def _compile_pattern(pattern: str | re.Pattern[str], *, flags: int = 0) -> re.Pattern[str]:
    if isinstance(pattern, re.Pattern):
        return pattern
    return re.compile(pattern, flags)


def _message_type(event: Any) -> str | None:
    raw = getattr(event, "raw", {})
    if isinstance(raw, dict):
        value = raw.get("message_type")
        return None if value is None else str(value)
    return None


def _normalize_rule_result(value: Any) -> tuple[bool, RulePayload]:
    if isinstance(value, tuple) and len(value) == 2:
        ok, payload = value
        return bool(ok), dict(payload or {})
    if isinstance(value, Mapping):
        return True, dict(value)
    if value is None:
        return False, {}
    return bool(value), {}


if TYPE_CHECKING:
    from .runtime import Runtime
    from .context import Context
