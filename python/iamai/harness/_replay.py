"""Pure reconstruction and causal validation of committed Trajectories."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math
from typing import cast

from ._controlled import (
    CONTROLLED_EXECUTION_VERSION,
    TOOL_SCHEMA_VERSION,
    TOOL_SPEC_VERSION,
    ApprovalRequest,
    ToolCallStatus,
    _canonical_names,
    _validate_schema_definition,
    _validate_schema_instance,
)
from ._model import (
    HARNESS_CONFIGURATION_VERSION,
    TRAJECTORY_FORMAT_VERSION,
    Evaluation,
    FrozenJsonValue,
    Trajectory,
    TrialFailure,
    TrialResult,
    TrialStatus,
    _configuration_hash,
    _frozen_object,
)


def _causal_error(reason: str) -> ValueError:
    return ValueError(f"invalid Trajectory causal order: {reason}")


@dataclass(slots=True)
class _ControlledReplayLedger:
    max_tool_calls: int
    max_tokens: int
    max_cost_microunits: int
    calls: int = 0
    tokens: int = 0
    cost_microunits: int = 0
    poisoned: bool = False


def _declared_names(
    declaration: Mapping[str, FrozenJsonValue],
    field_name: str,
) -> tuple[str, ...]:
    value = declaration.get(field_name)
    if not isinstance(value, tuple) or not all(
        isinstance(item, str) for item in value
    ):
        raise _causal_error(f"controlled declaration {field_name} is invalid")
    names = cast(tuple[str, ...], value)
    try:
        canonical = _canonical_names(names, field_name=field_name)
    except (TypeError, ValueError) as exc:
        raise _causal_error(
            f"controlled declaration {field_name} is invalid"
        ) from exc
    if names != canonical:
        raise _causal_error(
            f"controlled declaration {field_name} is not canonical"
        )
    return names


def _require_exact_fields(
    declaration: Mapping[str, FrozenJsonValue],
    expected: set[str],
    *,
    field_name: str,
) -> None:
    if set(declaration) != expected:
        raise _causal_error(f"{field_name} fields are invalid")


def _non_negative_record_int(value: FrozenJsonValue, *, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise _causal_error(f"{field_name} must be a non-negative integer")
    return value


def _expect_tool_outcome(
    *,
    actual_status: ToolCallStatus,
    actual_error: FrozenJsonValue,
    expected_status: ToolCallStatus,
    expected_errors: str | tuple[str, ...] | None,
    stage: str,
) -> None:
    if actual_status is not expected_status:
        raise _causal_error(f"Tool Call status does not match {stage}")
    if expected_errors is None:
        if actual_error is not None:
            raise _causal_error(f"Tool Call error does not match {stage}")
        return
    errors = (expected_errors,) if isinstance(expected_errors, str) else expected_errors
    if actual_error not in errors:
        raise _causal_error(f"Tool Call error does not match {stage}")


def _zero_tool_usage(
    usage: Mapping[str, FrozenJsonValue],
    charged: Mapping[str, FrozenJsonValue],
    *,
    stage: str,
) -> None:
    if any(
        payload.get(field_name) != 0
        for payload in (usage, charged)
        for field_name in ("tokens", "cost_microunits")
    ):
        raise _causal_error(f"Tool Call usage must be zero at {stage}")


def _expect_preapproval_evidence(
    outcome: Mapping[str, FrozenJsonValue],
    approval: Mapping[str, FrozenJsonValue],
    *,
    stage: str,
) -> None:
    approval_required = outcome.get("approval_required")
    expected_status = "not_obtained" if approval_required is True else "not_required"
    if (
        approval.get("status") != expected_status
        or approval.get("approver") is not None
        or approval.get("approver_version") is not None
        or approval.get("reason") != ""
    ):
        raise _causal_error(f"Tool Call approval evidence does not match {stage}")


def _validate_controlled_tool_semantics(
    *,
    trajectory: Trajectory,
    action_index: int,
    arguments: FrozenJsonValue,
    tool_name: str,
    declared_tool: Mapping[str, FrozenJsonValue] | None,
    policy: Mapping[str, FrozenJsonValue],
    policy_hash: str,
    budget_hash: str,
    approver_hash: str | None,
    outcome: Mapping[str, FrozenJsonValue],
    ledger: _ControlledReplayLedger,
) -> None:
    status_value = outcome.get("status")
    if not isinstance(status_value, str):
        raise _causal_error("Tool Call status must be a string")
    try:
        tool_status = ToolCallStatus(status_value)
    except ValueError as exc:
        raise _causal_error("Tool Call status is unsupported") from exc
    error_code = outcome.get("error_code")
    request_hash = outcome.get("request_hash")
    request_nonce = outcome.get("request_nonce")
    usage = outcome.get("usage")
    charged = outcome.get("budget_charged")
    approval = outcome.get("approval")
    if (
        not isinstance(usage, Mapping)
        or not isinstance(charged, Mapping)
        or not isinstance(approval, Mapping)
    ):
        raise _causal_error("Tool Call semantic evidence is incomplete")
    approval_status = approval.get("status")
    if not isinstance(approval_status, str):
        raise _causal_error("Tool Call approval status is invalid")

    if ledger.calls >= ledger.max_tool_calls:
        _expect_tool_outcome(
            actual_status=tool_status,
            actual_error=error_code,
            expected_status=ToolCallStatus.BUDGET_EXHAUSTED,
            expected_errors="call_budget_exhausted",
            stage="call budget exhaustion",
        )
        if request_hash is not None or request_nonce is not None:
            raise _causal_error("call-budget outcome cannot contain request evidence")
        _zero_tool_usage(usage, charged, stage="call budget exhaustion")
        _expect_preapproval_evidence(
            outcome,
            approval,
            stage="call budget exhaustion",
        )
        return
    ledger.calls += 1

    if declared_tool is None:
        _expect_tool_outcome(
            actual_status=tool_status,
            actual_error=error_code,
            expected_status=ToolCallStatus.DENIED,
            expected_errors="unknown_tool",
            stage="unknown Tool rejection",
        )
        if request_hash is not None or request_nonce is not None:
            raise _causal_error("unknown Tool outcome cannot contain request evidence")
        _zero_tool_usage(usage, charged, stage="unknown Tool rejection")
        _expect_preapproval_evidence(
            outcome,
            approval,
            stage="unknown Tool rejection",
        )
        return

    if ledger.poisoned:
        _expect_tool_outcome(
            actual_status=tool_status,
            actual_error=error_code,
            expected_status=ToolCallStatus.BUDGET_EXHAUSTED,
            expected_errors="usage_budget_exhausted",
            stage="poisoned execution budget",
        )
        if request_hash is not None or request_nonce is not None:
            raise _causal_error(
                "poisoned-budget outcome cannot contain request evidence"
            )
        _zero_tool_usage(usage, charged, stage="poisoned execution budget")
        _expect_preapproval_evidence(
            outcome,
            approval,
            stage="poisoned execution budget",
        )
        return

    input_schema = declared_tool.get("input_schema")
    schema_valid = isinstance(arguments, Mapping) and isinstance(input_schema, Mapping)
    if schema_valid:
        try:
            _validate_schema_instance(
                cast(Mapping[str, FrozenJsonValue], arguments),
                cast(Mapping[str, FrozenJsonValue], input_schema),
            )
        except (TypeError, ValueError, AssertionError):
            schema_valid = False
    if not schema_valid:
        _expect_tool_outcome(
            actual_status=tool_status,
            actual_error=error_code,
            expected_status=ToolCallStatus.INVALID,
            expected_errors="invalid_arguments",
            stage="schema validation",
        )
        if request_hash is not None or request_nonce is not None:
            raise _causal_error("schema-invalid outcome cannot contain request evidence")
        _zero_tool_usage(usage, charged, stage="schema validation")
        _expect_preapproval_evidence(outcome, approval, stage="schema validation")
        return
    if not isinstance(arguments, Mapping) or not isinstance(input_schema, Mapping):
        raise AssertionError("schema-valid Tool arguments were not objects")

    tool_version = declared_tool.get("version")
    tool_spec_hash = outcome.get("tool_spec_hash")
    reserved_tokens = _non_negative_record_int(
        declared_tool.get("reserved_tokens"),
        field_name="Tool reserved_tokens",
    )
    reserved_cost = _non_negative_record_int(
        declared_tool.get("reserved_cost_microunits"),
        field_name="Tool reserved_cost_microunits",
    )
    if (
        not isinstance(tool_version, str)
        or not isinstance(tool_spec_hash, str)
        or not isinstance(request_nonce, str)
        or not request_nonce.strip()
    ):
        raise _causal_error("Tool reservation declaration is invalid")
    expected_request = ApprovalRequest(
        trial_id=trajectory.trial_id,
        call_id=f"tool-{action_index}",
        request_nonce=request_nonce,
        action_index=action_index,
        tool_name=tool_name,
        tool_version=tool_version,
        tool_spec_hash=tool_spec_hash,
        arguments=arguments,
        policy_hash=policy_hash,
        budget_hash=budget_hash,
        approver_hash=approver_hash,
        reserved_tokens=reserved_tokens,
        reserved_cost_microunits=reserved_cost,
    )
    if request_hash != expected_request.request_hash:
        raise _causal_error("Tool Call request hash does not bind this Action")

    permission_name = declared_tool.get("permission_name")
    runtime_capabilities = declared_tool.get("runtime_capabilities")
    if not isinstance(permission_name, str) or not isinstance(
        runtime_capabilities, tuple
    ):
        raise _causal_error("Tool policy declaration is invalid")
    allowed = (
        tool_name in _declared_names(policy, "allowed_tools")
        and permission_name in _declared_names(policy, "allowed_permissions")
        and set(runtime_capabilities).issubset(
            _declared_names(policy, "allowed_runtime_capabilities")
        )
    )
    if not allowed:
        _expect_tool_outcome(
            actual_status=tool_status,
            actual_error=error_code,
            expected_status=ToolCallStatus.DENIED,
            expected_errors="policy_denied",
            stage="ExecutionPolicy",
        )
        _zero_tool_usage(usage, charged, stage="ExecutionPolicy")
        _expect_preapproval_evidence(outcome, approval, stage="ExecutionPolicy")
        return

    if (
        ledger.tokens + reserved_tokens > ledger.max_tokens
        or ledger.cost_microunits + reserved_cost > ledger.max_cost_microunits
    ):
        _expect_tool_outcome(
            actual_status=tool_status,
            actual_error=error_code,
            expected_status=ToolCallStatus.BUDGET_EXHAUSTED,
            expected_errors="usage_budget_exhausted",
            stage="usage reservation",
        )
        _zero_tool_usage(usage, charged, stage="usage reservation")
        _expect_preapproval_evidence(outcome, approval, stage="usage reservation")
        return

    if approval_status == "missing":
        if approver_hash is not None:
            raise _causal_error(
                "Tool Call claims a missing Approver despite its declaration"
            )
    elif approval_status in {
        "cancelled",
        "timed_out",
        "failed",
        "invalid",
        "denied",
        "approved",
    } and approver_hash is None:
        raise _causal_error(
            "Tool Call claims an Approver outcome without a declaration"
        )

    if approval_status != "not_required" and approval_status != "approved":
        approval_outcomes = {
            "missing": (ToolCallStatus.DENIED, ("approval_missing",)),
            "cancelled": (ToolCallStatus.CANCELLED, ("cancelled",)),
            "timed_out": (ToolCallStatus.TIMED_OUT, ("approval_timed_out",)),
            "failed": (ToolCallStatus.DENIED, ("approval_failed",)),
            "invalid": (
                ToolCallStatus.DENIED,
                (
                    "approval_invalid",
                    "approval_mismatch",
                    "approval_drift",
                ),
            ),
            "denied": (ToolCallStatus.DENIED, ("approval_denied",)),
        }
        expected = approval_outcomes.get(approval_status)
        if expected is None:
            raise _causal_error("Tool Call did not resolve required Approval")
        _expect_tool_outcome(
            actual_status=tool_status,
            actual_error=error_code,
            expected_status=expected[0],
            expected_errors=expected[1],
            stage="Approval",
        )
        _zero_tool_usage(usage, charged, stage="Approval")
        return

    usage_tokens = _non_negative_record_int(
        usage.get("tokens"),
        field_name="Tool usage tokens",
    )
    usage_cost = _non_negative_record_int(
        usage.get("cost_microunits"),
        field_name="Tool usage cost_microunits",
    )
    charged_tokens = _non_negative_record_int(
        charged.get("tokens"),
        field_name="Tool charged tokens",
    )
    charged_cost = _non_negative_record_int(
        charged.get("cost_microunits"),
        field_name="Tool charged cost_microunits",
    )

    if tool_status is ToolCallStatus.SUCCEEDED:
        _expect_tool_outcome(
            actual_status=tool_status,
            actual_error=error_code,
            expected_status=ToolCallStatus.SUCCEEDED,
            expected_errors=None,
            stage="successful Tool execution",
        )
        if (
            usage_tokens != charged_tokens
            or usage_cost != charged_cost
            or usage_tokens > reserved_tokens
            or usage_cost > reserved_cost
        ):
            raise _causal_error("successful Tool usage exceeds its reservation")
        ledger.tokens += usage_tokens
        ledger.cost_microunits += usage_cost
        return

    if error_code == "usage_exceeded_reservation":
        _expect_tool_outcome(
            actual_status=tool_status,
            actual_error=error_code,
            expected_status=ToolCallStatus.FAILED,
            expected_errors="usage_exceeded_reservation",
            stage="Tool usage contract violation",
        )
        if (
            usage_tokens != charged_tokens
            or usage_cost != charged_cost
            or not (
                usage_tokens > reserved_tokens or usage_cost > reserved_cost
            )
        ):
            raise _causal_error("Tool usage violation evidence is inconsistent")
        ledger.tokens += usage_tokens
        ledger.cost_microunits += usage_cost
        ledger.poisoned = True
        return

    handler_outcomes = {
        "tool_failed": (ToolCallStatus.FAILED, "Tool failure"),
        "tool_timed_out": (ToolCallStatus.TIMED_OUT, "Tool timeout"),
        "cancelled": (ToolCallStatus.CANCELLED, "Tool cancellation"),
    }
    if not isinstance(error_code, str):
        raise _causal_error("Tool handler error code is invalid")
    expected_handler = handler_outcomes.get(error_code)
    if expected_handler is None:
        raise _causal_error("Tool Call outcome does not match an execution stage")
    _expect_tool_outcome(
        actual_status=tool_status,
        actual_error=error_code,
        expected_status=expected_handler[0],
        expected_errors=error_code,
        stage=expected_handler[1],
    )
    if (
        usage_tokens != 0
        or usage_cost != 0
        or charged_tokens != reserved_tokens
        or charged_cost != reserved_cost
    ):
        raise _causal_error("failed Tool execution charge does not match reservation")
    ledger.tokens += reserved_tokens
    ledger.cost_microunits += reserved_cost


def _validate_configuration(
    trajectory: Trajectory,
) -> Mapping[str, FrozenJsonValue]:
    configuration = trajectory.configuration
    _require_exact_fields(
        configuration,
        {
            "harness_configuration_version",
            "agent",
            "environment",
            "evaluator",
            "max_actions",
        },
        field_name="configuration",
    )
    if (
        configuration.get("harness_configuration_version")
        != HARNESS_CONFIGURATION_VERSION
    ):
        raise ValueError("Trajectory configuration version is missing or unsupported")
    declared_components: dict[str, Mapping[str, FrozenJsonValue]] = {}
    for role in ("agent", "environment", "evaluator"):
        declared = configuration.get(role)
        if not isinstance(declared, Mapping):
            raise ValueError(f"Trajectory configuration is missing declared {role}")
        _require_exact_fields(
            declared,
            {"name", "version", "config"},
            field_name=f"{role} declaration",
        )
        name = declared.get("name")
        version = declared.get("version")
        component_config = declared.get("config")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Trajectory configuration {role} name is invalid")
        if not isinstance(version, str) or not version.strip():
            raise ValueError(f"Trajectory configuration {role} version is invalid")
        if not isinstance(component_config, Mapping):
            raise ValueError(f"Trajectory configuration {role} config is invalid")
        declared_components[role] = declared
    return declared_components["evaluator"]


def _validate_causal_order(
    trajectory: Trajectory,
    status: TrialStatus,
) -> FrozenJsonValue:
    max_actions = trajectory.configuration.get("max_actions")
    if (
        isinstance(max_actions, bool)
        or not isinstance(max_actions, int)
        or max_actions <= 0
    ):
        raise _causal_error("configuration must declare a positive integer max_actions")

    environment = trajectory.configuration.get("environment")
    if not isinstance(environment, Mapping):
        raise _causal_error("configuration must declare an Environment")
    environment_config = environment.get("config")
    if not isinstance(environment_config, Mapping):
        raise _causal_error("configuration must declare Environment config")
    controlled = environment_config.get("kind") == "controlled_tool"
    if controlled and (
        environment_config.get("controlled_execution_version")
        != CONTROLLED_EXECUTION_VERSION
    ):
        raise _causal_error("controlled execution version is unsupported")
    if controlled and environment_config.get("schema_version") != TOOL_SCHEMA_VERSION:
        raise _causal_error("controlled Tool schema version is unsupported")
    if controlled and environment_config.get("single_use") is not True:
        raise _causal_error("controlled Environment lifecycle declaration is invalid")
    controlled_tools: dict[str, Mapping[str, FrozenJsonValue]] = {}
    controlled_policy: Mapping[str, FrozenJsonValue] | None = None
    controlled_policy_hash: str | None = None
    controlled_budget_hash: str | None = None
    controlled_approver: Mapping[str, FrozenJsonValue] | None = None
    controlled_approver_hash: str | None = None
    controlled_ledger: _ControlledReplayLedger | None = None
    if controlled:
        _require_exact_fields(
            environment_config,
            {
                "kind",
                "controlled_execution_version",
                "schema_version",
                "tools",
                "policy",
                "policy_hash",
                "budget",
                "budget_hash",
                "approver",
                "approver_hash",
                "single_use",
            },
            field_name="Environment declaration",
        )
        raw_tools = environment_config.get("tools")
        raw_policy = environment_config.get("policy")
        raw_policy_hash = environment_config.get("policy_hash")
        raw_budget = environment_config.get("budget")
        raw_budget_hash = environment_config.get("budget_hash")
        raw_approver = environment_config.get("approver")
        raw_approver_hash = environment_config.get("approver_hash")
        if (
            not isinstance(raw_tools, tuple)
            or not isinstance(raw_policy, Mapping)
            or not isinstance(raw_budget, Mapping)
        ):
            raise _causal_error("controlled execution declaration is incomplete")
        if not isinstance(raw_policy_hash, str):
            raise _causal_error("controlled policy hash is invalid")
        if _configuration_hash(raw_policy) != raw_policy_hash:
            raise _causal_error("controlled policy hash does not match its declaration")
        if (
            not isinstance(raw_budget_hash, str)
            or _configuration_hash(raw_budget) != raw_budget_hash
        ):
            raise _causal_error("controlled budget hash does not match its declaration")
        if raw_approver is not None and not isinstance(raw_approver, Mapping):
            raise _causal_error("controlled Approver declaration is invalid")
        if raw_approver is None:
            if raw_approver_hash is not None:
                raise _causal_error("controlled Approver hash has no declaration")
        elif (
            not isinstance(raw_approver_hash, str)
            or _configuration_hash(raw_approver) != raw_approver_hash
        ):
            raise _causal_error("controlled Approver hash does not match declaration")
        controlled_policy = raw_policy
        controlled_policy_hash = raw_policy_hash
        controlled_budget_hash = raw_budget_hash
        controlled_approver = raw_approver
        controlled_approver_hash = raw_approver_hash
        _require_exact_fields(
            raw_policy,
            {
                "version",
                "allowed_tools",
                "allowed_permissions",
                "allowed_runtime_capabilities",
                "approval_required_tools",
                "approval_required_permissions",
            },
            field_name="ExecutionPolicy declaration",
        )
        policy_version = raw_policy.get("version")
        if not isinstance(policy_version, str) or not policy_version.strip():
            raise _causal_error("controlled policy version is invalid")
        policy_names = {
            field_name: _declared_names(raw_policy, field_name)
            for field_name in (
                "allowed_tools",
                "allowed_permissions",
                "allowed_runtime_capabilities",
                "approval_required_tools",
                "approval_required_permissions",
            )
        }
        _require_exact_fields(
            raw_budget,
            {
                "max_tool_calls",
                "max_tokens",
                "max_cost_microunits",
                "tool_timeout_seconds",
                "currency",
                "pricing_version",
            },
            field_name="ExecutionBudget declaration",
        )
        timeout = raw_budget.get("tool_timeout_seconds")
        currency = raw_budget.get("currency")
        pricing_version = raw_budget.get("pricing_version")
        if (
            not isinstance(timeout, float)
            or not math.isfinite(timeout)
            or timeout <= 0
            or not isinstance(currency, str)
            or not currency.strip()
            or not isinstance(pricing_version, str)
            or not pricing_version.strip()
        ):
            raise _causal_error("controlled execution budget declaration is invalid")
        if raw_approver is not None:
            _require_exact_fields(
                raw_approver,
                {"name", "version", "config"},
                field_name="Approver declaration",
            )
            approver_name = raw_approver.get("name")
            approver_version = raw_approver.get("version")
            approver_config = raw_approver.get("config")
            if (
                not isinstance(approver_name, str)
                or not approver_name.strip()
                or not isinstance(approver_version, str)
                or not approver_version.strip()
                or not isinstance(approver_config, Mapping)
            ):
                raise _causal_error("controlled Approver declaration is invalid")
        max_tool_calls = _non_negative_record_int(
            raw_budget.get("max_tool_calls"),
            field_name="controlled max_tool_calls",
        )
        max_tokens = _non_negative_record_int(
            raw_budget.get("max_tokens"),
            field_name="controlled max_tokens",
        )
        max_cost = _non_negative_record_int(
            raw_budget.get("max_cost_microunits"),
            field_name="controlled max_cost_microunits",
        )
        controlled_ledger = _ControlledReplayLedger(
            max_tool_calls=max_tool_calls,
            max_tokens=max_tokens,
            max_cost_microunits=max_cost,
        )
        declared_tool_names: list[str] = []
        for raw_tool in raw_tools:
            if not isinstance(raw_tool, Mapping):
                raise _causal_error("controlled Tool declaration must be an object")
            _require_exact_fields(
                raw_tool,
                {
                    "tool_spec_version",
                    "name",
                    "version",
                    "description",
                    "input_schema_version",
                    "input_schema",
                    "permission_name",
                    "runtime_capabilities",
                    "requires_approval",
                    "reserved_tokens",
                    "reserved_cost_microunits",
                },
                field_name="Tool declaration",
            )
            tool_name = raw_tool.get("name")
            tool_version = raw_tool.get("version")
            if (
                not isinstance(tool_name, str)
                or not tool_name.strip()
                or not isinstance(tool_version, str)
                or not tool_version.strip()
                or tool_name in controlled_tools
            ):
                raise _causal_error("controlled Tool declaration identity is invalid")
            input_schema = raw_tool.get("input_schema")
            runtime_capabilities = raw_tool.get("runtime_capabilities")
            if (
                raw_tool.get("tool_spec_version") != TOOL_SPEC_VERSION
                or raw_tool.get("input_schema_version") != TOOL_SCHEMA_VERSION
                or not isinstance(raw_tool.get("description"), str)
                or not isinstance(raw_tool.get("permission_name"), str)
                or not str(raw_tool.get("permission_name")).strip()
                or not isinstance(runtime_capabilities, tuple)
                or not isinstance(raw_tool.get("requires_approval"), bool)
            ):
                raise _causal_error("controlled Tool declaration is invalid")
            _declared_names(raw_tool, "runtime_capabilities")
            try:
                _validate_schema_definition(input_schema)
            except (TypeError, ValueError) as exc:
                raise _causal_error("controlled Tool schema is invalid") from exc
            if not isinstance(input_schema, Mapping) or input_schema.get("type") != "object":
                raise _causal_error("controlled Tool schema root must be an object")
            _non_negative_record_int(
                raw_tool.get("reserved_tokens"),
                field_name="Tool reserved_tokens",
            )
            _non_negative_record_int(
                raw_tool.get("reserved_cost_microunits"),
                field_name="Tool reserved_cost_microunits",
            )
            controlled_tools[tool_name] = raw_tool
            declared_tool_names.append(tool_name)
        if declared_tool_names != sorted(declared_tool_names):
            raise _causal_error("controlled Tool declarations are not canonical")
        if not set(policy_names["allowed_tools"]).issubset(controlled_tools):
            raise _causal_error("ExecutionPolicy allows an undeclared Tool")
        if not set(policy_names["approval_required_tools"]).issubset(
            policy_names["allowed_tools"]
        ):
            raise _causal_error("ExecutionPolicy requires Approval for a denied Tool")
        if not set(policy_names["approval_required_permissions"]).issubset(
            policy_names["allowed_permissions"]
        ):
            raise _causal_error(
                "ExecutionPolicy requires Approval for a denied permission"
            )

    middle = trajectory.records[1:-1]
    if not middle:
        raise _causal_error("terminal record has no preceding outcome")
    marker_kind = {
        TrialStatus.COMPLETED: "evaluation.recorded",
        TrialStatus.BUDGET_EXHAUSTED: "evaluation.recorded",
        TrialStatus.FAILED: "trial.failure",
        TrialStatus.CANCELLED: "trial.cancelled",
    }[status]
    marker = middle[-1]
    if marker.kind != marker_kind:
        raise _causal_error(
            f"{status.value} must place {marker_kind} immediately before termination"
        )
    marker_fields = {
        TrialStatus.COMPLETED: {
            "passed",
            "score",
            "evaluator",
            "evaluator_version",
        },
        TrialStatus.BUDGET_EXHAUSTED: {
            "passed",
            "score",
            "evaluator",
            "evaluator_version",
        },
        TrialStatus.FAILED: {"phase", "code", "exception_type", "message"},
        TrialStatus.CANCELLED: {"phase", "operation"},
    }[status]
    _require_exact_fields(
        marker.payload,
        marker_fields,
        field_name=f"{marker_kind} payload",
    )
    body = middle[:-1]

    reset_seen = bool(body and body[0].kind == "environment.reset")
    if reset_seen and "observation" not in body[0].payload:
        raise _causal_error("Environment reset observation is missing")
    if reset_seen:
        _require_exact_fields(
            body[0].payload,
            {"observation"},
            field_name="reset evidence",
        )
    if reset_seen and controlled:
        reset_hash = _configuration_hash(
            _frozen_object(value=body[0].payload.get("observation"))
        )
        task_input_hash = _configuration_hash(
            _frozen_object(value=trajectory.task.input)
        )
        if reset_hash != task_input_hash:
            raise _causal_error(
                "controlled Environment reset does not match Task input"
            )
    position = 1 if reset_seen else 0
    pending_action = False
    pending_action_name: str | None = None
    pending_action_final = False
    pending_action_payload: FrozenJsonValue = None
    pending_tool_outcome: Mapping[str, FrozenJsonValue] | None = None
    terminated = False
    budget_exhausted = False
    action_count = 0
    final_output: FrozenJsonValue = None

    for record in body[position:]:
        if record.kind == "agent.action":
            if not reset_seen or pending_action or terminated or budget_exhausted:
                raise _causal_error("Agent Action is outside an active Environment state")
            _require_exact_fields(
                record.payload,
                {"name", "payload", "is_final"},
                field_name="Agent Action payload",
            )
            name = record.payload.get("name")
            is_final = record.payload.get("is_final")
            if (
                not isinstance(name, str)
                or not name.strip()
                or not isinstance(is_final, bool)
                or "payload" not in record.payload
            ):
                raise _causal_error("Agent Action payload is invalid")
            pending_action = True
            pending_action_name = name
            pending_action_final = is_final
            pending_action_payload = record.payload.get("payload")
            pending_tool_outcome = None
            action_count += 1
            if action_count > max_actions:
                raise _causal_error("Action count exceeds max_actions")
            continue

        if record.kind == "tool.call.outcome":
            if (
                not controlled
                or not pending_action
                or pending_action_final
                or pending_tool_outcome is not None
                or terminated
                or budget_exhausted
            ):
                raise _causal_error("Tool Call outcome has no pending controlled Action")
            _require_exact_fields(
                record.payload,
                {
                    "call_id",
                    "tool_name",
                    "tool_version",
                    "status",
                    "tool_spec_hash",
                    "policy_hash",
                    "request_hash",
                    "request_nonce",
                    "observation_hash",
                    "approval_required",
                    "approval",
                    "usage",
                    "budget_charged",
                    "error_code",
                    "message",
                },
                field_name="Tool Call outcome",
            )
            call_id = record.payload.get("call_id")
            tool_name = record.payload.get("tool_name")
            status_value = record.payload.get("status")
            if call_id != f"tool-{action_count - 1}":
                raise _causal_error("Tool Call id does not match the pending Action")
            if not isinstance(tool_name, str) or tool_name != pending_action_name:
                raise _causal_error("Tool Call name does not match the pending Action")
            if not isinstance(status_value, str):
                raise _causal_error("Tool Call status must be a string")
            try:
                tool_status = ToolCallStatus(status_value)
            except ValueError as exc:
                raise _causal_error("Tool Call status is unsupported") from exc
            declared_tool = controlled_tools.get(tool_name)
            tool_version = record.payload.get("tool_version")
            tool_spec_hash = record.payload.get("tool_spec_hash")
            if declared_tool is None:
                if tool_version is not None or tool_spec_hash is not None:
                    raise _causal_error("unknown Tool Call has forged Tool declaration")
            else:
                if tool_version != declared_tool.get("version"):
                    raise _causal_error("Tool Call version does not match its declaration")
                if tool_spec_hash != _configuration_hash(declared_tool):
                    raise _causal_error("Tool Call spec hash does not match its declaration")
            if record.payload.get("policy_hash") != controlled_policy_hash:
                raise _causal_error("Tool Call policy hash does not match its declaration")
            usage = record.payload.get("usage")
            charged = record.payload.get("budget_charged")
            if not isinstance(usage, Mapping) or not isinstance(charged, Mapping):
                raise _causal_error("Tool Call usage evidence is missing")
            _require_exact_fields(
                usage,
                {"tokens", "cost_microunits"},
                field_name="Tool usage evidence",
            )
            _require_exact_fields(
                charged,
                {"tokens", "cost_microunits"},
                field_name="Tool charge evidence",
            )
            for usage_payload in (usage, charged):
                for field_name in ("tokens", "cost_microunits"):
                    value = usage_payload.get(field_name)
                    if (
                        isinstance(value, bool)
                        or not isinstance(value, int)
                        or value < 0
                    ):
                        raise _causal_error("Tool Call usage evidence is invalid")
            approval_required = record.payload.get("approval_required")
            policy_hash = record.payload.get("policy_hash")
            if not isinstance(approval_required, bool) or not isinstance(
                policy_hash, str
            ):
                raise _causal_error("Tool Call policy evidence is invalid")
            if controlled_policy is None:
                raise AssertionError("controlled policy was not initialized")
            expected_approval = False
            if declared_tool is not None:
                required_tools = controlled_policy.get("approval_required_tools", ())
                required_permissions = controlled_policy.get(
                    "approval_required_permissions", ()
                )
                expected_approval = (
                    declared_tool.get("requires_approval") is True
                    or isinstance(required_tools, tuple)
                    and tool_name in required_tools
                    or isinstance(required_permissions, tuple)
                    and declared_tool.get("permission_name") in required_permissions
                )
            if approval_required is not expected_approval:
                raise _causal_error("Tool Call approval requirement was forged")
            approval = record.payload.get("approval")
            if not isinstance(approval, Mapping):
                raise _causal_error("Tool Call approval evidence is missing")
            _require_exact_fields(
                approval,
                {"status", "approver", "approver_version", "reason"},
                field_name="Approval evidence",
            )
            approval_status = approval.get("status")
            approver_name = approval.get("approver")
            approver_version = approval.get("approver_version")
            approval_reason = approval.get("reason")
            if not isinstance(approval_status, str) or not isinstance(
                approval_reason, str
            ):
                raise _causal_error("Tool Call approval evidence is invalid")
            if not approval_required:
                if (
                    approval_status != "not_required"
                    or approver_name is not None
                    or approver_version is not None
                    or approval_reason != ""
                ):
                    raise _causal_error("Tool Call contains forged approval evidence")
            else:
                allowed_approval_statuses = {
                    "not_obtained",
                    "missing",
                    "cancelled",
                    "timed_out",
                    "failed",
                    "invalid",
                    "denied",
                    "approved",
                }
                if approval_status not in allowed_approval_statuses:
                    raise _causal_error("Tool Call approval status is unsupported")
                if tool_status is ToolCallStatus.SUCCEEDED and approval_status != "approved":
                    raise _causal_error("successful Tool Call is missing approval evidence")
                if approval_status in {"approved", "denied"}:
                    if controlled_approver is None or (
                        approver_name != controlled_approver.get("name")
                        or approver_version != controlled_approver.get("version")
                    ):
                        raise _causal_error("Tool Call Approver identity was forged")
                elif approver_name is not None or approver_version is not None:
                    raise _causal_error("Tool Call has unexpected Approver identity")
                elif approval_reason != "":
                    raise _causal_error("Tool Call has unexpected Approval reason")

            error_code = record.payload.get("error_code")
            message = record.payload.get("message")
            observation_hash = record.payload.get("observation_hash")
            if tool_status is ToolCallStatus.SUCCEEDED:
                if error_code is not None or message is not None:
                    raise _causal_error("successful Tool Call cannot contain an error")
            elif not isinstance(error_code, str) or not isinstance(message, str):
                raise _causal_error("unsuccessful Tool Call must contain an error")
            if tool_status is ToolCallStatus.CANCELLED:
                if observation_hash is not None:
                    raise _causal_error("cancelled Tool Call cannot bind an Observation")
            elif not isinstance(observation_hash, str):
                raise _causal_error("Tool Call outcome is missing its Observation hash")
            if (
                controlled_ledger is None
                or controlled_policy is None
                or controlled_policy_hash is None
                or controlled_budget_hash is None
            ):
                raise AssertionError("controlled Replay state was not initialized")
            _validate_controlled_tool_semantics(
                trajectory=trajectory,
                action_index=action_count - 1,
                arguments=pending_action_payload,
                tool_name=tool_name,
                declared_tool=declared_tool,
                policy=controlled_policy,
                policy_hash=controlled_policy_hash,
                budget_hash=controlled_budget_hash,
                approver_hash=controlled_approver_hash,
                outcome=record.payload,
                ledger=controlled_ledger,
            )
            pending_tool_outcome = record.payload
            continue

        if record.kind == "environment.transition":
            if not pending_action or terminated or budget_exhausted:
                raise _causal_error("Environment Transition has no pending Agent Action")
            _require_exact_fields(
                record.payload,
                {"observation", "terminated", "output"},
                field_name="Environment Transition",
            )
            transition_terminated = record.payload.get("terminated")
            if not isinstance(transition_terminated, bool):
                raise _causal_error("Environment Transition termination flag is invalid")
            if "observation" not in record.payload or "output" not in record.payload:
                raise _causal_error("Environment Transition payload is incomplete")
            if controlled:
                if pending_action_final:
                    if pending_tool_outcome is not None or not transition_terminated:
                        raise _causal_error(
                            "final controlled Action must terminate without Tool evidence"
                        )
                    action_hash = _configuration_hash(
                        _frozen_object(value=pending_action_payload)
                    )
                    observation_hash = _configuration_hash(
                        _frozen_object(value=record.payload.get("observation"))
                    )
                    output_hash = _configuration_hash(
                        _frozen_object(value=record.payload.get("output"))
                    )
                    if observation_hash != action_hash or output_hash != action_hash:
                        raise _causal_error(
                            "final controlled Transition does not match its Action"
                        )
                else:
                    if pending_tool_outcome is None:
                        raise _causal_error(
                            "controlled Action is missing its Tool Call outcome"
                        )
                    if pending_tool_outcome.get("status") == ToolCallStatus.CANCELLED.value:
                        raise _causal_error(
                            "cancelled Tool Call cannot have an Environment Transition"
                        )
                    observation = record.payload.get("observation")
                    tool_call = (
                        observation.get("tool_call")
                        if isinstance(observation, Mapping)
                        else None
                    )
                    if not isinstance(tool_call, Mapping):
                        raise _causal_error(
                            "controlled Transition is missing Tool Call Observation"
                        )
                    if not isinstance(observation, Mapping):
                        raise AssertionError(
                            "controlled Tool Call Observation was not an object"
                        )
                    _require_exact_fields(
                        observation,
                        {"tool_call"},
                        field_name="Tool Call Observation",
                    )
                    _require_exact_fields(
                        tool_call,
                        {
                            "call_id",
                            "tool_name",
                            "status",
                            "output",
                            "usage",
                            "error_code",
                            "message",
                        },
                        field_name="Tool Call Observation payload",
                    )
                    expected_observation_hash = _configuration_hash(
                        _frozen_object(observation=observation)
                    )
                    if (
                        pending_tool_outcome.get("observation_hash")
                        != expected_observation_hash
                    ):
                        raise _causal_error(
                            "controlled Transition Observation hash does not match outcome"
                        )
                    for field_name in (
                        "call_id",
                        "tool_name",
                        "status",
                        "usage",
                        "error_code",
                        "message",
                    ):
                        transition_field_hash = _configuration_hash(
                            _frozen_object(value=tool_call.get(field_name))
                        )
                        outcome_field_hash = _configuration_hash(
                            _frozen_object(
                                value=pending_tool_outcome.get(field_name)
                            )
                        )
                        if transition_field_hash != outcome_field_hash:
                            raise _causal_error(
                                "controlled Transition does not match Tool Call outcome"
                            )
                    if (
                        pending_tool_outcome.get("status")
                        != ToolCallStatus.SUCCEEDED.value
                        and tool_call.get("output") is not None
                    ):
                        raise _causal_error(
                            "unsuccessful Tool Call Observation cannot contain output"
                        )
                    if transition_terminated:
                        raise _causal_error("Tool invocation Transition cannot terminate Trial")
                    if record.payload.get("output") is not None:
                        raise _causal_error(
                            "Tool invocation Transition cannot contain final output"
                        )
            pending_action = False
            pending_action_name = None
            pending_action_final = False
            pending_action_payload = None
            pending_tool_outcome = None
            if transition_terminated:
                terminated = True
                final_output = record.payload.get("output")
            continue

        if record.kind == "budget.exhausted":
            declared_budget = record.payload.get("max_actions")
            if (
                set(record.payload) != {"max_actions"}
                or isinstance(declared_budget, bool)
                or not isinstance(declared_budget, int)
                or not reset_seen
                or pending_action
                or terminated
                or budget_exhausted
                or declared_budget != max_actions
                or action_count != max_actions
            ):
                raise _causal_error(
                    "budget exhaustion does not follow a bounded Action loop"
                )
            budget_exhausted = True
            continue

        raise _causal_error(f"unexpected record kind: {record.kind}")

    if status is TrialStatus.COMPLETED:
        if not reset_seen or pending_action or not terminated or budget_exhausted:
            raise _causal_error(
                "completed Trial requires a paired terminating Environment Transition"
            )
        return final_output

    if status is TrialStatus.BUDGET_EXHAUSTED:
        if (
            not reset_seen
            or pending_action
            or terminated
            or not budget_exhausted
            or action_count != max_actions
        ):
            raise _causal_error(
                "budget-exhausted Trial requires exactly max_actions non-terminal pairs"
            )
        return None

    if status is TrialStatus.FAILED:
        code = marker.payload.get("code")
        phase = marker.payload.get("phase")
        valid_failure_state = (
            code == "environment_reset_error"
            and phase == "environment"
            and not reset_seen
            and not body
            or code == "agent_decide_error"
            and phase == "agent"
            and reset_seen
            and not pending_action
            and not terminated
            and not budget_exhausted
            and action_count < max_actions
            or code == "environment_step_error"
            and phase == "environment"
            and pending_action
            and not terminated
            and not budget_exhausted
            or code == "evaluator_evaluate_error"
            and phase == "evaluator"
            and reset_seen
            and not pending_action
            and (terminated or budget_exhausted)
        )
        if not valid_failure_state:
            raise _causal_error("failure code does not match the committed execution prefix")
        if (
            controlled
            and code == "environment_step_error"
            and pending_action
            and not pending_action_final
            and pending_tool_outcome is not None
        ):
            raise _causal_error(
                "failed controlled Action cannot follow a committed Tool Call outcome"
            )
        return None

    operation = marker.payload.get("operation")
    phase = marker.payload.get("phase")
    valid_cancellation_state = (
        operation == "environment.reset"
        and phase == "environment"
        and not reset_seen
        and not body
        or operation == "agent.decide"
        and phase == "agent"
        and reset_seen
        and not pending_action
        and not terminated
        and not budget_exhausted
        and action_count < max_actions
        or operation == "environment.step"
        and phase == "environment"
        and pending_action
        and not terminated
        and not budget_exhausted
        or operation == "evaluator.evaluate"
        and phase == "evaluator"
        and reset_seen
        and not pending_action
        and (terminated or budget_exhausted)
    )
    if (
        valid_cancellation_state
        and controlled
        and operation == "environment.step"
        and not pending_action_final
        and (
            pending_tool_outcome is None
            or pending_tool_outcome.get("status") != ToolCallStatus.CANCELLED.value
        )
    ):
        raise _causal_error(
            "cancelled controlled Action requires a cancelled Tool Call outcome"
        )
    if not valid_cancellation_state:
        raise _causal_error("cancellation operation does not match the execution prefix")
    return None


def replay(trajectory: Trajectory) -> TrialResult:
    """Reconstruct a TrialResult without invoking Agent or Environment effects."""
    if trajectory.format_version != TRAJECTORY_FORMAT_VERSION:
        raise ValueError(f"unsupported Trajectory format: {trajectory.format_version}")
    if trajectory.config_hash != _configuration_hash(trajectory.configuration):
        raise ValueError("Trajectory configuration hash does not match its snapshot")
    declared_evaluator = _validate_configuration(trajectory)
    if not trajectory.records:
        raise ValueError("Trajectory has no records")
    if [record.sequence for record in trajectory.records] != list(
        range(len(trajectory.records))
    ):
        raise ValueError("Trajectory record sequence must be contiguous from zero")
    if trajectory.records[0].kind != "trial.started":
        raise ValueError("Trajectory must start with trial.started")
    _require_exact_fields(
        trajectory.records[0].payload,
        set(),
        field_name="Trial start payload",
    )
    terminal_records = [
        record for record in trajectory.records if record.kind == "trial.terminated"
    ]
    if len(terminal_records) != 1 or trajectory.records[-1] is not terminal_records[0]:
        raise ValueError("Trajectory must end with exactly one trial.terminated record")

    status_value = terminal_records[0].payload.get("status")
    if not isinstance(status_value, str):
        raise ValueError("terminal Trial status must be a string")
    try:
        status = TrialStatus(status_value)
    except ValueError as exc:
        raise ValueError(f"unsupported terminal Trial status: {status_value}") from exc
    terminal_fields = {
        TrialStatus.COMPLETED: {"status"},
        TrialStatus.BUDGET_EXHAUSTED: {"status"},
        TrialStatus.FAILED: {"status", "phase"},
        TrialStatus.CANCELLED: {"status", "phase", "operation"},
    }[status]
    _require_exact_fields(
        terminal_records[0].payload,
        terminal_fields,
        field_name="Trial termination payload",
    )
    final_output = _validate_causal_order(trajectory, status)

    evaluation_records = [
        record for record in trajectory.records if record.kind == "evaluation.recorded"
    ]
    failure_records = [
        record for record in trajectory.records if record.kind == "trial.failure"
    ]
    cancelled_records = [
        record for record in trajectory.records if record.kind == "trial.cancelled"
    ]

    evaluation: Evaluation | None = None
    failure: TrialFailure | None = None
    if status in {TrialStatus.COMPLETED, TrialStatus.BUDGET_EXHAUSTED}:
        if len(evaluation_records) != 1:
            raise ValueError(
                "completed or budget-exhausted Trajectory must contain exactly one "
                "evaluation.recorded record"
            )
        if failure_records or cancelled_records:
            raise ValueError("evaluated Trajectory cannot contain failure or cancellation")
        evaluation_payload = evaluation_records[0].payload
        passed = evaluation_payload.get("passed")
        score = evaluation_payload.get("score")
        evaluator = evaluation_payload.get("evaluator")
        evaluator_version = evaluation_payload.get("evaluator_version")
        if not isinstance(passed, bool):
            raise ValueError("recorded Evaluation passed value must be a bool")
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise ValueError("recorded Evaluation score must be a number")
        if not isinstance(evaluator, str) or not isinstance(evaluator_version, str):
            raise ValueError("recorded Evaluation identity must be strings")
        if (
            evaluator != declared_evaluator["name"]
            or evaluator_version != declared_evaluator["version"]
        ):
            raise ValueError(
                "recorded Evaluation identity does not match Trajectory configuration"
            )
        evaluation = Evaluation(
            passed=passed,
            score=float(score),
            evaluator=evaluator,
            evaluator_version=evaluator_version,
        )
    elif status is TrialStatus.FAILED:
        if evaluation_records or cancelled_records or len(failure_records) != 1:
            raise ValueError(
                "failed Trajectory must contain exactly one failure and no "
                "Evaluation or cancellation"
            )
        failure_payload = failure_records[0].payload
        phase = failure_payload.get("phase")
        code = failure_payload.get("code")
        exception_type = failure_payload.get("exception_type")
        message = failure_payload.get("message")
        if (
            not isinstance(phase, str)
            or not isinstance(code, str)
            or not isinstance(exception_type, str)
            or not isinstance(message, str)
        ):
            raise ValueError("recorded Trial failure fields must be strings")
        failure = TrialFailure(
            phase=phase,
            code=code,
            exception_type=exception_type,
            message=message,
        )
        if terminal_records[0].payload.get("phase") != failure.phase:
            raise ValueError("terminal Trial phase does not match recorded failure")
    else:
        if evaluation_records or failure_records or len(cancelled_records) != 1:
            raise ValueError(
                "cancelled Trajectory must contain exactly one cancellation and no "
                "Evaluation or failure"
            )
        cancelled_phase = cancelled_records[0].payload.get("phase")
        cancelled_operation = cancelled_records[0].payload.get("operation")
        if not isinstance(cancelled_phase, str) or not isinstance(
            cancelled_operation, str
        ):
            raise ValueError("recorded cancellation phase and operation must be strings")
        if terminal_records[0].payload.get("phase") != cancelled_phase:
            raise ValueError("terminal Trial phase does not match cancellation")
        if terminal_records[0].payload.get("operation") != cancelled_operation:
            raise ValueError("terminal Trial operation does not match cancellation")

    return TrialResult(
        trial_id=trajectory.trial_id,
        status=status,
        final_output=final_output,
        evaluation=evaluation,
        trajectory=trajectory,
        failure=failure,
    )
