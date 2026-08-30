"""Fail-closed Tool execution for the provisional Harness Environment."""

from __future__ import annotations

import asyncio
import inspect
import math
import secrets
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Protocol, TypeVar, cast

from ._model import (
    Action,
    FrozenJsonValue,
    Observation,
    Task,
    Transition,
    _configuration_hash,
    _freeze_json,
    _frozen_object,
)

CONTROLLED_EXECUTION_VERSION = "1"
TOOL_SPEC_VERSION = "1"
TOOL_SCHEMA_VERSION = "iamai-json-schema-subset-1"

_SCHEMA_TYPES = {"null", "boolean", "integer", "number", "string", "array", "object"}
_SCHEMA_KEYS = {
    "type",
    "enum",
    "properties",
    "required",
    "additionalProperties",
    "items",
}

_T = TypeVar("_T")
_NO_LATE_RESULT = object()


class _ControlledDeadlineExceeded(Exception):
    def __init__(self, late_result: object = _NO_LATE_RESULT) -> None:
        super().__init__("controlled execution deadline exceeded")
        self.late_result = late_result


def _caller_cancellation_pending() -> bool:
    current = asyncio.current_task()
    return current is not None and current.cancelling() > 0


async def _await_before_deadline(
    awaitable_factory: Callable[[], Awaitable[_T]],
    *,
    deadline: float,
) -> _T:
    loop = asyncio.get_running_loop()
    if loop.time() >= deadline:
        raise _ControlledDeadlineExceeded
    awaitable = awaitable_factory()
    if loop.time() >= deadline:
        close = getattr(awaitable, "close", None)
        if callable(close):
            close()
        elif isinstance(awaitable, asyncio.Future):
            awaitable.cancel()
        raise _ControlledDeadlineExceeded
    task = asyncio.ensure_future(awaitable)
    try:
        done, _ = await asyncio.wait(
            (task,),
            timeout=max(0.0, deadline - loop.time()),
        )
    except asyncio.CancelledError:
        task.cancel()
        try:
            await task
        except BaseException:
            pass
        raise
    if task in done:
        try:
            result = task.result()
        except BaseException:
            if _caller_cancellation_pending():
                raise asyncio.CancelledError from None
            if loop.time() >= deadline:
                raise _ControlledDeadlineExceeded from None
            raise
        if _caller_cancellation_pending():
            raise asyncio.CancelledError
        if loop.time() >= deadline:
            raise _ControlledDeadlineExceeded(result)
        return result

    task.cancel()
    try:
        late_result = await task
    except asyncio.CancelledError:
        if _caller_cancellation_pending():
            task.cancel()
            try:
                await task
            except BaseException:
                pass
            raise
        raise _ControlledDeadlineExceeded from None
    except BaseException:
        if _caller_cancellation_pending():
            raise asyncio.CancelledError from None
        raise _ControlledDeadlineExceeded from None
    if _caller_cancellation_pending():
        raise asyncio.CancelledError
    raise _ControlledDeadlineExceeded(late_result)


def _json_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    frozen = _freeze_json(value, path=f"$.{field_name}")
    if not isinstance(frozen, str):
        raise AssertionError("JSON string did not remain a string")
    return frozen


def _required_text(value: object, *, field_name: str) -> str:
    text = _json_text(value, field_name=field_name)
    if not text.strip():
        raise ValueError(f"{field_name} cannot be empty")
    return text


def _non_negative_integer(value: object, *, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} cannot be negative")
    frozen = _freeze_json(value, path=f"$.{field_name}")
    if isinstance(frozen, bool) or not isinstance(frozen, int):
        raise AssertionError("JSON integer did not remain an integer")
    return frozen


def _canonical_names(values: Sequence[str], *, field_name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be an array of strings")
    names: list[str] = []
    for value in values:
        names.append(_required_text(value, field_name=field_name))
    if len(names) != len(set(names)):
        raise ValueError(f"{field_name} cannot contain duplicates")
    return tuple(sorted(names))


def _validate_schema_definition(schema: object, *, path: str = "$") -> None:
    if not isinstance(schema, Mapping):
        raise TypeError(f"{path} schema must be an object")
    unsupported = set(schema) - _SCHEMA_KEYS
    if unsupported:
        keyword = sorted(unsupported)[0]
        raise ValueError(f"{path} schema keyword is unsupported: {keyword}")
    schema_type = schema.get("type")
    if not isinstance(schema_type, str) or schema_type not in _SCHEMA_TYPES:
        raise ValueError(f"{path}.type must name one supported JSON type")

    enum = schema.get("enum")
    if enum is not None:
        if isinstance(enum, (str, bytes)) or not isinstance(enum, Sequence) or not enum:
            raise ValueError(f"{path}.enum must be a non-empty array")
        _freeze_json(enum, path=f"{path}.enum")

    object_keywords = {"properties", "required", "additionalProperties"}
    if schema_type != "object" and object_keywords.intersection(schema):
        raise ValueError(f"{path} object keywords require type=object")
    if schema_type == "object":
        properties = schema.get("properties", {})
        if not isinstance(properties, Mapping):
            raise TypeError(f"{path}.properties must be an object")
        for name, child in properties.items():
            _required_text(name, field_name=f"{path}.properties key")
            _validate_schema_definition(child, path=f"{path}.properties.{name}")
        required = schema.get("required", ())
        if isinstance(required, (str, bytes)) or not isinstance(required, Sequence):
            raise TypeError(f"{path}.required must be an array")
        required_names = _canonical_names(required, field_name=f"{path}.required item")
        unknown_required = set(required_names) - set(properties)
        if unknown_required:
            name = sorted(unknown_required)[0]
            raise ValueError(f"{path}.required names an undeclared property: {name}")
        additional = schema.get("additionalProperties", True)
        if not isinstance(additional, bool):
            raise TypeError(f"{path}.additionalProperties must be a bool")

    if schema_type != "array" and "items" in schema:
        raise ValueError(f"{path}.items requires type=array")
    if schema_type == "array" and "items" in schema:
        _validate_schema_definition(schema["items"], path=f"{path}.items")


def _same_json_value(left: FrozenJsonValue, right: FrozenJsonValue) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    if isinstance(left, Mapping) or isinstance(right, Mapping):
        if not isinstance(left, Mapping) or not isinstance(right, Mapping):
            return False
        return set(left) == set(right) and all(
            _same_json_value(left[key], right[key]) for key in left
        )
    if isinstance(left, tuple) or isinstance(right, tuple):
        if not isinstance(left, tuple) or not isinstance(right, tuple):
            return False
        return len(left) == len(right) and all(
            _same_json_value(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    return type(left) is type(right) and left == right


def _validate_schema_instance(
    value: FrozenJsonValue,
    schema: Mapping[str, FrozenJsonValue],
    *,
    path: str = "$",
) -> None:
    schema_type = schema["type"]
    valid = (
        schema_type == "null"
        and value is None
        or schema_type == "boolean"
        and isinstance(value, bool)
        or schema_type == "integer"
        and isinstance(value, int)
        and not isinstance(value, bool)
        or schema_type == "number"
        and isinstance(value, (int, float))
        and not isinstance(value, bool)
        or schema_type == "string"
        and isinstance(value, str)
        or schema_type == "array"
        and isinstance(value, tuple)
        or schema_type == "object"
        and isinstance(value, Mapping)
    )
    if not valid:
        raise ValueError(f"{path} must have JSON type {schema_type}")

    enum = schema.get("enum")
    if isinstance(enum, tuple) and not any(_same_json_value(value, item) for item in enum):
        raise ValueError(f"{path} is not one of the declared enum values")

    if schema_type == "object":
        if not isinstance(value, Mapping):
            raise AssertionError("validated object is not a mapping")
        properties = schema.get("properties", MappingProxyType({}))
        if not isinstance(properties, Mapping):
            raise AssertionError("validated schema properties are not a mapping")
        required = schema.get("required", ())
        if not isinstance(required, tuple):
            raise AssertionError("validated schema required is not a tuple")
        for name in required:
            if not isinstance(name, str):
                raise AssertionError("validated schema required item is not a string")
            if name not in value:
                raise ValueError(f"{path} is missing required property: {name}")
        if schema.get("additionalProperties", True) is False:
            extra = set(value) - set(properties)
            if extra:
                name = sorted(extra)[0]
                raise ValueError(f"{path} contains undeclared property: {name}")
        for name, item in value.items():
            child = properties.get(name)
            if child is not None:
                if not isinstance(child, Mapping):
                    raise AssertionError("validated child schema is not a mapping")
                _validate_schema_instance(item, child, path=f"{path}.{name}")

    if schema_type == "array" and "items" in schema:
        if not isinstance(value, tuple):
            raise AssertionError("validated array is not a tuple")
        items = schema["items"]
        if not isinstance(items, Mapping):
            raise AssertionError("validated array schema items are not a mapping")
        for index, item in enumerate(value):
            _validate_schema_instance(item, items, path=f"{path}[{index}]")


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """Frozen declaration used to validate and budget one Harness Tool."""

    name: str
    version: str
    input_schema: Mapping[str, object]
    permission_name: str
    description: str = ""
    runtime_capabilities: tuple[str, ...] = ()
    requires_approval: bool = False
    reserved_tokens: int = 0
    reserved_cost_microunits: int = 0
    spec_hash: str = field(init=False)
    _configuration: Mapping[str, FrozenJsonValue] = field(
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        name = _required_text(self.name, field_name="ToolSpec name")
        version = _required_text(self.version, field_name="ToolSpec version")
        permission_name = _required_text(
            self.permission_name,
            field_name="ToolSpec permission_name",
        )
        if not isinstance(self.description, str):
            raise TypeError("ToolSpec description must be a string")
        if not isinstance(self.requires_approval, bool):
            raise TypeError("ToolSpec requires_approval must be a bool")
        capabilities = _canonical_names(
            self.runtime_capabilities,
            field_name="ToolSpec runtime_capabilities",
        )
        reserved_tokens = _non_negative_integer(
            self.reserved_tokens,
            field_name="ToolSpec reserved_tokens",
        )
        reserved_cost = _non_negative_integer(
            self.reserved_cost_microunits,
            field_name="ToolSpec reserved_cost_microunits",
        )
        _validate_schema_definition(self.input_schema)
        frozen_schema = _freeze_json(self.input_schema, path="$.tool.input_schema")
        if not isinstance(frozen_schema, Mapping):
            raise AssertionError("Tool schema did not freeze to an object")
        if frozen_schema.get("type") != "object":
            raise ValueError("ToolSpec input_schema must have type=object")
        configuration = _frozen_object(
            tool_spec_version=TOOL_SPEC_VERSION,
            name=name,
            version=version,
            description=self.description,
            input_schema_version=TOOL_SCHEMA_VERSION,
            input_schema=frozen_schema,
            permission_name=permission_name,
            runtime_capabilities=capabilities,
            requires_approval=self.requires_approval,
            reserved_tokens=reserved_tokens,
            reserved_cost_microunits=reserved_cost,
        )
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "version", version)
        object.__setattr__(self, "permission_name", permission_name)
        object.__setattr__(self, "runtime_capabilities", capabilities)
        object.__setattr__(self, "reserved_tokens", reserved_tokens)
        object.__setattr__(self, "reserved_cost_microunits", reserved_cost)
        object.__setattr__(self, "input_schema", frozen_schema)
        object.__setattr__(self, "_configuration", configuration)
        object.__setattr__(self, "spec_hash", _configuration_hash(configuration))

    @property
    def configuration(self) -> Mapping[str, FrozenJsonValue]:
        """Return the declaration covered by ``spec_hash``."""
        return self._configuration

    def validate(self, arguments: Mapping[str, FrozenJsonValue]) -> None:
        """Validate frozen arguments without coercion or applying defaults."""
        _validate_schema_instance(
            arguments,
            cast(Mapping[str, FrozenJsonValue], self.input_schema),
        )


@dataclass(frozen=True, slots=True)
class ToolResult:
    """JSON output and trusted usage reported by a conforming Tool adapter."""

    output: FrozenJsonValue
    tokens: int = 0
    cost_microunits: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "output",
            _freeze_json(
                self.output,
                path="$.tool.output",
                _depth=3,
            ),
        )
        object.__setattr__(
            self,
            "tokens",
            _non_negative_integer(self.tokens, field_name="ToolResult tokens"),
        )
        object.__setattr__(
            self,
            "cost_microunits",
            _non_negative_integer(
                self.cost_microunits,
                field_name="ToolResult cost_microunits",
            ),
        )


ToolHandler = Callable[[Mapping[str, FrozenJsonValue]], Awaitable[ToolResult]]


class Tool:
    """Bind one frozen Tool declaration to an asynchronous implementation."""

    __slots__ = ("_handler", "_spec")

    def __init__(self, spec: ToolSpec, handler: ToolHandler) -> None:
        if not isinstance(spec, ToolSpec):
            raise TypeError("Tool spec must be a ToolSpec")
        if not callable(handler):
            raise TypeError("Tool handler must be callable")
        self._spec = spec
        self._handler = handler

    @property
    def spec(self) -> ToolSpec:
        return self._spec

    async def _invoke(self, arguments: Mapping[str, FrozenJsonValue]) -> ToolResult:
        pending = self._handler(arguments)
        if not inspect.isawaitable(pending):
            raise TypeError("Tool handler must return an awaitable ToolResult")
        result = await pending
        if not isinstance(result, ToolResult):
            raise TypeError("Tool handler must return ToolResult")
        return result


@dataclass(frozen=True, slots=True)
class ExecutionPolicy:
    """Versioned, static, default-deny policy for declared Harness Tools."""

    version: str
    allowed_tools: tuple[str, ...] = ()
    allowed_permissions: tuple[str, ...] = ()
    allowed_runtime_capabilities: tuple[str, ...] = ()
    approval_required_tools: tuple[str, ...] = ()
    approval_required_permissions: tuple[str, ...] = ()
    policy_hash: str = field(init=False)
    _configuration: Mapping[str, FrozenJsonValue] = field(
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        version = _required_text(self.version, field_name="ExecutionPolicy version")
        values = {
            name: _canonical_names(getattr(self, name), field_name=f"ExecutionPolicy {name}")
            for name in (
                "allowed_tools",
                "allowed_permissions",
                "allowed_runtime_capabilities",
                "approval_required_tools",
                "approval_required_permissions",
            )
        }
        configuration = _frozen_object(version=version, **values)
        object.__setattr__(self, "version", version)
        for name, value in values.items():
            object.__setattr__(self, name, value)
        object.__setattr__(self, "_configuration", configuration)
        object.__setattr__(self, "policy_hash", _configuration_hash(configuration))

    @property
    def configuration(self) -> Mapping[str, FrozenJsonValue]:
        return self._configuration

    def _allows(self, spec: ToolSpec) -> bool:
        return (
            spec.name in self.allowed_tools
            and spec.permission_name in self.allowed_permissions
            and set(spec.runtime_capabilities).issubset(
                self.allowed_runtime_capabilities
            )
        )

    def _requires_approval(self, spec: ToolSpec) -> bool:
        return (
            spec.requires_approval
            or spec.name in self.approval_required_tools
            or spec.permission_name in self.approval_required_permissions
        )


@dataclass(frozen=True, slots=True)
class ExecutionBudget:
    """Run-scoped Tool limits plus a per-attempt cooperative timeout."""

    max_tool_calls: int
    max_tokens: int
    max_cost_microunits: int
    tool_timeout_seconds: float
    currency: str
    pricing_version: str
    budget_hash: str = field(init=False)
    _configuration: Mapping[str, FrozenJsonValue] = field(
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "max_tool_calls",
            _non_negative_integer(self.max_tool_calls, field_name="ExecutionBudget max_tool_calls"),
        )
        object.__setattr__(
            self,
            "max_tokens",
            _non_negative_integer(self.max_tokens, field_name="ExecutionBudget max_tokens"),
        )
        object.__setattr__(
            self,
            "max_cost_microunits",
            _non_negative_integer(
                self.max_cost_microunits,
                field_name="ExecutionBudget max_cost_microunits",
            ),
        )
        if isinstance(self.tool_timeout_seconds, bool) or not isinstance(
            self.tool_timeout_seconds, (int, float)
        ):
            raise TypeError("ExecutionBudget tool_timeout_seconds must be a number")
        timeout = float(self.tool_timeout_seconds)
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("ExecutionBudget tool_timeout_seconds must be finite and positive")
        object.__setattr__(self, "tool_timeout_seconds", timeout)
        object.__setattr__(
            self,
            "currency",
            _required_text(self.currency, field_name="ExecutionBudget currency"),
        )
        object.__setattr__(
            self,
            "pricing_version",
            _required_text(
                self.pricing_version,
                field_name="ExecutionBudget pricing_version",
            ),
        )
        configuration = _frozen_object(
            max_tool_calls=self.max_tool_calls,
            max_tokens=self.max_tokens,
            max_cost_microunits=self.max_cost_microunits,
            tool_timeout_seconds=self.tool_timeout_seconds,
            currency=self.currency,
            pricing_version=self.pricing_version,
        )
        object.__setattr__(self, "_configuration", configuration)
        object.__setattr__(self, "budget_hash", _configuration_hash(configuration))

    @property
    def configuration(self) -> Mapping[str, FrozenJsonValue]:
        return self._configuration


@dataclass(frozen=True, slots=True)
class ApprovalRequest:
    """Immutable approval request bound to exactly one Tool invocation."""

    trial_id: str
    call_id: str
    request_nonce: str
    action_index: int
    tool_name: str
    tool_version: str
    tool_spec_hash: str
    arguments: Mapping[str, FrozenJsonValue]
    policy_hash: str
    budget_hash: str
    approver_hash: str | None
    reserved_tokens: int
    reserved_cost_microunits: int
    request_hash: str = field(init=False)

    def __post_init__(self) -> None:
        for name in (
            "trial_id",
            "call_id",
            "request_nonce",
            "tool_name",
            "tool_version",
            "tool_spec_hash",
            "policy_hash",
            "budget_hash",
        ):
            object.__setattr__(
                self,
                name,
                _required_text(getattr(self, name), field_name=f"ApprovalRequest {name}"),
            )
        action_index = _non_negative_integer(
            self.action_index,
            field_name="ApprovalRequest action_index",
        )
        arguments = _freeze_json(self.arguments, path="$.approval.arguments")
        if not isinstance(arguments, Mapping):
            raise TypeError("ApprovalRequest arguments must be an object")
        reserved_tokens = _non_negative_integer(
            self.reserved_tokens,
            field_name="ApprovalRequest reserved_tokens",
        )
        reserved_cost = _non_negative_integer(
            self.reserved_cost_microunits,
            field_name="ApprovalRequest reserved_cost_microunits",
        )
        approver_hash = self.approver_hash
        if approver_hash is not None:
            approver_hash = _required_text(
                approver_hash,
                field_name="ApprovalRequest approver_hash",
            )
        payload = _frozen_object(
            trial_id=self.trial_id,
            call_id=self.call_id,
            request_nonce=self.request_nonce,
            action_index=action_index,
            tool_name=self.tool_name,
            tool_version=self.tool_version,
            tool_spec_hash=self.tool_spec_hash,
            arguments=arguments,
            policy_hash=self.policy_hash,
            budget_hash=self.budget_hash,
            approver_hash=approver_hash,
            reserved_tokens=reserved_tokens,
            reserved_cost_microunits=reserved_cost,
        )
        object.__setattr__(self, "action_index", action_index)
        object.__setattr__(self, "arguments", arguments)
        object.__setattr__(self, "reserved_tokens", reserved_tokens)
        object.__setattr__(self, "reserved_cost_microunits", reserved_cost)
        object.__setattr__(self, "approver_hash", approver_hash)
        object.__setattr__(self, "request_hash", _configuration_hash(payload))


@dataclass(frozen=True, slots=True)
class ApprovalDecision:
    """An Approver decision content-hash bound to one ApprovalRequest."""

    request_hash: str
    approved: bool
    reason: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "request_hash",
            _required_text(
                self.request_hash,
                field_name="ApprovalDecision request_hash",
            ),
        )
        if not isinstance(self.approved, bool):
            raise TypeError("ApprovalDecision approved must be a bool")
        object.__setattr__(
            self,
            "reason",
            _json_text(
                self.reason,
                field_name="ApprovalDecision reason",
            ),
        )

    @classmethod
    def approve(
        cls,
        request: ApprovalRequest,
        *,
        reason: str = "",
    ) -> ApprovalDecision:
        return cls(request.request_hash, True, reason)

    @classmethod
    def deny(
        cls,
        request: ApprovalRequest,
        *,
        reason: str = "",
    ) -> ApprovalDecision:
        return cls(request.request_hash, False, reason)


class Approver(Protocol):
    """Declared asynchronous decision source for exact ApprovalRequests."""

    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    @property
    def configuration(self) -> Mapping[str, object]: ...

    async def decide(self, request: ApprovalRequest) -> ApprovalDecision: ...


class ToolCallStatus(str, Enum):
    """Harness-visible outcome of one controlled Tool invocation attempt."""

    SUCCEEDED = "succeeded"
    INVALID = "invalid"
    DENIED = "denied"
    BUDGET_EXHAUSTED = "budget_exhausted"
    TIMED_OUT = "timed_out"
    FAILED = "failed"
    CANCELLED = "cancelled"


def _approval_evidence(
    status: str,
    *,
    approver: str | None = None,
    approver_version: str | None = None,
    reason: str = "",
) -> Mapping[str, FrozenJsonValue]:
    return _frozen_object(
        status=status,
        approver=approver,
        approver_version=approver_version,
        reason=reason,
    )


class ControlledToolEnvironment:
    """Environment that validates, authorizes, budgets, and audits async Tools."""

    def __init__(
        self,
        *,
        tools: Sequence[Tool],
        policy: ExecutionPolicy,
        budget: ExecutionBudget,
        name: str,
        version: str,
        approver: Approver | None = None,
    ) -> None:
        self._name = _required_text(name, field_name="ControlledToolEnvironment name")
        self._version = _required_text(
            version,
            field_name="ControlledToolEnvironment version",
        )
        if not isinstance(policy, ExecutionPolicy):
            raise TypeError("ControlledToolEnvironment policy must be ExecutionPolicy")
        if not isinstance(budget, ExecutionBudget):
            raise TypeError("ControlledToolEnvironment budget must be ExecutionBudget")
        declared_tools: dict[str, Tool] = {}
        for tool in tools:
            if not isinstance(tool, Tool):
                raise TypeError("ControlledToolEnvironment tools must contain Tool values")
            if tool.spec.name in declared_tools:
                raise ValueError(f"duplicate Tool name: {tool.spec.name}")
            declared_tools[tool.spec.name] = tool
        declared_tools = dict(sorted(declared_tools.items()))
        if not set(policy.allowed_tools).issubset(declared_tools):
            raise ValueError("ExecutionPolicy allowed_tools must name declared Tools")
        if not set(policy.approval_required_tools).issubset(policy.allowed_tools):
            raise ValueError(
                "ExecutionPolicy approval_required_tools must be allowed Tools"
            )
        if not set(policy.approval_required_permissions).issubset(
            policy.allowed_permissions
        ):
            raise ValueError(
                "ExecutionPolicy approval_required_permissions must be allowed permissions"
            )
        self._tools = MappingProxyType(declared_tools)
        self._policy = policy
        self._budget = budget
        self._approver = approver
        self._approver_name: str | None = None
        self._approver_version: str | None = None
        self._approver_configuration: Mapping[str, FrozenJsonValue] | None = None
        self._approver_hash: str | None = None
        approver_declaration: Mapping[str, FrozenJsonValue] | None = None
        if approver is not None:
            approver_name = _required_text(
                getattr(approver, "name", None),
                field_name="Approver name",
            )
            approver_version = _required_text(
                getattr(approver, "version", None),
                field_name="Approver version",
            )
            approver_config = getattr(approver, "configuration", None)
            if not isinstance(approver_config, Mapping):
                raise TypeError("Approver configuration must be an object")
            approver_declaration = _frozen_object(
                name=approver_name,
                version=approver_version,
                config=approver_config,
            )
            declared_config = approver_declaration["config"]
            if not isinstance(declared_config, Mapping):
                raise AssertionError("Approver config did not freeze to an object")
            self._approver_name = approver_name
            self._approver_version = approver_version
            self._approver_configuration = declared_config
            self._approver_hash = _configuration_hash(approver_declaration)
        self._configuration = _frozen_object(
            kind="controlled_tool",
            controlled_execution_version=CONTROLLED_EXECUTION_VERSION,
            schema_version=TOOL_SCHEMA_VERSION,
            tools=[tool.spec.configuration for tool in declared_tools.values()],
            policy=policy.configuration,
            policy_hash=policy.policy_hash,
            budget=budget.configuration,
            budget_hash=budget.budget_hash,
            approver=approver_declaration,
            approver_hash=self._approver_hash,
            single_use=True,
        )
        self._calls = 0
        self._tokens = 0
        self._cost_microunits = 0
        self._budget_poisoned = False
        self._request_nonces: dict[str, str] = {}
        self._records: list[tuple[str, Mapping[str, FrozenJsonValue]]] = []
        self._direct_trial_id: str | None = None
        self._reset_generation = 0
        self._has_reset = False
        self._bound_trial_id: str | None = None
        self._next_action_index = 0
        self._terminated = False
        self._lock = asyncio.Lock()

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def configuration(self) -> Mapping[str, FrozenJsonValue]:
        return self._configuration

    def _bind_trial(self, trial_id: str) -> None:
        if self._bound_trial_id is not None:
            raise RuntimeError(
                "ControlledToolEnvironment can be bound to only one Trial"
            )
        self._bound_trial_id = _required_text(
            trial_id,
            field_name="ControlledToolEnvironment trial_id",
        )

    async def reset(self, task: Task, *, seed: int) -> Observation:
        """Reset run-local counters and expose the Task input."""
        if self._has_reset:
            raise RuntimeError(
                "ControlledToolEnvironment is single-use; create one instance per Trial"
            )
        if self._records:
            raise RuntimeError("controlled Tool audit records were not drained")
        self._has_reset = True
        self._calls = 0
        self._tokens = 0
        self._cost_microunits = 0
        self._budget_poisoned = False
        self._request_nonces.clear()
        self._next_action_index = 0
        self._terminated = False
        self._reset_generation += 1
        self._direct_trial_id = (
            f"direct:{task.id}:{seed}:{self._reset_generation}"
        )
        return Observation(task.input)

    async def step(self, action: Action, *, seed: int, action_index: int) -> Transition:
        """Apply an Action directly without retaining Trial-only audit evidence."""
        if self._direct_trial_id is None:
            raise RuntimeError("ControlledToolEnvironment must be reset before step")
        try:
            return await self._step_with_audit(
                action,
                trial_id=self._direct_trial_id,
                seed=seed,
                action_index=action_index,
            )
        finally:
            self._drain_trajectory_records()

    async def _step_with_audit(
        self,
        action: Action,
        *,
        trial_id: str,
        seed: int,
        action_index: int,
    ) -> Transition:
        del seed
        call_id: str | None = None
        try:
            async with self._lock:
                if not self._has_reset:
                    raise RuntimeError(
                        "ControlledToolEnvironment must be reset before step"
                    )
                if self._terminated:
                    raise RuntimeError(
                        "ControlledToolEnvironment has already terminated"
                    )
                if self._bound_trial_id is not None and trial_id != self._bound_trial_id:
                    raise RuntimeError(
                        "ControlledToolEnvironment Trial binding does not match"
                    )
                if action_index != self._next_action_index:
                    raise RuntimeError(
                        "ControlledToolEnvironment action_index must be contiguous from zero"
                    )
                self._next_action_index += 1
                call_id = f"tool-{action_index}"
                if action.is_final:
                    self._terminated = True
                    return Transition(
                        observation=Observation(action.payload),
                        terminated=True,
                        output=action.payload,
                    )
                return await self._invoke(
                    action,
                    trial_id=trial_id,
                    call_id=call_id,
                    action_index=action_index,
                )
        except asyncio.CancelledError:
            if (
                call_id is not None
                and not action.is_final
                and not self._has_outcome(call_id)
            ):
                tool = self._tools.get(action.name)
                self._record_outcome(
                    call_id=call_id,
                    tool_name=action.name,
                    status=ToolCallStatus.CANCELLED,
                    tool=tool,
                    request_hash=None,
                    approval_required=(
                        False
                        if tool is None
                        else self._policy._requires_approval(tool.spec)
                    ),
                    usage_tokens=0,
                    usage_cost=0,
                    charged_tokens=0,
                    charged_cost=0,
                    error_code="cancelled",
                    message="controlled Tool call was cancelled",
                    approval=None,
                )
            raise

    def _has_outcome(self, call_id: str) -> bool:
        return any(record[1].get("call_id") == call_id for record in self._records)

    def _drain_trajectory_records(
        self,
    ) -> tuple[tuple[str, Mapping[str, FrozenJsonValue]], ...]:
        records = tuple(self._records)
        self._records.clear()
        return records

    def _request(
        self,
        *,
        trial_id: str,
        call_id: str,
        action_index: int,
        tool: Tool,
        arguments: Mapping[str, FrozenJsonValue],
    ) -> ApprovalRequest:
        request = ApprovalRequest(
            trial_id=trial_id,
            call_id=call_id,
            request_nonce=secrets.token_hex(16),
            action_index=action_index,
            tool_name=tool.spec.name,
            tool_version=tool.spec.version,
            tool_spec_hash=tool.spec.spec_hash,
            arguments=arguments,
            policy_hash=self._policy.policy_hash,
            budget_hash=self._budget.budget_hash,
            approver_hash=self._approver_hash,
            reserved_tokens=tool.spec.reserved_tokens,
            reserved_cost_microunits=tool.spec.reserved_cost_microunits,
        )
        self._request_nonces[request.request_hash] = request.request_nonce
        return request

    def _approver_declaration_is_current(self) -> bool:
        if (
            self._approver is None
            or self._approver_name is None
            or self._approver_version is None
            or self._approver_configuration is None
            or self._approver_hash is None
        ):
            return False
        try:
            live_name = _required_text(
                self._approver.name,
                field_name="Approver name",
            )
            live_version = _required_text(
                self._approver.version,
                field_name="Approver version",
            )
            live_configuration = _freeze_json(
                self._approver.configuration,
                path="$.approver.configuration",
            )
            if not isinstance(live_configuration, Mapping):
                return False
            live_declaration = _frozen_object(
                name=live_name,
                version=live_version,
                config=live_configuration,
            )
            return _configuration_hash(live_declaration) == self._approver_hash
        except BaseException:
            return False

    async def _invoke(
        self,
        action: Action,
        *,
        trial_id: str,
        call_id: str,
        action_index: int,
    ) -> Transition:
        tool = self._tools.get(action.name)
        approval_required = (
            False if tool is None else self._policy._requires_approval(tool.spec)
        )
        if self._calls >= self._budget.max_tool_calls:
            return self._finish(
                call_id=call_id,
                tool_name=action.name,
                status=ToolCallStatus.BUDGET_EXHAUSTED,
                tool=tool,
                request_hash=None,
                approval_required=approval_required,
                error_code="call_budget_exhausted",
                message="controlled Tool call budget is exhausted",
            )
        self._calls += 1
        if tool is None:
            return self._finish(
                call_id=call_id,
                tool_name=action.name,
                status=ToolCallStatus.DENIED,
                tool=None,
                request_hash=None,
                approval_required=False,
                error_code="unknown_tool",
                message=f"Tool is not declared: {action.name}",
            )
        if self._budget_poisoned:
            return self._finish(
                call_id=call_id,
                tool_name=action.name,
                status=ToolCallStatus.BUDGET_EXHAUSTED,
                tool=tool,
                request_hash=None,
                approval_required=approval_required,
                error_code="usage_budget_exhausted",
                message="execution budget is exhausted after a Tool contract violation",
            )
        if not isinstance(action.payload, Mapping):
            return self._finish(
                call_id=call_id,
                tool_name=action.name,
                status=ToolCallStatus.INVALID,
                tool=tool,
                request_hash=None,
                approval_required=approval_required,
                error_code="invalid_arguments",
                message="Tool arguments must be an object",
            )
        arguments = action.payload
        try:
            tool.spec.validate(arguments)
        except (TypeError, ValueError) as error:
            return self._finish(
                call_id=call_id,
                tool_name=action.name,
                status=ToolCallStatus.INVALID,
                tool=tool,
                request_hash=None,
                approval_required=approval_required,
                error_code="invalid_arguments",
                message=str(error),
            )
        request = self._request(
            trial_id=trial_id,
            call_id=call_id,
            action_index=action_index,
            tool=tool,
            arguments=arguments,
        )
        if not self._policy._allows(tool.spec):
            return self._finish(
                call_id=call_id,
                tool_name=action.name,
                status=ToolCallStatus.DENIED,
                tool=tool,
                request_hash=request.request_hash,
                approval_required=approval_required,
                error_code="policy_denied",
                message="ExecutionPolicy denied the Tool",
            )
        if (
            self._tokens + tool.spec.reserved_tokens > self._budget.max_tokens
            or self._cost_microunits + tool.spec.reserved_cost_microunits
            > self._budget.max_cost_microunits
        ):
            return self._finish(
                call_id=call_id,
                tool_name=action.name,
                status=ToolCallStatus.BUDGET_EXHAUSTED,
                tool=tool,
                request_hash=request.request_hash,
                approval_required=approval_required,
                error_code="usage_budget_exhausted",
                message="Tool reservation exceeds the remaining execution budget",
            )

        loop = asyncio.get_running_loop()
        deadline = loop.time() + self._budget.tool_timeout_seconds
        approval: Mapping[str, FrozenJsonValue] | None = None
        if approval_required:
            if self._approver is None:
                return self._finish(
                    call_id=call_id,
                    tool_name=action.name,
                    status=ToolCallStatus.DENIED,
                    tool=tool,
                    request_hash=request.request_hash,
                    approval_required=True,
                    approval=_approval_evidence("missing"),
                    error_code="approval_missing",
                    message="Tool requires an Approver",
                )
            approver = self._approver
            if not self._approver_declaration_is_current():
                return self._finish(
                    call_id=call_id,
                    tool_name=action.name,
                    status=ToolCallStatus.DENIED,
                    tool=tool,
                    request_hash=request.request_hash,
                    approval_required=True,
                    approval=_approval_evidence("invalid"),
                    error_code="approval_drift",
                    message="Approver declaration drifted before execution",
                )
            try:
                decision: object = await _await_before_deadline(
                    lambda: approver.decide(request),
                    deadline=deadline,
                )
            except asyncio.CancelledError:
                current = asyncio.current_task()
                if current is None or current.cancelling() == 0:
                    return self._finish(
                        call_id=call_id,
                        tool_name=action.name,
                        status=ToolCallStatus.DENIED,
                        tool=tool,
                        request_hash=request.request_hash,
                        approval_required=True,
                        approval=_approval_evidence("failed"),
                        error_code="approval_failed",
                        message="Approver failed: CancelledError",
                    )
                self._record_outcome(
                    call_id=call_id,
                    tool_name=action.name,
                    status=ToolCallStatus.CANCELLED,
                    tool=tool,
                    request_hash=request.request_hash,
                    approval_required=True,
                    usage_tokens=0,
                    usage_cost=0,
                    charged_tokens=0,
                    charged_cost=0,
                    error_code="cancelled",
                    message="approval wait was cancelled",
                    approval=_approval_evidence("cancelled"),
                )
                raise
            except _ControlledDeadlineExceeded:
                return self._finish(
                    call_id=call_id,
                    tool_name=action.name,
                    status=ToolCallStatus.TIMED_OUT,
                    tool=tool,
                    request_hash=request.request_hash,
                    approval_required=True,
                    approval=_approval_evidence("timed_out"),
                    error_code="approval_timed_out",
                    message="approval exceeded the Tool timeout",
                )
            except BaseException as error:
                return self._finish(
                    call_id=call_id,
                    tool_name=action.name,
                    status=ToolCallStatus.DENIED,
                    tool=tool,
                    request_hash=request.request_hash,
                    approval_required=True,
                    approval=_approval_evidence("failed"),
                    error_code="approval_failed",
                    message=f"Approver failed: {type(error).__name__}",
                )
            if loop.time() >= deadline:
                return self._finish(
                    call_id=call_id,
                    tool_name=action.name,
                    status=ToolCallStatus.TIMED_OUT,
                    tool=tool,
                    request_hash=request.request_hash,
                    approval_required=True,
                    approval=_approval_evidence("timed_out"),
                    error_code="approval_timed_out",
                    message="approval exceeded the Tool timeout",
                )
            if not self._approver_declaration_is_current():
                return self._finish(
                    call_id=call_id,
                    tool_name=action.name,
                    status=ToolCallStatus.DENIED,
                    tool=tool,
                    request_hash=request.request_hash,
                    approval_required=True,
                    approval=_approval_evidence("invalid"),
                    error_code="approval_drift",
                    message="Approver declaration drifted during approval",
                )
            if loop.time() >= deadline:
                return self._finish(
                    call_id=call_id,
                    tool_name=action.name,
                    status=ToolCallStatus.TIMED_OUT,
                    tool=tool,
                    request_hash=request.request_hash,
                    approval_required=True,
                    approval=_approval_evidence("timed_out"),
                    error_code="approval_timed_out",
                    message="approval exceeded the Tool timeout",
                )
            if not isinstance(decision, ApprovalDecision):
                return self._finish(
                    call_id=call_id,
                    tool_name=action.name,
                    status=ToolCallStatus.DENIED,
                    tool=tool,
                    request_hash=request.request_hash,
                    approval_required=True,
                    approval=_approval_evidence("invalid"),
                    error_code="approval_invalid",
                    message="Approver must return ApprovalDecision",
                )
            if decision.request_hash != request.request_hash:
                return self._finish(
                    call_id=call_id,
                    tool_name=action.name,
                    status=ToolCallStatus.DENIED,
                    tool=tool,
                    request_hash=request.request_hash,
                    approval_required=True,
                    approval=_approval_evidence("invalid"),
                    error_code="approval_mismatch",
                    message="ApprovalDecision does not match this request",
                )
            if not decision.approved:
                return self._finish(
                    call_id=call_id,
                    tool_name=action.name,
                    status=ToolCallStatus.DENIED,
                    tool=tool,
                    request_hash=request.request_hash,
                    approval_required=True,
                    approval=_approval_evidence(
                        "denied",
                        approver=self._approver_name,
                        approver_version=self._approver_version,
                        reason=decision.reason,
                    ),
                    error_code="approval_denied",
                    message=decision.reason or "Approver denied the Tool",
                )
            approval = _approval_evidence(
                "approved",
                approver=self._approver_name,
                approver_version=self._approver_version,
                reason=decision.reason,
            )

        reserved_tokens = tool.spec.reserved_tokens
        reserved_cost = tool.spec.reserved_cost_microunits
        self._tokens += reserved_tokens
        self._cost_microunits += reserved_cost
        try:
            result = await _await_before_deadline(
                lambda: tool._invoke(arguments),
                deadline=deadline,
            )
        except asyncio.CancelledError:
            current = asyncio.current_task()
            if current is None or current.cancelling() == 0:
                return self._finish(
                    call_id=call_id,
                    tool_name=action.name,
                    status=ToolCallStatus.FAILED,
                    tool=tool,
                    request_hash=request.request_hash,
                    approval_required=approval_required,
                    approval=approval,
                    charged_tokens=reserved_tokens,
                    charged_cost=reserved_cost,
                    error_code="tool_failed",
                    message="Tool failed: CancelledError",
                )
            self._record_outcome(
                call_id=call_id,
                tool_name=action.name,
                status=ToolCallStatus.CANCELLED,
                tool=tool,
                request_hash=request.request_hash,
                approval_required=approval_required,
                usage_tokens=0,
                usage_cost=0,
                charged_tokens=reserved_tokens,
                charged_cost=reserved_cost,
                error_code="cancelled",
                message="Tool wait was cancelled",
                approval=approval,
            )
            raise
        except _ControlledDeadlineExceeded as error:
            late_result = error.late_result
            if isinstance(late_result, ToolResult) and (
                late_result.tokens > reserved_tokens
                or late_result.cost_microunits > reserved_cost
            ):
                self._tokens += late_result.tokens - reserved_tokens
                self._cost_microunits += (
                    late_result.cost_microunits - reserved_cost
                )
                self._budget_poisoned = True
                return self._finish(
                    call_id=call_id,
                    tool_name=action.name,
                    status=ToolCallStatus.FAILED,
                    tool=tool,
                    request_hash=request.request_hash,
                    approval_required=approval_required,
                    approval=approval,
                    usage_tokens=late_result.tokens,
                    usage_cost=late_result.cost_microunits,
                    charged_tokens=late_result.tokens,
                    charged_cost=late_result.cost_microunits,
                    error_code="usage_exceeded_reservation",
                    message="Tool usage exceeded its declared reservation",
                )
            return self._finish(
                call_id=call_id,
                tool_name=action.name,
                status=ToolCallStatus.TIMED_OUT,
                tool=tool,
                request_hash=request.request_hash,
                approval_required=approval_required,
                approval=approval,
                charged_tokens=reserved_tokens,
                charged_cost=reserved_cost,
                error_code="tool_timed_out",
                message="Tool exceeded the execution timeout",
            )
        except BaseException as error:
            return self._finish(
                call_id=call_id,
                tool_name=action.name,
                status=ToolCallStatus.FAILED,
                tool=tool,
                request_hash=request.request_hash,
                approval_required=approval_required,
                approval=approval,
                charged_tokens=reserved_tokens,
                charged_cost=reserved_cost,
                error_code="tool_failed",
                message=f"Tool failed: {type(error).__name__}",
            )
        if (
            result.tokens > reserved_tokens
            or result.cost_microunits > reserved_cost
        ):
            self._tokens += result.tokens - reserved_tokens
            self._cost_microunits += result.cost_microunits - reserved_cost
            self._budget_poisoned = True
            return self._finish(
                call_id=call_id,
                tool_name=action.name,
                status=ToolCallStatus.FAILED,
                tool=tool,
                request_hash=request.request_hash,
                approval_required=approval_required,
                approval=approval,
                usage_tokens=result.tokens,
                usage_cost=result.cost_microunits,
                charged_tokens=result.tokens,
                charged_cost=result.cost_microunits,
                error_code="usage_exceeded_reservation",
                message="Tool usage exceeded its declared reservation",
            )
        if loop.time() >= deadline:
            return self._finish(
                call_id=call_id,
                tool_name=action.name,
                status=ToolCallStatus.TIMED_OUT,
                tool=tool,
                request_hash=request.request_hash,
                approval_required=approval_required,
                approval=approval,
                charged_tokens=reserved_tokens,
                charged_cost=reserved_cost,
                error_code="tool_timed_out",
                message="Tool exceeded the execution timeout",
            )
        self._tokens -= reserved_tokens - result.tokens
        self._cost_microunits -= reserved_cost - result.cost_microunits
        return self._finish(
            call_id=call_id,
            tool_name=action.name,
            status=ToolCallStatus.SUCCEEDED,
            tool=tool,
            request_hash=request.request_hash,
            approval_required=approval_required,
            approval=approval,
            output=result.output,
            usage_tokens=result.tokens,
            usage_cost=result.cost_microunits,
            charged_tokens=result.tokens,
            charged_cost=result.cost_microunits,
        )

    def _record_outcome(
        self,
        *,
        call_id: str,
        tool_name: str,
        status: ToolCallStatus,
        tool: Tool | None,
        request_hash: str | None,
        approval_required: bool,
        usage_tokens: int,
        usage_cost: int,
        charged_tokens: int,
        charged_cost: int,
        error_code: str | None,
        message: str | None,
        approval: Mapping[str, FrozenJsonValue] | None,
        observation_hash: str | None = None,
    ) -> None:
        if self._has_outcome(call_id):
            raise RuntimeError(f"duplicate controlled Tool outcome: {call_id}")
        if approval is None:
            approval = _approval_evidence(
                "not_obtained" if approval_required else "not_required"
            )
        request_nonce = (
            None
            if request_hash is None
            else self._request_nonces.pop(request_hash)
        )
        self._records.append(
            (
                "tool.call.outcome",
                _frozen_object(
                    call_id=call_id,
                    tool_name=tool_name,
                    tool_version=None if tool is None else tool.spec.version,
                    status=status.value,
                    tool_spec_hash=None if tool is None else tool.spec.spec_hash,
                    policy_hash=self._policy.policy_hash,
                    request_hash=request_hash,
                    request_nonce=request_nonce,
                    observation_hash=observation_hash,
                    approval_required=approval_required,
                    approval=approval,
                    usage={"tokens": usage_tokens, "cost_microunits": usage_cost},
                    budget_charged={
                        "tokens": charged_tokens,
                        "cost_microunits": charged_cost,
                    },
                    error_code=error_code,
                    message=message,
                ),
            )
        )

    def _finish(
        self,
        *,
        call_id: str,
        tool_name: str,
        status: ToolCallStatus,
        tool: Tool | None,
        request_hash: str | None,
        approval_required: bool,
        output: FrozenJsonValue = None,
        usage_tokens: int = 0,
        usage_cost: int = 0,
        charged_tokens: int = 0,
        charged_cost: int = 0,
        error_code: str | None = None,
        message: str | None = None,
        approval: Mapping[str, FrozenJsonValue] | None = None,
    ) -> Transition:
        observation = Observation(
            {
                "tool_call": {
                    "call_id": call_id,
                    "tool_name": tool_name,
                    "status": status.value,
                    "output": output,
                    "usage": {
                        "tokens": usage_tokens,
                        "cost_microunits": usage_cost,
                    },
                    "error_code": error_code,
                    "message": message,
                }
            }
        )
        observation_hash = _configuration_hash(
            _frozen_object(observation=observation.value)
        )
        self._record_outcome(
            call_id=call_id,
            tool_name=tool_name,
            status=status,
            tool=tool,
            request_hash=request_hash,
            approval_required=approval_required,
            usage_tokens=usage_tokens,
            usage_cost=usage_cost,
            charged_tokens=charged_tokens,
            charged_cost=charged_cost,
            error_code=error_code,
            message=message,
            approval=approval,
            observation_hash=observation_hash,
        )
        return Transition(observation=observation)
