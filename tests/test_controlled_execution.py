from __future__ import annotations

import asyncio
import time
from collections.abc import Mapping
from dataclasses import replace
from typing import cast

import pytest

from iamai.harness import (
    Action,
    ApprovalDecision,
    ApprovalRequest,
    ControlledToolEnvironment,
    ExactEvaluator,
    Experiment,
    ExecutionBudget,
    ExecutionPolicy,
    JsonlTrajectoryStore,
    ScriptedAgent,
    Task,
    Tool,
    ToolResult,
    ToolSpec,
    Trial,
    TrialConfig,
    TrialResult,
    TrialStatus,
    Trajectory,
    TrajectoryRecord,
    replay,
)
from iamai.harness._model import (
    FrozenJsonValue,
    JsonValue,
    _configuration_hash,
    _freeze_json,
    _thaw_json,
)


def _with_configuration(
    trajectory: Trajectory,
    configuration: dict[str, JsonValue],
) -> Trajectory:
    frozen = _freeze_json(configuration)
    assert isinstance(frozen, Mapping)
    typed = cast(Mapping[str, FrozenJsonValue], frozen)
    return replace(
        trajectory,
        configuration=typed,
        config_hash=_configuration_hash(typed),
    )


def _hash_json_object(value: dict[str, JsonValue]) -> str:
    frozen = _freeze_json(value)
    assert isinstance(frozen, Mapping)
    return _configuration_hash(cast(Mapping[str, FrozenJsonValue], frozen))


def _with_records(
    trajectory: Trajectory,
    records: list[TrajectoryRecord],
) -> Trajectory:
    return replace(
        trajectory,
        records=tuple(
            replace(record, sequence=index)
            for index, record in enumerate(records)
        ),
    )


def _with_self_consistent_tool_outcome(
    trajectory: Trajectory,
    *,
    outcome_number: int = 0,
    **updates: JsonValue,
) -> Trajectory:
    records = list(trajectory.records)
    outcome_indexes = [
        index for index, record in enumerate(records) if record.kind == "tool.call.outcome"
    ]
    outcome_index = outcome_indexes[outcome_number]
    transition_index = next(
        index
        for index, record in enumerate(records[outcome_index + 1 :], outcome_index + 1)
        if record.kind == "environment.transition"
    )
    outcome = cast(
        dict[str, JsonValue],
        _thaw_json(records[outcome_index].payload),
    )
    outcome.update(updates)
    transition = cast(
        dict[str, JsonValue],
        _thaw_json(records[transition_index].payload),
    )
    observation = cast(dict[str, JsonValue], transition["observation"])
    tool_call = cast(dict[str, JsonValue], observation["tool_call"])
    for field_name in (
        "call_id",
        "tool_name",
        "status",
        "usage",
        "error_code",
        "message",
    ):
        tool_call[field_name] = outcome[field_name]
    outcome["observation_hash"] = _hash_json_object({"observation": observation})
    records[outcome_index] = replace(records[outcome_index], payload=outcome)
    records[transition_index] = replace(records[transition_index], payload=transition)
    return _with_records(trajectory, records)


def test_controlled_tool_success_is_recorded_and_replay_has_no_effects() -> None:
    calls = 0

    async def add(arguments: Mapping[str, object]) -> ToolResult:
        nonlocal calls
        calls += 1
        assert arguments == {"left": 1, "right": 2}
        return ToolResult(output=3, tokens=2, cost_microunits=5)

    async def scenario() -> None:
        environment = ControlledToolEnvironment(
            tools=(
                Tool(
                    ToolSpec(
                        name="add",
                        version="1",
                        description="Add two integers.",
                        input_schema={
                            "type": "object",
                            "properties": {
                                "left": {"type": "integer"},
                                "right": {"type": "integer"},
                            },
                            "required": ["left", "right"],
                            "additionalProperties": False,
                        },
                        permission_name="math.read",
                        reserved_tokens=4,
                        reserved_cost_microunits=10,
                    ),
                    lambda arguments: add(arguments),
                ),
            ),
            policy=ExecutionPolicy(
                version="policy-1",
                allowed_tools=("add",),
                allowed_permissions=("math.read",),
            ),
            budget=ExecutionBudget(
                max_tool_calls=2,
                max_tokens=4,
                max_cost_microunits=10,
                tool_timeout_seconds=1,
                currency="USD",
                pricing_version="fixture-1",
            ),
            name="controlled-math",
            version="1",
        )
        result = await Trial(
            task=Task(id="controlled-add", input={"question": "1 + 2"}),
            agent=ScriptedAgent(
                [Action.invoke("add", {"left": 1, "right": 2}), Action.finish(3)],
                name="controlled-agent",
                version="1",
            ),
            environment=environment,
            evaluator=ExactEvaluator(3, version="1"),
            config=TrialConfig(trial_id="controlled-add-1", max_actions=2),
        ).run()

        assert result.status is TrialStatus.COMPLETED
        assert calls == 1
        assert [record.kind for record in result.trajectory.records] == [
            "trial.started",
            "environment.reset",
            "agent.action",
            "tool.call.outcome",
            "environment.transition",
            "agent.action",
            "environment.transition",
            "evaluation.recorded",
            "trial.terminated",
        ]
        outcome = result.trajectory.records[3].payload
        assert outcome["call_id"] == "tool-0"
        assert outcome["tool_name"] == "add"
        assert outcome["status"] == "succeeded"
        assert outcome["usage"] == {"tokens": 2, "cost_microunits": 5}
        assert result.trajectory.configuration["environment"]["config"]["kind"] == (
            "controlled_tool"
        )

        assert replay(result.trajectory) == result
        assert calls == 1

    asyncio.run(scenario())


def test_schema_is_checked_without_coercion_before_approval_or_tool_effects() -> None:
    approvals = 0
    calls = 0

    class Approver:
        name = "fixture-approver"
        version = "1"
        configuration: dict[str, object] = {"mode": "approve"}

        async def decide(self, request: ApprovalRequest) -> ApprovalDecision:
            nonlocal approvals
            approvals += 1
            return ApprovalDecision.approve(
                request,
            )

    async def effect(arguments: Mapping[str, object]) -> ToolResult:
        nonlocal calls
        calls += 1
        return ToolResult(output=arguments["value"])

    async def scenario() -> None:
        environment = ControlledToolEnvironment(
            tools=(
                Tool(
                    ToolSpec(
                        name="strict-int",
                        version="1",
                        input_schema={
                            "type": "object",
                            "properties": {"value": {"type": "integer"}},
                            "required": ["value"],
                            "additionalProperties": False,
                        },
                        permission_name="fixture.read",
                        requires_approval=True,
                    ),
                    effect,
                ),
            ),
            policy=ExecutionPolicy(
                version="1",
                allowed_tools=("strict-int",),
                allowed_permissions=("fixture.read",),
            ),
            budget=ExecutionBudget(
                max_tool_calls=1,
                max_tokens=0,
                max_cost_microunits=0,
                tool_timeout_seconds=1,
                currency="USD",
                pricing_version="fixture-1",
            ),
            approver=Approver(),
            name="strict-schema",
            version="1",
        )
        result = await Trial(
            task=Task(id="strict-schema", input=None),
            agent=ScriptedAgent(
                [Action.invoke("strict-int", {"value": True}), Action.finish("recovered")],
                name="strict-schema-agent",
                version="1",
            ),
            environment=environment,
            evaluator=ExactEvaluator("recovered", version="1"),
            config=TrialConfig(trial_id="strict-schema-1", max_actions=2),
        ).run()

        assert result.status is TrialStatus.COMPLETED
        assert approvals == 0
        assert calls == 0
        outcomes = [
            record for record in result.trajectory.records if record.kind == "tool.call.outcome"
        ]
        assert len(outcomes) == 1
        assert outcomes[0].payload["status"] == "invalid"
        assert outcomes[0].payload["error_code"] == "invalid_arguments"
        transitions = [
            record
            for record in result.trajectory.records
            if record.kind == "environment.transition"
        ]
        assert transitions[0].payload["observation"]["tool_call"]["status"] == "invalid"
        assert replay(result.trajectory) == result

    asyncio.run(scenario())


def test_tool_schema_rejects_unsupported_or_remote_reference_keywords() -> None:
    try:
        ToolSpec(
            name="remote-schema",
            version="1",
            input_schema={"type": "object", "$ref": "https://example.com/schema.json"},
            permission_name="fixture.read",
        )
    except ValueError as error:
        assert "unsupported: $ref" in str(error)
    else:
        raise AssertionError("unsupported schema was accepted")


def test_policy_is_default_deny_and_runs_before_approval() -> None:
    approvals = 0
    calls = 0

    class Approver:
        name = "should-not-run"
        version = "1"
        configuration: dict[str, object] = {}

        async def decide(self, request: ApprovalRequest) -> ApprovalDecision:
            nonlocal approvals
            approvals += 1
            return ApprovalDecision.approve(
                request,
            )

    async def network_tool(arguments: Mapping[str, object]) -> ToolResult:
        nonlocal calls
        calls += 1
        return ToolResult(output=arguments)

    async def scenario() -> None:
        environment = ControlledToolEnvironment(
            tools=(
                Tool(
                    ToolSpec(
                        name="fetch",
                        version="1",
                        input_schema={
                            "type": "object",
                            "properties": {},
                            "additionalProperties": False,
                        },
                        permission_name="network.read",
                        runtime_capabilities=("network",),
                        requires_approval=True,
                    ),
                    network_tool,
                ),
            ),
            policy=ExecutionPolicy(
                version="deny-network-1",
                allowed_tools=("fetch",),
                allowed_permissions=("network.read",),
                # The required runtime capability is deliberately not granted.
            ),
            budget=ExecutionBudget(
                max_tool_calls=1,
                max_tokens=0,
                max_cost_microunits=0,
                tool_timeout_seconds=1,
                currency="USD",
                pricing_version="fixture-1",
            ),
            approver=Approver(),
            name="default-deny",
            version="1",
        )
        result = await Trial(
            task=Task(id="deny-network", input=None),
            agent=ScriptedAgent(
                [Action.invoke("fetch"), Action.finish("recovered")],
                name="deny-network-agent",
                version="1",
            ),
            environment=environment,
            evaluator=ExactEvaluator("recovered", version="1"),
            config=TrialConfig(trial_id="deny-network-1", max_actions=2),
        ).run()

        outcome = next(
            record for record in result.trajectory.records if record.kind == "tool.call.outcome"
        )
        assert outcome.payload["status"] == "denied"
        assert outcome.payload["error_code"] == "policy_denied"
        assert approvals == 0
        assert calls == 0
        assert replay(result.trajectory) == result

    asyncio.run(scenario())


def test_approval_is_bound_to_the_exact_trial_action_tool_and_policy() -> None:
    requests: list[ApprovalRequest] = []
    calls = 0

    class Approver:
        name = "human-gate"
        version = "2026-08"
        configuration: dict[str, object] = {"queue": "fixture"}

        def __init__(self, *, stale: bool) -> None:
            self.stale = stale

        async def decide(self, request: ApprovalRequest) -> ApprovalDecision:
            requests.append(request)
            approved_request = (
                replace(request, trial_id="another-trial") if self.stale else request
            )
            return ApprovalDecision.approve(
                approved_request,
                reason="fixture approval",
            )

    async def effect(arguments: Mapping[str, object]) -> ToolResult:
        nonlocal calls
        calls += 1
        return ToolResult(output=arguments["value"])

    def trial(*, stale: bool, trial_id: str) -> Trial:
        return Trial(
            task=Task(id="bound-approval", input=None),
            agent=ScriptedAgent(
                [Action.invoke("write", {"value": "ok"}), Action.finish("done")],
                name="bound-approval-agent",
                version="1",
            ),
            environment=ControlledToolEnvironment(
                tools=(
                    Tool(
                        ToolSpec(
                            name="write",
                            version="2",
                            input_schema={
                                "type": "object",
                                "properties": {"value": {"type": "string"}},
                                "required": ["value"],
                                "additionalProperties": False,
                            },
                            permission_name="fixture.write",
                            requires_approval=True,
                        ),
                        effect,
                    ),
                ),
                policy=ExecutionPolicy(
                    version="write-policy-3",
                    allowed_tools=("write",),
                    allowed_permissions=("fixture.write",),
                ),
                budget=ExecutionBudget(
                    max_tool_calls=1,
                    max_tokens=0,
                    max_cost_microunits=0,
                    tool_timeout_seconds=1,
                    currency="USD",
                    pricing_version="fixture-1",
                ),
                approver=Approver(stale=stale),
                name="bound-approval",
                version="1",
            ),
            evaluator=ExactEvaluator("done", version="1"),
            config=TrialConfig(trial_id=trial_id, max_actions=2),
        )

    async def scenario() -> None:
        accepted = await trial(stale=False, trial_id="approval-current").run()
        rejected = await trial(stale=True, trial_id="approval-stale").run()

        assert calls == 1
        assert len(requests) == 2
        assert requests[0].trial_id == "approval-current"
        assert requests[0].call_id == "tool-0"
        assert requests[0].tool_name == "write"
        assert requests[0].tool_version == "2"
        assert requests[0].arguments == {"value": "ok"}
        assert requests[0].policy_hash != requests[0].tool_spec_hash
        accepted_outcome = next(
            record
            for record in accepted.trajectory.records
            if record.kind == "tool.call.outcome"
        )
        rejected_outcome = next(
            record
            for record in rejected.trajectory.records
            if record.kind == "tool.call.outcome"
        )
        assert accepted_outcome.payload["status"] == "succeeded"
        assert accepted_outcome.payload["request_hash"] == requests[0].request_hash
        assert accepted_outcome.payload["approval"] == {
            "status": "approved",
            "approver": "human-gate",
            "approver_version": "2026-08",
            "reason": "fixture approval",
        }
        assert rejected_outcome.payload["status"] == "denied"
        assert rejected_outcome.payload["error_code"] == "approval_mismatch"
        assert rejected_outcome.payload["approval"]["status"] == "invalid"
        assert replay(accepted.trajectory) == accepted
        assert replay(rejected.trajectory) == rejected

    asyncio.run(scenario())


def test_approval_decision_cannot_be_reused_for_a_new_identical_invocation() -> None:
    requests: list[ApprovalRequest] = []
    cached: ApprovalDecision | None = None
    calls = 0

    class CachingApprover:
        name = "caching-approver"
        version = "1"
        configuration: dict[str, object] = {"cache": True}

        async def decide(self, request: ApprovalRequest) -> ApprovalDecision:
            nonlocal cached
            requests.append(request)
            if cached is None:
                cached = ApprovalDecision.approve(request)
            return cached

    async def effect(arguments: Mapping[str, object]) -> ToolResult:
        nonlocal calls
        calls += 1
        return ToolResult(output=arguments)

    def trial(approver: CachingApprover) -> Trial:
        return Trial(
            task=Task(id="approval-reuse", input=None),
            agent=ScriptedAgent(
                [Action.invoke("write"), Action.finish("done")],
                name="approval-reuse-agent",
                version="1",
            ),
            environment=ControlledToolEnvironment(
                tools=(
                    Tool(
                        ToolSpec(
                            name="write",
                            version="1",
                            input_schema={
                                "type": "object",
                                "properties": {},
                                "additionalProperties": False,
                            },
                            permission_name="fixture.write",
                            requires_approval=True,
                        ),
                        effect,
                    ),
                ),
                policy=ExecutionPolicy(
                    version="1",
                    allowed_tools=("write",),
                    allowed_permissions=("fixture.write",),
                ),
                budget=ExecutionBudget(
                    max_tool_calls=1,
                    max_tokens=0,
                    max_cost_microunits=0,
                    tool_timeout_seconds=1,
                    currency="USD",
                    pricing_version="fixture-1",
                ),
                approver=approver,
                name="approval-reuse",
                version="1",
            ),
            evaluator=ExactEvaluator("done", version="1"),
            config=TrialConfig(trial_id="approval-reuse-1", max_actions=2),
        )

    async def scenario() -> None:
        approver = CachingApprover()
        accepted = await trial(approver).run()
        rejected = await trial(approver).run()

        assert calls == 1
        assert len(requests) == 2
        assert requests[0].request_hash != requests[1].request_hash
        rejected_outcome = next(
            record.payload
            for record in rejected.trajectory.records
            if record.kind == "tool.call.outcome"
        )
        assert rejected_outcome["status"] == "denied"
        assert rejected_outcome["error_code"] == "approval_mismatch"
        assert replay(accepted.trajectory) == accepted
        assert replay(rejected.trajectory) == rejected

    asyncio.run(scenario())


def test_approver_identity_or_configuration_drift_fails_before_tool_effects() -> None:
    calls = 0

    class DriftingApprover:
        name = "declared-approver"
        version = "1"

        def __init__(self) -> None:
            self.configuration: dict[str, object] = {"gate": 1}

        async def decide(self, request: ApprovalRequest) -> ApprovalDecision:
            self.configuration["gate"] = True
            return ApprovalDecision.approve(
                request,
            )

    async def effect(arguments: Mapping[str, object]) -> ToolResult:
        nonlocal calls
        calls += 1
        return ToolResult(output=arguments)

    async def scenario() -> None:
        result = await Trial(
            task=Task(id="approver-drift", input=None),
            agent=ScriptedAgent(
                [Action.invoke("write"), Action.finish("recovered")],
                name="approver-drift-agent",
                version="1",
            ),
            environment=ControlledToolEnvironment(
                tools=(
                    Tool(
                        ToolSpec(
                            name="write",
                            version="1",
                            input_schema={
                                "type": "object",
                                "properties": {},
                                "additionalProperties": False,
                            },
                            permission_name="fixture.write",
                            requires_approval=True,
                        ),
                        effect,
                    ),
                ),
                policy=ExecutionPolicy(
                    version="1",
                    allowed_tools=("write",),
                    allowed_permissions=("fixture.write",),
                ),
                budget=ExecutionBudget(
                    max_tool_calls=1,
                    max_tokens=0,
                    max_cost_microunits=0,
                    tool_timeout_seconds=1,
                    currency="USD",
                    pricing_version="fixture-1",
                ),
                approver=DriftingApprover(),
                name="approver-drift",
                version="1",
            ),
            evaluator=ExactEvaluator("recovered", version="1"),
            config=TrialConfig(trial_id="approver-drift-1", max_actions=2),
        ).run()

        assert calls == 0
        outcome = next(
            record.payload
            for record in result.trajectory.records
            if record.kind == "tool.call.outcome"
        )
        assert outcome["status"] == "denied"
        assert outcome["error_code"] == "approval_drift"
        assert replay(result.trajectory) == result

    asyncio.run(scenario())


def test_non_json_approver_identity_drift_is_an_audited_denial() -> None:
    calls = 0

    class MutableApprover:
        name = "declared-approver"
        version = "1"
        configuration: dict[str, object] = {}

        async def decide(self, request: ApprovalRequest) -> ApprovalDecision:
            raise AssertionError(f"drifted Approver was called: {request.request_hash}")

    async def effect(arguments: Mapping[str, object]) -> ToolResult:
        nonlocal calls
        calls += 1
        return ToolResult(output=arguments)

    async def scenario() -> None:
        approver = MutableApprover()
        environment = ControlledToolEnvironment(
            tools=(
                Tool(
                    ToolSpec(
                        name="write",
                        version="1",
                        input_schema={
                            "type": "object",
                            "properties": {},
                            "additionalProperties": False,
                        },
                        permission_name="fixture.write",
                        requires_approval=True,
                    ),
                    effect,
                ),
            ),
            policy=ExecutionPolicy(
                version="1",
                allowed_tools=("write",),
                allowed_permissions=("fixture.write",),
            ),
            budget=ExecutionBudget(
                max_tool_calls=1,
                max_tokens=0,
                max_cost_microunits=0,
                tool_timeout_seconds=1,
                currency="USD",
                pricing_version="fixture-1",
            ),
            approver=approver,
            name="malformed-approver-drift",
            version="1",
        )
        trial = Trial(
            task=Task(id="malformed-approver-drift", input=None),
            agent=ScriptedAgent(
                [Action.invoke("write"), Action.finish("recovered")],
                name="malformed-approver-drift-agent",
                version="1",
            ),
            environment=environment,
            evaluator=ExactEvaluator("recovered", version="1"),
            config=TrialConfig(trial_id="malformed-approver-drift-1", max_actions=2),
        )
        approver.name = cast(str, object())
        result = await trial.run()

        assert result.status is TrialStatus.COMPLETED
        assert calls == 0
        outcome = next(
            record.payload
            for record in result.trajectory.records
            if record.kind == "tool.call.outcome"
        )
        assert outcome["status"] == "denied"
        assert outcome["error_code"] == "approval_drift"
        assert replay(result.trajectory) == result

    asyncio.run(scenario())


def test_call_and_reservation_budgets_fail_before_additional_effects() -> None:
    calls = 0

    async def metered(arguments: Mapping[str, object]) -> ToolResult:
        nonlocal calls
        calls += 1
        return ToolResult(
            output=arguments["value"],
            tokens=2,
            cost_microunits=3,
        )

    async def scenario() -> None:
        environment = ControlledToolEnvironment(
            tools=(
                Tool(
                    ToolSpec(
                        name="metered",
                        version="1",
                        input_schema={
                            "type": "object",
                            "properties": {"value": {"type": "string"}},
                            "required": ["value"],
                            "additionalProperties": False,
                        },
                        permission_name="metered.read",
                        reserved_tokens=4,
                        reserved_cost_microunits=5,
                    ),
                    metered,
                ),
            ),
            policy=ExecutionPolicy(
                version="1",
                allowed_tools=("metered",),
                allowed_permissions=("metered.read",),
            ),
            budget=ExecutionBudget(
                max_tool_calls=2,
                max_tokens=4,
                max_cost_microunits=5,
                tool_timeout_seconds=1,
                currency="USD",
                pricing_version="fixture-1",
            ),
            name="metered",
            version="1",
        )
        result = await Trial(
            task=Task(id="metered", input=None),
            agent=ScriptedAgent(
                [
                    Action.invoke("metered", {"value": "first"}),
                    Action.invoke("metered", {"value": "second"}),
                    Action.finish("recovered"),
                ],
                name="metered-agent",
                version="1",
            ),
            environment=environment,
            evaluator=ExactEvaluator("recovered", version="1"),
            config=TrialConfig(trial_id="metered-1", max_actions=3),
        ).run()

        assert calls == 1
        outcomes = [
            record.payload
            for record in result.trajectory.records
            if record.kind == "tool.call.outcome"
        ]
        assert [outcome["status"] for outcome in outcomes] == [
            "succeeded",
            "budget_exhausted",
        ]
        assert outcomes[0]["budget_charged"] == {
            "tokens": 2,
            "cost_microunits": 3,
        }
        assert outcomes[1]["error_code"] == "usage_budget_exhausted"
        assert replay(result.trajectory) == result

    asyncio.run(scenario())


def test_every_nonfinal_attempt_consumes_the_call_budget() -> None:
    calls = 0

    async def effect(arguments: Mapping[str, object]) -> ToolResult:
        nonlocal calls
        calls += 1
        return ToolResult(output=arguments)

    async def scenario() -> None:
        environment = ControlledToolEnvironment(
            tools=(
                Tool(
                    ToolSpec(
                        name="declared",
                        version="1",
                        input_schema={
                            "type": "object",
                            "properties": {},
                            "additionalProperties": False,
                        },
                        permission_name="fixture.read",
                    ),
                    effect,
                ),
            ),
            policy=ExecutionPolicy(
                version="1",
                allowed_tools=("declared",),
                allowed_permissions=("fixture.read",),
            ),
            budget=ExecutionBudget(
                max_tool_calls=1,
                max_tokens=0,
                max_cost_microunits=0,
                tool_timeout_seconds=1,
                currency="USD",
                pricing_version="fixture-1",
            ),
            name="attempt-budget",
            version="1",
        )
        result = await Trial(
            task=Task(id="attempt-budget", input=None),
            agent=ScriptedAgent(
                [
                    Action.invoke("unknown"),
                    Action.invoke("declared"),
                    Action.finish("done"),
                ],
                name="attempt-budget-agent",
                version="1",
            ),
            environment=environment,
            evaluator=ExactEvaluator("done", version="1"),
            config=TrialConfig(trial_id="attempt-budget-1", max_actions=3),
        ).run()

        assert calls == 0
        outcomes = [
            record.payload
            for record in result.trajectory.records
            if record.kind == "tool.call.outcome"
        ]
        assert [outcome["error_code"] for outcome in outcomes] == [
            "unknown_tool",
            "call_budget_exhausted",
        ]
        assert replay(result.trajectory) == result

    asyncio.run(scenario())


def test_usage_beyond_a_reservation_is_an_audited_adapter_failure() -> None:
    calls = 0

    async def underdeclared(arguments: Mapping[str, object]) -> ToolResult:
        nonlocal calls
        calls += 1
        return ToolResult(output=arguments, tokens=2, cost_microunits=2)

    async def scenario() -> None:
        environment = ControlledToolEnvironment(
            tools=(
                Tool(
                    ToolSpec(
                        name="underdeclared",
                        version="1",
                        input_schema={
                            "type": "object",
                            "properties": {},
                            "additionalProperties": False,
                        },
                        permission_name="fixture.read",
                        reserved_tokens=1,
                        reserved_cost_microunits=1,
                    ),
                    underdeclared,
                ),
            ),
            policy=ExecutionPolicy(
                version="1",
                allowed_tools=("underdeclared",),
                allowed_permissions=("fixture.read",),
            ),
            budget=ExecutionBudget(
                max_tool_calls=2,
                max_tokens=1,
                max_cost_microunits=1,
                tool_timeout_seconds=1,
                currency="USD",
                pricing_version="fixture-1",
            ),
            name="underdeclared",
            version="1",
        )
        result = await Trial(
            task=Task(id="underdeclared", input=None),
            agent=ScriptedAgent(
                [
                    Action.invoke("underdeclared"),
                    Action.invoke("underdeclared"),
                    Action.finish("recovered"),
                ],
                name="underdeclared-agent",
                version="1",
            ),
            environment=environment,
            evaluator=ExactEvaluator("recovered", version="1"),
            config=TrialConfig(trial_id="underdeclared-1", max_actions=3),
        ).run()

        assert calls == 1
        outcomes = [
            record.payload
            for record in result.trajectory.records
            if record.kind == "tool.call.outcome"
        ]
        assert [outcome["status"] for outcome in outcomes] == [
            "failed",
            "budget_exhausted",
        ]
        assert outcomes[0]["error_code"] == "usage_exceeded_reservation"
        assert outcomes[0]["usage"] == {"tokens": 2, "cost_microunits": 2}
        assert outcomes[0]["budget_charged"] == {
            "tokens": 2,
            "cost_microunits": 2,
        }
        assert outcomes[1]["error_code"] == "usage_budget_exhausted"
        assert replay(result.trajectory) == result

    asyncio.run(scenario())


def test_timeout_and_callback_failure_are_recoverable_environment_outcomes() -> None:
    invalid_output_effects = 0
    deeply_nested_output_effects = 0
    invalid_usage_effects = 0

    class CallbackBaseError(BaseException):
        pass

    async def slow(arguments: Mapping[str, object]) -> ToolResult:
        del arguments
        await asyncio.Event().wait()
        raise AssertionError("unreachable")

    async def broken(arguments: Mapping[str, object]) -> ToolResult:
        del arguments
        raise RuntimeError("secret provider detail")

    async def broken_base(arguments: Mapping[str, object]) -> ToolResult:
        del arguments
        raise CallbackBaseError("base callback failure")

    async def provider_timeout(arguments: Mapping[str, object]) -> ToolResult:
        del arguments
        raise TimeoutError("provider timeout, not Harness timeout")

    async def callback_cancel(arguments: Mapping[str, object]) -> ToolResult:
        del arguments
        raise asyncio.CancelledError

    async def invalid_output(arguments: Mapping[str, object]) -> ToolResult:
        nonlocal invalid_output_effects
        del arguments
        invalid_output_effects += 1
        return ToolResult(output="\ud800")

    async def deeply_nested_output(arguments: Mapping[str, object]) -> ToolResult:
        nonlocal deeply_nested_output_effects
        del arguments
        deeply_nested_output_effects += 1
        nested: object = "leaf"
        for _ in range(126):
            nested = [nested]
        return ToolResult(output=nested)

    async def invalid_usage(arguments: Mapping[str, object]) -> ToolResult:
        nonlocal invalid_usage_effects
        del arguments
        invalid_usage_effects += 1
        return ToolResult(output=None, tokens=10**5000)

    def environment(name: str, handler: object) -> ControlledToolEnvironment:
        return ControlledToolEnvironment(
            tools=(
                Tool(
                    ToolSpec(
                        name=name,
                        version="1",
                        input_schema={
                            "type": "object",
                            "properties": {},
                            "additionalProperties": False,
                        },
                        permission_name="fixture.read",
                    ),
                    handler,  # type: ignore[arg-type]
                ),
            ),
            policy=ExecutionPolicy(
                version="1",
                allowed_tools=(name,),
                allowed_permissions=("fixture.read",),
            ),
            budget=ExecutionBudget(
                max_tool_calls=1,
                max_tokens=0,
                max_cost_microunits=0,
                tool_timeout_seconds=0.01,
                currency="USD",
                pricing_version="fixture-1",
            ),
            name=f"{name}-environment",
            version="1",
        )

    async def run(name: str, handler: object, trial_id: str) -> object:
        return await Trial(
            task=Task(id=trial_id, input=None),
            agent=ScriptedAgent(
                [Action.invoke(name), Action.finish("recovered")],
                name=f"{name}-agent",
                version="1",
            ),
            environment=environment(name, handler),
            evaluator=ExactEvaluator("recovered", version="1"),
            config=TrialConfig(trial_id=trial_id, max_actions=2),
        ).run()

    async def scenario() -> None:
        timed_out = await run("slow", slow, "timeout-1")
        failed = await run("broken", broken, "failure-1")
        base_failed = await run("broken-base", broken_base, "base-failure-1")
        provider_failed = await run(
            "provider-timeout",
            provider_timeout,
            "provider-timeout-1",
        )
        callback_cancelled = await run(
            "callback-cancel",
            callback_cancel,
            "callback-cancel-1",
        )
        invalid = await run("invalid-output", invalid_output, "invalid-output-1")
        too_deep = await run(
            "deeply-nested-output",
            deeply_nested_output,
            "deeply-nested-output-1",
        )
        invalid_usage_result = await run(
            "invalid-usage",
            invalid_usage,
            "invalid-usage-1",
        )

        assert timed_out.status is TrialStatus.COMPLETED
        assert failed.status is TrialStatus.COMPLETED
        assert base_failed.status is TrialStatus.COMPLETED
        assert provider_failed.status is TrialStatus.COMPLETED
        assert callback_cancelled.status is TrialStatus.COMPLETED
        assert invalid.status is TrialStatus.COMPLETED
        assert too_deep.status is TrialStatus.COMPLETED
        assert invalid_usage_result.status is TrialStatus.COMPLETED
        timeout_outcome = next(
            record.payload
            for record in timed_out.trajectory.records
            if record.kind == "tool.call.outcome"
        )
        failure_outcome = next(
            record.payload
            for record in failed.trajectory.records
            if record.kind == "tool.call.outcome"
        )
        base_failure_outcome = next(
            record.payload
            for record in base_failed.trajectory.records
            if record.kind == "tool.call.outcome"
        )
        provider_failure_outcome = next(
            record.payload
            for record in provider_failed.trajectory.records
            if record.kind == "tool.call.outcome"
        )
        callback_cancel_outcome = next(
            record.payload
            for record in callback_cancelled.trajectory.records
            if record.kind == "tool.call.outcome"
        )
        invalid_outcome = next(
            record.payload
            for record in invalid.trajectory.records
            if record.kind == "tool.call.outcome"
        )
        too_deep_outcome = next(
            record.payload
            for record in too_deep.trajectory.records
            if record.kind == "tool.call.outcome"
        )
        invalid_usage_outcome = next(
            record.payload
            for record in invalid_usage_result.trajectory.records
            if record.kind == "tool.call.outcome"
        )
        assert timeout_outcome["status"] == "timed_out"
        assert timeout_outcome["error_code"] == "tool_timed_out"
        assert failure_outcome["status"] == "failed"
        assert failure_outcome["error_code"] == "tool_failed"
        assert base_failure_outcome["status"] == "failed"
        assert base_failure_outcome["error_code"] == "tool_failed"
        assert provider_failure_outcome["status"] == "failed"
        assert provider_failure_outcome["error_code"] == "tool_failed"
        assert callback_cancel_outcome["status"] == "failed"
        assert callback_cancel_outcome["error_code"] == "tool_failed"
        assert invalid_outcome["status"] == "failed"
        assert invalid_outcome["error_code"] == "tool_failed"
        assert too_deep_outcome["status"] == "failed"
        assert too_deep_outcome["error_code"] == "tool_failed"
        assert invalid_usage_outcome["status"] == "failed"
        assert invalid_usage_outcome["error_code"] == "tool_failed"
        assert invalid_output_effects == 1
        assert deeply_nested_output_effects == 1
        assert invalid_usage_effects == 1
        assert "secret provider detail" not in failure_outcome["message"]
        assert replay(timed_out.trajectory) == timed_out
        assert replay(failed.trajectory) == failed
        assert replay(base_failed.trajectory) == base_failed
        assert replay(provider_failed.trajectory) == provider_failed
        assert replay(callback_cancelled.trajectory) == callback_cancelled
        assert replay(invalid.trajectory) == invalid
        assert replay(too_deep.trajectory) == too_deep
        assert replay(invalid_usage_result.trajectory) == invalid_usage_result

    asyncio.run(scenario())


def test_approver_callback_errors_are_denials_not_harness_timeouts() -> None:
    calls = 0

    class CallbackBaseError(BaseException):
        pass

    class ProviderTimeoutApprover:
        name = "provider-timeout-approver"
        version = "1"
        configuration: dict[str, object] = {}

        async def decide(self, request: ApprovalRequest) -> ApprovalDecision:
            del request
            raise TimeoutError("provider timeout, not Harness timeout")

    class InvalidReasonApprover:
        name = "invalid-reason-approver"
        version = "1"
        configuration: dict[str, object] = {}

        async def decide(self, request: ApprovalRequest) -> ApprovalDecision:
            return ApprovalDecision.approve(request, reason="\ud800")

    class CallbackCancelApprover:
        name = "callback-cancel-approver"
        version = "1"
        configuration: dict[str, object] = {}

        async def decide(self, request: ApprovalRequest) -> ApprovalDecision:
            del request
            raise asyncio.CancelledError

    class CallbackBaseErrorApprover:
        name = "callback-base-error-approver"
        version = "1"
        configuration: dict[str, object] = {}

        async def decide(self, request: ApprovalRequest) -> ApprovalDecision:
            del request
            raise CallbackBaseError("base callback failure")

    class BlockingPostcheckApprover:
        name = "blocking-postcheck-approver"
        version = "1"

        def __init__(self) -> None:
            self.reads = 0

        @property
        def configuration(self) -> dict[str, object]:
            self.reads += 1
            if self.reads == 3:
                time.sleep(0.02)
            return {}

        async def decide(self, request: ApprovalRequest) -> ApprovalDecision:
            return ApprovalDecision.approve(request)

    async def effect(arguments: Mapping[str, object]) -> ToolResult:
        nonlocal calls
        calls += 1
        return ToolResult(output=arguments)

    async def run(
        approver: object,
        trial_id: str,
        *,
        timeout: float = 1,
    ) -> TrialResult:
        return await Trial(
            task=Task(id=trial_id, input=None),
            agent=ScriptedAgent(
                [Action.invoke("write"), Action.finish("recovered")],
                name=f"{trial_id}-agent",
                version="1",
            ),
            environment=ControlledToolEnvironment(
                tools=(
                    Tool(
                        ToolSpec(
                            name="write",
                            version="1",
                            input_schema={
                                "type": "object",
                                "properties": {},
                                "additionalProperties": False,
                            },
                            permission_name="fixture.write",
                            requires_approval=True,
                        ),
                        effect,
                    ),
                ),
                policy=ExecutionPolicy(
                    version="1",
                    allowed_tools=("write",),
                    allowed_permissions=("fixture.write",),
                ),
                budget=ExecutionBudget(
                    max_tool_calls=1,
                    max_tokens=0,
                    max_cost_microunits=0,
                    tool_timeout_seconds=timeout,
                    currency="USD",
                    pricing_version="fixture-1",
                ),
                approver=approver,  # type: ignore[arg-type]
                name=f"{trial_id}-environment",
                version="1",
            ),
            evaluator=ExactEvaluator("recovered", version="1"),
            config=TrialConfig(trial_id=trial_id, max_actions=2),
        ).run()

    async def scenario() -> None:
        provider_failure = await run(
            ProviderTimeoutApprover(),
            "approval-provider-timeout",
        )
        invalid_reason = await run(
            InvalidReasonApprover(),
            "approval-invalid-reason",
        )
        callback_cancel = await run(
            CallbackCancelApprover(),
            "approval-callback-cancel",
        )
        callback_base_error = await run(
            CallbackBaseErrorApprover(),
            "approval-callback-base-error",
        )
        postcheck_timeout = await run(
            BlockingPostcheckApprover(),
            "approval-blocking-postcheck",
            timeout=0.005,
        )

        assert calls == 0
        for result in (
            provider_failure,
            invalid_reason,
            callback_cancel,
            callback_base_error,
        ):
            assert result.status is TrialStatus.COMPLETED
            outcome = next(
                record.payload
                for record in result.trajectory.records
                if record.kind == "tool.call.outcome"
            )
            assert outcome["status"] == "denied"
            assert outcome["error_code"] == "approval_failed"
            assert outcome["approval"]["status"] == "failed"
            assert replay(result.trajectory) == result

        postcheck_outcome = next(
            record.payload
            for record in postcheck_timeout.trajectory.records
            if record.kind == "tool.call.outcome"
        )
        assert postcheck_timeout.status is TrialStatus.COMPLETED
        assert postcheck_outcome["status"] == "timed_out"
        assert postcheck_outcome["error_code"] == "approval_timed_out"
        assert postcheck_outcome["approval"]["status"] == "timed_out"
        assert postcheck_outcome["budget_charged"] == {
            "tokens": 0,
            "cost_microunits": 0,
        }
        assert replay(postcheck_timeout.trajectory) == postcheck_timeout

    asyncio.run(scenario())


def test_late_tool_or_approval_return_cannot_turn_a_timeout_into_success() -> None:
    tool_calls = 0

    async def late_tool(arguments: Mapping[str, object]) -> ToolResult:
        nonlocal tool_calls
        tool_calls += 1
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            await asyncio.sleep(0.02)
            return ToolResult(output=arguments)
        raise AssertionError("unreachable")

    async def late_tool_error(arguments: Mapping[str, object]) -> ToolResult:
        nonlocal tool_calls
        del arguments
        tool_calls += 1
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            await asyncio.sleep(0.02)
            raise RuntimeError("late Tool failure")
        raise AssertionError("unreachable")

    async def late_tool_over_reservation(
        arguments: Mapping[str, object],
    ) -> ToolResult:
        nonlocal tool_calls
        del arguments
        tool_calls += 1
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            await asyncio.sleep(0.02)
            return ToolResult(output=None, tokens=1, cost_microunits=1)
        raise AssertionError("unreachable")

    async def blocking_late_tool_over_reservation(
        arguments: Mapping[str, object],
    ) -> ToolResult:
        nonlocal tool_calls
        del arguments
        tool_calls += 1
        time.sleep(0.02)
        return ToolResult(output=None, tokens=1, cost_microunits=1)

    class LateApprover:
        name = "late-approver"
        version = "1"
        configuration: dict[str, object] = {}

        def __init__(self, *, fail_late: bool = False) -> None:
            self.fail_late = fail_late

        async def decide(self, request: ApprovalRequest) -> ApprovalDecision:
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                await asyncio.sleep(0.02)
                if self.fail_late:
                    raise RuntimeError("late Approver failure")
                return ApprovalDecision.approve(
                    request,
                )
            raise AssertionError("unreachable")

    def trial(
        *,
        approval: bool,
        trial_id: str,
        handler: object = late_tool,
        approver_fails_late: bool = False,
        repeat: bool = False,
    ) -> Trial:
        return Trial(
            task=Task(id=trial_id, input=None),
            agent=ScriptedAgent(
                [Action.invoke("late")]
                + ([Action.invoke("late")] if repeat else [])
                + [Action.finish("recovered")],
                name="late-agent",
                version="1",
            ),
            environment=ControlledToolEnvironment(
                tools=(
                    Tool(
                        ToolSpec(
                            name="late",
                            version="1",
                            input_schema={
                                "type": "object",
                                "properties": {},
                                "additionalProperties": False,
                            },
                            permission_name="fixture.read",
                            requires_approval=approval,
                        ),
                        handler,  # type: ignore[arg-type]
                    ),
                ),
                policy=ExecutionPolicy(
                    version="1",
                    allowed_tools=("late",),
                    allowed_permissions=("fixture.read",),
                ),
                budget=ExecutionBudget(
                    max_tool_calls=2 if repeat else 1,
                    max_tokens=0,
                    max_cost_microunits=0,
                    tool_timeout_seconds=0.005,
                    currency="USD",
                    pricing_version="fixture-1",
                ),
                approver=(
                    LateApprover(fail_late=approver_fails_late)
                    if approval
                    else None
                ),
                name="late-environment",
                version="1",
            ),
            evaluator=ExactEvaluator("recovered", version="1"),
            config=TrialConfig(trial_id=trial_id, max_actions=3 if repeat else 2),
        )

    async def scenario() -> None:
        late_result = await trial(approval=False, trial_id="late-tool-1").run()
        approval_result = await trial(approval=True, trial_id="late-approval-1").run()
        late_error_result = await trial(
            approval=False,
            trial_id="late-tool-error-1",
            handler=late_tool_error,
        ).run()
        approval_error_result = await trial(
            approval=True,
            trial_id="late-approval-error-1",
            approver_fails_late=True,
        ).run()
        late_over_reservation_result = await trial(
            approval=False,
            trial_id="late-tool-over-reservation-1",
            handler=late_tool_over_reservation,
            repeat=True,
        ).run()
        blocking_late_over_reservation_result = await trial(
            approval=False,
            trial_id="blocking-late-tool-over-reservation-1",
            handler=blocking_late_tool_over_reservation,
            repeat=True,
        ).run()

        late_outcome = next(
            record.payload
            for record in late_result.trajectory.records
            if record.kind == "tool.call.outcome"
        )
        approval_outcome = next(
            record.payload
            for record in approval_result.trajectory.records
            if record.kind == "tool.call.outcome"
        )
        late_error_outcome = next(
            record.payload
            for record in late_error_result.trajectory.records
            if record.kind == "tool.call.outcome"
        )
        approval_error_outcome = next(
            record.payload
            for record in approval_error_result.trajectory.records
            if record.kind == "tool.call.outcome"
        )
        late_over_reservation_outcomes = [
            record.payload
            for record in late_over_reservation_result.trajectory.records
            if record.kind == "tool.call.outcome"
        ]
        blocking_late_over_reservation_outcomes = [
            record.payload
            for record in blocking_late_over_reservation_result.trajectory.records
            if record.kind == "tool.call.outcome"
        ]
        assert late_outcome["status"] == "timed_out"
        assert late_outcome["error_code"] == "tool_timed_out"
        assert approval_outcome["status"] == "timed_out"
        assert approval_outcome["error_code"] == "approval_timed_out"
        assert late_error_outcome["status"] == "timed_out"
        assert late_error_outcome["error_code"] == "tool_timed_out"
        assert approval_error_outcome["status"] == "timed_out"
        assert approval_error_outcome["error_code"] == "approval_timed_out"
        assert [outcome["status"] for outcome in late_over_reservation_outcomes] == [
            "failed",
            "budget_exhausted",
        ]
        assert late_over_reservation_outcomes[0]["error_code"] == (
            "usage_exceeded_reservation"
        )
        assert late_over_reservation_outcomes[0]["usage"] == {
            "tokens": 1,
            "cost_microunits": 1,
        }
        assert late_over_reservation_outcomes[0]["budget_charged"] == {
            "tokens": 1,
            "cost_microunits": 1,
        }
        assert late_over_reservation_outcomes[1]["error_code"] == (
            "usage_budget_exhausted"
        )
        assert [
            outcome["status"] for outcome in blocking_late_over_reservation_outcomes
        ] == ["failed", "budget_exhausted"]
        assert blocking_late_over_reservation_outcomes[0]["error_code"] == (
            "usage_exceeded_reservation"
        )
        assert blocking_late_over_reservation_outcomes[1]["error_code"] == (
            "usage_budget_exhausted"
        )
        assert tool_calls == 4
        assert replay(late_result.trajectory) == late_result
        assert replay(approval_result.trajectory) == approval_result
        assert replay(late_error_result.trajectory) == late_error_result
        assert replay(approval_error_result.trajectory) == approval_error_result
        assert replay(late_over_reservation_result.trajectory) == (
            late_over_reservation_result
        )
        assert replay(blocking_late_over_reservation_result.trajectory) == (
            blocking_late_over_reservation_result
        )

    asyncio.run(scenario())


def test_cancellation_during_tool_records_one_outcome_before_trial_cancellation() -> None:
    started: asyncio.Event

    async def blocking(arguments: Mapping[str, object]) -> ToolResult:
        del arguments
        started.set()
        await asyncio.Event().wait()
        raise AssertionError("unreachable")

    async def scenario() -> None:
        nonlocal started
        started = asyncio.Event()
        trial = Trial(
            task=Task(id="cancel-tool", input=None),
            agent=ScriptedAgent(
                [Action.invoke("blocking")],
                name="cancel-tool-agent",
                version="1",
            ),
            environment=ControlledToolEnvironment(
                tools=(
                    Tool(
                        ToolSpec(
                            name="blocking",
                            version="1",
                            input_schema={
                                "type": "object",
                                "properties": {},
                                "additionalProperties": False,
                            },
                            permission_name="fixture.read",
                        ),
                        blocking,
                    ),
                ),
                policy=ExecutionPolicy(
                    version="1",
                    allowed_tools=("blocking",),
                    allowed_permissions=("fixture.read",),
                ),
                budget=ExecutionBudget(
                    max_tool_calls=1,
                    max_tokens=0,
                    max_cost_microunits=0,
                    tool_timeout_seconds=30,
                    currency="USD",
                    pricing_version="fixture-1",
                ),
                name="cancel-tool",
                version="1",
            ),
            evaluator=ExactEvaluator(None, version="1"),
            config=TrialConfig(trial_id="cancel-tool-1", max_actions=1),
        )
        running = asyncio.create_task(trial.run())
        await started.wait()
        running.cancel()
        try:
            await running
        except asyncio.CancelledError:
            pass
        else:
            raise AssertionError("Trial cancellation did not propagate")

        assert [record.kind for record in trial.trajectory.records] == [
            "trial.started",
            "environment.reset",
            "agent.action",
            "tool.call.outcome",
            "trial.cancelled",
            "trial.terminated",
        ]
        assert trial.trajectory.records[3].payload["status"] == "cancelled"
        assert replay(trial.trajectory).status is TrialStatus.CANCELLED

        forged_records = list(trial.trajectory.records)
        forged_records[-2] = replace(
            forged_records[-2],
            kind="trial.failure",
            payload={
                "phase": "environment",
                "code": "environment_step_error",
                "exception_type": "RuntimeError",
                "message": "forged failure",
            },
        )
        forged_records[-1] = replace(
            forged_records[-1],
            payload={"status": "failed", "phase": "environment"},
        )
        forged = _with_records(trial.trajectory, forged_records)
        with pytest.raises(ValueError, match="invalid Trajectory causal order"):
            replay(forged)

    asyncio.run(scenario())


def test_agent_cannot_swallow_caller_cancellation_and_start_a_tool() -> None:
    started: asyncio.Event
    effects = 0

    class CallbackBaseError(BaseException):
        pass

    class SwallowingAgent:
        version = "1"
        configuration: dict[str, object] = {}

        def __init__(self, mode: str) -> None:
            self.mode = mode
            self.name = f"swallow-cancel-{mode}"

        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                if self.mode == "return":
                    return Action.invoke("effect")
                if self.mode == "uncancel-return":
                    current = asyncio.current_task()
                    if current is None:
                        raise AssertionError("Agent callback has no current Task")
                    current.uncancel()
                    return Action.invoke("effect")
                if self.mode == "error":
                    raise RuntimeError("callback replaced cancellation")
                raise CallbackBaseError("callback replaced cancellation")
            raise AssertionError("unreachable")

    async def effect(arguments: Mapping[str, object]) -> ToolResult:
        nonlocal effects
        effects += 1
        return ToolResult(output=arguments)

    def trial(mode: str) -> Trial:
        return Trial(
            task=Task(id=f"swallow-cancel-{mode}", input=None),
            agent=SwallowingAgent(mode),
            environment=ControlledToolEnvironment(
                tools=(
                    Tool(
                        ToolSpec(
                            name="effect",
                            version="1",
                            input_schema={
                                "type": "object",
                                "properties": {},
                                "additionalProperties": False,
                            },
                            permission_name="fixture.write",
                        ),
                        effect,
                    ),
                ),
                policy=ExecutionPolicy(
                    version="1",
                    allowed_tools=("effect",),
                    allowed_permissions=("fixture.write",),
                ),
                budget=ExecutionBudget(
                    max_tool_calls=1,
                    max_tokens=0,
                    max_cost_microunits=0,
                    tool_timeout_seconds=1,
                    currency="USD",
                    pricing_version="fixture-1",
                ),
                name=f"swallow-cancel-{mode}",
                version="1",
            ),
            evaluator=ExactEvaluator(None, version="1"),
            config=TrialConfig(trial_id=f"swallow-cancel-{mode}-1", max_actions=1),
        )

    async def scenario() -> None:
        nonlocal started
        for mode in ("return", "uncancel-return", "error", "base-error"):
            started = asyncio.Event()
            current = trial(mode)
            running = asyncio.create_task(current.run())
            await started.wait()
            running.cancel()
            with pytest.raises(asyncio.CancelledError):
                await running
            assert [record.kind for record in current.trajectory.records][-2:] == [
                "trial.cancelled",
                "trial.terminated",
            ]
            assert replay(current.trajectory).status is TrialStatus.CANCELLED
        assert effects == 0

    asyncio.run(scenario())


def test_cancellation_during_timeout_cleanup_remains_caller_cancellation() -> None:
    cleanup_started: asyncio.Event
    approval_cleanup_started: asyncio.Event
    calls = 0
    fail_tool_cleanup = False
    fail_approval_cleanup = False

    async def slow_cleanup(arguments: Mapping[str, object]) -> ToolResult:
        del arguments
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cleanup_started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                if fail_tool_cleanup:
                    raise RuntimeError("late Tool cleanup failed")
                return ToolResult(output="ignored late result")
        raise AssertionError("unreachable")

    class SlowCleanupApprover:
        name = "slow-cleanup-approver"
        version = "1"
        configuration: dict[str, object] = {}

        async def decide(self, request: ApprovalRequest) -> ApprovalDecision:
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                approval_cleanup_started.set()
                try:
                    await asyncio.Event().wait()
                except asyncio.CancelledError:
                    if fail_approval_cleanup:
                        raise RuntimeError("late Approval cleanup failed")
                    return ApprovalDecision.approve(request)
            raise AssertionError("unreachable")

    async def effect(arguments: Mapping[str, object]) -> ToolResult:
        nonlocal calls
        calls += 1
        return ToolResult(output=arguments)

    def tool_cleanup_trial(trial_id: str) -> Trial:
        return Trial(
            task=Task(id=trial_id, input=None),
            agent=ScriptedAgent(
                [Action.invoke("slow-cleanup")],
                name="cancel-timeout-cleanup-agent",
                version="1",
            ),
            environment=ControlledToolEnvironment(
                tools=(
                    Tool(
                        ToolSpec(
                            name="slow-cleanup",
                            version="1",
                            input_schema={
                                "type": "object",
                                "properties": {},
                                "additionalProperties": False,
                            },
                            permission_name="fixture.read",
                        ),
                        slow_cleanup,
                    ),
                ),
                policy=ExecutionPolicy(
                    version="1",
                    allowed_tools=("slow-cleanup",),
                    allowed_permissions=("fixture.read",),
                ),
                budget=ExecutionBudget(
                    max_tool_calls=1,
                    max_tokens=0,
                    max_cost_microunits=0,
                    tool_timeout_seconds=0.005,
                    currency="USD",
                    pricing_version="fixture-1",
                ),
                name="cancel-timeout-cleanup",
                version="1",
            ),
            evaluator=ExactEvaluator(None, version="1"),
            config=TrialConfig(trial_id=trial_id, max_actions=1),
        )

    async def scenario() -> None:
        nonlocal cleanup_started, approval_cleanup_started, fail_tool_cleanup
        cleanup_started = asyncio.Event()
        approval_cleanup_started = asyncio.Event()
        trial = tool_cleanup_trial("cancel-timeout-cleanup-1")
        running = asyncio.create_task(trial.run())
        await cleanup_started.wait()
        running.cancel()
        with pytest.raises(asyncio.CancelledError):
            await running

        outcomes = [
            record.payload
            for record in trial.trajectory.records
            if record.kind == "tool.call.outcome"
        ]
        assert len(outcomes) == 1
        assert outcomes[0]["status"] == "cancelled"
        assert replay(trial.trajectory).status is TrialStatus.CANCELLED

        fail_tool_cleanup = True
        cleanup_started = asyncio.Event()
        failing_cleanup_trial = tool_cleanup_trial(
            "cancel-failing-timeout-cleanup-1"
        )
        failing_cleanup_running = asyncio.create_task(failing_cleanup_trial.run())
        await cleanup_started.wait()
        failing_cleanup_running.cancel()
        with pytest.raises(asyncio.CancelledError):
            await failing_cleanup_running
        failing_cleanup_outcomes = [
            record.payload
            for record in failing_cleanup_trial.trajectory.records
            if record.kind == "tool.call.outcome"
        ]
        assert len(failing_cleanup_outcomes) == 1
        assert failing_cleanup_outcomes[0]["status"] == "cancelled"
        assert replay(failing_cleanup_trial.trajectory).status is TrialStatus.CANCELLED

        approval_trial = Trial(
            task=Task(id="cancel-approval-timeout-cleanup", input=None),
            agent=ScriptedAgent(
                [Action.invoke("write")],
                name="cancel-approval-timeout-cleanup-agent",
                version="1",
            ),
            environment=ControlledToolEnvironment(
                tools=(
                    Tool(
                        ToolSpec(
                            name="write",
                            version="1",
                            input_schema={
                                "type": "object",
                                "properties": {},
                                "additionalProperties": False,
                            },
                            permission_name="fixture.write",
                            requires_approval=True,
                        ),
                        effect,
                    ),
                ),
                policy=ExecutionPolicy(
                    version="1",
                    allowed_tools=("write",),
                    allowed_permissions=("fixture.write",),
                ),
                budget=ExecutionBudget(
                    max_tool_calls=1,
                    max_tokens=0,
                    max_cost_microunits=0,
                    tool_timeout_seconds=0.005,
                    currency="USD",
                    pricing_version="fixture-1",
                ),
                approver=SlowCleanupApprover(),
                name="cancel-approval-timeout-cleanup",
                version="1",
            ),
            evaluator=ExactEvaluator(None, version="1"),
            config=TrialConfig(
                trial_id="cancel-approval-timeout-cleanup-1",
                max_actions=1,
            ),
        )
        approval_running = asyncio.create_task(approval_trial.run())
        await approval_cleanup_started.wait()
        approval_running.cancel()
        with pytest.raises(asyncio.CancelledError):
            await approval_running

        approval_outcomes = [
            record.payload
            for record in approval_trial.trajectory.records
            if record.kind == "tool.call.outcome"
        ]
        assert calls == 0
        assert len(approval_outcomes) == 1
        assert approval_outcomes[0]["status"] == "cancelled"
        assert replay(approval_trial.trajectory).status is TrialStatus.CANCELLED

    asyncio.run(scenario())


def test_cancellation_during_approval_never_starts_the_tool() -> None:
    approval_started: asyncio.Event
    calls = 0

    class BlockingApprover:
        name = "blocking-approver"
        version = "1"
        configuration: dict[str, object] = {}

        async def decide(self, request: ApprovalRequest) -> ApprovalDecision:
            del request
            approval_started.set()
            await asyncio.Event().wait()
            raise AssertionError("unreachable")

    async def effect(arguments: Mapping[str, object]) -> ToolResult:
        nonlocal calls
        calls += 1
        return ToolResult(output=arguments)

    async def scenario() -> None:
        nonlocal approval_started
        approval_started = asyncio.Event()
        trial = Trial(
            task=Task(id="cancel-approval", input=None),
            agent=ScriptedAgent(
                [Action.invoke("write")],
                name="cancel-approval-agent",
                version="1",
            ),
            environment=ControlledToolEnvironment(
                tools=(
                    Tool(
                        ToolSpec(
                            name="write",
                            version="1",
                            input_schema={
                                "type": "object",
                                "properties": {},
                                "additionalProperties": False,
                            },
                            permission_name="fixture.write",
                            requires_approval=True,
                        ),
                        effect,
                    ),
                ),
                policy=ExecutionPolicy(
                    version="1",
                    allowed_tools=("write",),
                    allowed_permissions=("fixture.write",),
                ),
                budget=ExecutionBudget(
                    max_tool_calls=1,
                    max_tokens=0,
                    max_cost_microunits=0,
                    tool_timeout_seconds=30,
                    currency="USD",
                    pricing_version="fixture-1",
                ),
                approver=BlockingApprover(),
                name="cancel-approval",
                version="1",
            ),
            evaluator=ExactEvaluator(None, version="1"),
            config=TrialConfig(trial_id="cancel-approval-1", max_actions=1),
        )
        running = asyncio.create_task(trial.run())
        await approval_started.wait()
        running.cancel()
        try:
            await running
        except asyncio.CancelledError:
            pass
        else:
            raise AssertionError("Trial cancellation did not propagate")

        assert calls == 0
        outcomes = [
            record for record in trial.trajectory.records if record.kind == "tool.call.outcome"
        ]
        assert len(outcomes) == 1
        assert outcomes[0].payload["status"] == "cancelled"
        assert outcomes[0].payload["budget_charged"] == {
            "tokens": 0,
            "cost_microunits": 0,
        }
        assert replay(trial.trajectory).status is TrialStatus.CANCELLED

    asyncio.run(scenario())


def test_replay_rejects_missing_duplicate_or_mismatched_tool_outcomes() -> None:
    async def effect(arguments: Mapping[str, object]) -> ToolResult:
        return ToolResult(output=arguments)

    async def original() -> Trajectory:
        result = await Trial(
            task=Task(id="tamper-tool", input=None),
            agent=ScriptedAgent(
                [Action.invoke("effect"), Action.finish("done")],
                name="tamper-tool-agent",
                version="1",
            ),
            environment=ControlledToolEnvironment(
                tools=(
                    Tool(
                        ToolSpec(
                            name="effect",
                            version="1",
                            input_schema={
                                "type": "object",
                                "properties": {},
                                "additionalProperties": False,
                            },
                            permission_name="fixture.read",
                        ),
                        effect,
                    ),
                ),
                policy=ExecutionPolicy(
                    version="1",
                    allowed_tools=("effect",),
                    allowed_permissions=("fixture.read",),
                ),
                budget=ExecutionBudget(
                    max_tool_calls=1,
                    max_tokens=0,
                    max_cost_microunits=0,
                    tool_timeout_seconds=1,
                    currency="USD",
                    pricing_version="fixture-1",
                ),
                name="tamper-tool",
                version="1",
            ),
            evaluator=ExactEvaluator("done", version="1"),
            config=TrialConfig(trial_id="tamper-tool-1", max_actions=2),
        ).run()
        return result.trajectory

    def with_records(
        trajectory: Trajectory,
        records: list[object],
    ) -> Trajectory:
        return replace(
            trajectory,
            records=tuple(
                replace(record, sequence=index)
                for index, record in enumerate(records)
            ),
        )

    trajectory = asyncio.run(original())
    records = list(trajectory.records)
    outcome_index = next(
        index for index, record in enumerate(records) if record.kind == "tool.call.outcome"
    )

    missing = with_records(trajectory, records[:outcome_index] + records[outcome_index + 1 :])
    duplicate = with_records(
        trajectory,
        records[: outcome_index + 1] + [records[outcome_index]] + records[outcome_index + 1 :],
    )
    wrong_name_record = replace(
        records[outcome_index],
        payload={**records[outcome_index].payload, "tool_name": "another-tool"},
    )
    wrong_name = with_records(
        trajectory,
        records[:outcome_index] + [wrong_name_record] + records[outcome_index + 1 :],
    )
    wrong_spec_record = replace(
        records[outcome_index],
        payload={
            **records[outcome_index].payload,
            "tool_spec_hash": "sha256:wrong",
        },
    )
    wrong_spec = with_records(
        trajectory,
        records[:outcome_index] + [wrong_spec_record] + records[outcome_index + 1 :],
    )
    wrong_approval_record = replace(
        records[outcome_index],
        payload={
            **records[outcome_index].payload,
            "approval": {
                "status": "approved",
                "approver": "forged",
                "approver_version": "1",
                "reason": "",
            },
        },
    )
    wrong_approval = with_records(
        trajectory,
        records[:outcome_index]
        + [wrong_approval_record]
        + records[outcome_index + 1 :],
    )
    wrong_approval_reason_record = replace(
        records[outcome_index],
        payload={
            **records[outcome_index].payload,
            "approval": {
                **records[outcome_index].payload["approval"],
                "reason": "forged",
            },
        },
    )
    wrong_approval_reason = with_records(
        trajectory,
        records[:outcome_index]
        + [wrong_approval_reason_record]
        + records[outcome_index + 1 :],
    )
    transition_index = next(
        index
        for index, record in enumerate(records[outcome_index + 1 :], outcome_index + 1)
        if record.kind == "environment.transition"
    )
    original_observation = records[transition_index].payload["observation"]
    original_tool_call = original_observation["tool_call"]
    wrong_observation_record = replace(
        records[transition_index],
        payload={
            **records[transition_index].payload,
            "observation": {
                "tool_call": {**original_tool_call, "output": "forged-output"}
            },
        },
    )
    wrong_observation = with_records(
        trajectory,
        records[:transition_index]
        + [wrong_observation_record]
        + records[transition_index + 1 :],
    )
    reset_index = next(
        index for index, record in enumerate(records) if record.kind == "environment.reset"
    )
    wrong_reset_record = replace(
        records[reset_index],
        payload={**records[reset_index].payload, "observation": {"forged": True}},
    )
    wrong_reset = with_records(
        trajectory,
        records[:reset_index] + [wrong_reset_record] + records[reset_index + 1 :],
    )

    for tampered in (
        missing,
        duplicate,
        wrong_name,
        wrong_spec,
        wrong_approval,
        wrong_approval_reason,
        wrong_observation,
        wrong_reset,
    ):
        with pytest.raises(ValueError, match="invalid Trajectory causal order"):
            replay(tampered)


def test_replay_rejects_noncanonical_or_orphan_control_declarations() -> None:
    async def unused(arguments: Mapping[str, object]) -> ToolResult:
        raise AssertionError(f"final-only Trial invoked a Tool: {arguments}")

    async def original() -> Trajectory:
        result = await Trial(
            task=Task(id="tamper-control-config", input=None),
            agent=ScriptedAgent(
                [Action.finish("done")],
                name="tamper-control-config-agent",
                version="1",
            ),
            environment=ControlledToolEnvironment(
                tools=(
                    Tool(
                        ToolSpec(
                            name="unused",
                            version="1",
                            input_schema={
                                "type": "object",
                                "properties": {},
                                "additionalProperties": False,
                            },
                            permission_name="fixture.read",
                            runtime_capabilities=("cap.a", "cap.z"),
                        ),
                        unused,
                    ),
                ),
                policy=ExecutionPolicy(
                    version="1",
                    allowed_tools=("unused",),
                    allowed_permissions=("fixture.read",),
                    allowed_runtime_capabilities=("cap.a", "cap.z"),
                ),
                budget=ExecutionBudget(
                    max_tool_calls=1,
                    max_tokens=0,
                    max_cost_microunits=0,
                    tool_timeout_seconds=1,
                    currency="USD",
                    pricing_version="fixture-1",
                ),
                name="tamper-control-config",
                version="1",
            ),
            evaluator=ExactEvaluator("done", version="1"),
            config=TrialConfig(trial_id="tamper-control-config-1", max_actions=1),
        ).run()
        return result.trajectory

    trajectory = asyncio.run(original())

    def forge_policy(**updates: JsonValue) -> Trajectory:
        configuration = cast(
            dict[str, JsonValue],
            _thaw_json(trajectory.configuration),
        )
        environment = cast(dict[str, JsonValue], configuration["environment"])
        controlled = cast(dict[str, JsonValue], environment["config"])
        policy = cast(dict[str, JsonValue], controlled["policy"])
        policy.update(updates)
        controlled["policy_hash"] = _hash_json_object(policy)
        return _with_configuration(trajectory, configuration)

    forged = [
        forge_policy(allowed_tools=["ghost"]),
        forge_policy(approval_required_tools=["ghost"]),
        forge_policy(approval_required_permissions=["fixture.write"]),
        forge_policy(allowed_permissions=["fixture.read", "fixture.read"]),
        forge_policy(allowed_runtime_capabilities=["cap.z", "cap.a"]),
    ]

    configuration = cast(dict[str, JsonValue], _thaw_json(trajectory.configuration))
    environment = cast(dict[str, JsonValue], configuration["environment"])
    controlled = cast(dict[str, JsonValue], environment["config"])
    tools = cast(list[JsonValue], controlled["tools"])
    tool = cast(dict[str, JsonValue], tools[0])
    tool["runtime_capabilities"] = ["cap.z", "cap.a"]
    forged.append(_with_configuration(trajectory, configuration))

    configuration = cast(dict[str, JsonValue], _thaw_json(trajectory.configuration))
    environment = cast(dict[str, JsonValue], configuration["environment"])
    controlled = cast(dict[str, JsonValue], environment["config"])
    budget = cast(dict[str, JsonValue], controlled["budget"])
    budget["tool_timeout_seconds"] = 1
    controlled["budget_hash"] = _hash_json_object(budget)
    forged.append(_with_configuration(trajectory, configuration))

    for tampered in forged:
        with pytest.raises(ValueError, match="invalid Trajectory causal order"):
            replay(tampered)


def test_replay_rejects_self_consistent_control_state_forgery() -> None:
    async def metered(arguments: Mapping[str, object]) -> ToolResult:
        return ToolResult(output=arguments.get("value"), tokens=1)

    class AlwaysApprover:
        name = "forge-approver"
        version = "1"
        configuration: dict[str, object] = {}

        async def decide(self, request: ApprovalRequest) -> ApprovalDecision:
            return ApprovalDecision.approve(request)

    async def run_case(
        *,
        trial_id: str,
        actions: list[Action],
        spec: ToolSpec,
        policy: ExecutionPolicy,
        max_tokens: int,
        approver: object | None = None,
    ) -> Trajectory:
        result = await Trial(
            task=Task(id=trial_id, input={"case": trial_id}),
            agent=ScriptedAgent(
                actions,
                name=f"{trial_id}-agent",
                version="1",
            ),
            environment=ControlledToolEnvironment(
                tools=(Tool(spec, metered),),
                policy=policy,
                budget=ExecutionBudget(
                    max_tool_calls=max(1, len(actions) - 1),
                    max_tokens=max_tokens,
                    max_cost_microunits=0,
                    tool_timeout_seconds=1,
                    currency="USD",
                    pricing_version="fixture-1",
                ),
                approver=approver,  # type: ignore[arg-type]
                name=f"{trial_id}-environment",
                version="1",
            ),
            evaluator=ExactEvaluator("done", version="1"),
            config=TrialConfig(trial_id=trial_id, max_actions=len(actions)),
        ).run()
        assert replay(result.trajectory) == result
        return result.trajectory

    plain_spec = ToolSpec(
        name="metered",
        version="1",
        input_schema={
            "type": "object",
            "properties": {"value": {"type": "integer"}},
            "required": ["value"],
            "additionalProperties": False,
        },
        permission_name="fixture.read",
        reserved_tokens=1,
    )
    plain_policy = ExecutionPolicy(
        version="1",
        allowed_tools=("metered",),
        allowed_permissions=("fixture.read",),
    )
    capability_spec = ToolSpec(
        name="metered",
        version="1",
        input_schema=plain_spec.input_schema,
        permission_name="fixture.read",
        runtime_capabilities=("network",),
        reserved_tokens=1,
    )
    approval_spec = ToolSpec(
        name="metered",
        version="1",
        input_schema=plain_spec.input_schema,
        permission_name="fixture.read",
        requires_approval=True,
        reserved_tokens=1,
    )

    async def originals() -> tuple[Trajectory, ...]:
        unknown = await run_case(
            trial_id="forge-unknown",
            actions=[Action.invoke("ghost"), Action.finish("done")],
            spec=plain_spec,
            policy=plain_policy,
            max_tokens=1,
        )
        invalid = await run_case(
            trial_id="forge-invalid",
            actions=[Action.invoke("metered", {"value": "1"}), Action.finish("done")],
            spec=plain_spec,
            policy=plain_policy,
            max_tokens=1,
        )
        denied = await run_case(
            trial_id="forge-policy",
            actions=[Action.invoke("metered", {"value": 1}), Action.finish("done")],
            spec=capability_spec,
            policy=plain_policy,
            max_tokens=1,
        )
        succeeded = await run_case(
            trial_id="forge-success",
            actions=[Action.invoke("metered", {"value": 1}), Action.finish("done")],
            spec=plain_spec,
            policy=plain_policy,
            max_tokens=1,
        )
        cumulative = await run_case(
            trial_id="forge-cumulative",
            actions=[
                Action.invoke("metered", {"value": 1}),
                Action.invoke("metered", {"value": 2}),
                Action.finish("done"),
            ],
            spec=plain_spec,
            policy=plain_policy,
            max_tokens=1,
        )
        approval_missing = await run_case(
            trial_id="forge-approval",
            actions=[Action.invoke("metered", {"value": 1}), Action.finish("done")],
            spec=approval_spec,
            policy=plain_policy,
            max_tokens=1,
        )
        approval_approved = await run_case(
            trial_id="forge-approval-declared",
            actions=[Action.invoke("metered", {"value": 1}), Action.finish("done")],
            spec=approval_spec,
            policy=plain_policy,
            max_tokens=1,
            approver=AlwaysApprover(),
        )
        return (
            unknown,
            invalid,
            denied,
            succeeded,
            cumulative,
            approval_missing,
            approval_approved,
        )

    (
        unknown,
        invalid,
        denied,
        succeeded,
        cumulative,
        approval_missing,
        approval_approved,
    ) = asyncio.run(originals())
    forged_success = {
        "status": "succeeded",
        "usage": {"tokens": 0, "cost_microunits": 0},
        "budget_charged": {"tokens": 0, "cost_microunits": 0},
        "error_code": None,
        "message": None,
    }
    forged = [
        _with_self_consistent_tool_outcome(unknown, **forged_success),
        _with_self_consistent_tool_outcome(invalid, **forged_success),
        _with_self_consistent_tool_outcome(denied, **forged_success),
        _with_self_consistent_tool_outcome(succeeded, request_hash=None),
        _with_self_consistent_tool_outcome(
            cumulative,
            outcome_number=1,
            **forged_success,
        ),
        _with_self_consistent_tool_outcome(
            approval_missing,
            status="denied",
            approval={
                "status": "failed",
                "approver": None,
                "approver_version": None,
                "reason": "",
            },
            error_code="approval_failed",
            message="Approver failed: RuntimeError",
        ),
        _with_self_consistent_tool_outcome(
            approval_approved,
            status="denied",
            approval={
                "status": "missing",
                "approver": None,
                "approver_version": None,
                "reason": "",
            },
            usage={"tokens": 0, "cost_microunits": 0},
            budget_charged={"tokens": 0, "cost_microunits": 0},
            error_code="approval_missing",
            message="Tool requires an Approver",
        ),
    ]

    split_records = list(denied.records)
    split_outcome_index = next(
        index
        for index, record in enumerate(split_records)
        if record.kind == "tool.call.outcome"
    )
    split_transition_index = next(
        index
        for index, record in enumerate(split_records[split_outcome_index + 1 :])
        if record.kind == "environment.transition"
    ) + split_outcome_index + 1
    split_transition = cast(
        dict[str, JsonValue],
        _thaw_json(split_records[split_transition_index].payload),
    )
    split_observation = cast(
        dict[str, JsonValue],
        split_transition["observation"],
    )
    split_tool_call = cast(dict[str, JsonValue], split_observation["tool_call"])
    split_tool_call["message"] = "forged observation detail"
    split_outcome = cast(
        dict[str, JsonValue],
        _thaw_json(split_records[split_outcome_index].payload),
    )
    split_outcome["observation_hash"] = _hash_json_object(
        {"observation": split_observation}
    )
    split_records[split_outcome_index] = replace(
        split_records[split_outcome_index],
        payload=split_outcome,
    )
    split_records[split_transition_index] = replace(
        split_records[split_transition_index],
        payload=split_transition,
    )
    forged.append(_with_records(denied, split_records))

    error_split_records = list(denied.records)
    error_split_transition = cast(
        dict[str, JsonValue],
        _thaw_json(error_split_records[split_transition_index].payload),
    )
    error_split_observation = cast(
        dict[str, JsonValue],
        error_split_transition["observation"],
    )
    error_split_tool_call = cast(
        dict[str, JsonValue],
        error_split_observation["tool_call"],
    )
    error_split_tool_call["error_code"] = "forged_error"
    error_split_outcome = cast(
        dict[str, JsonValue],
        _thaw_json(error_split_records[split_outcome_index].payload),
    )
    error_split_outcome["observation_hash"] = _hash_json_object(
        {"observation": error_split_observation}
    )
    error_split_records[split_outcome_index] = replace(
        error_split_records[split_outcome_index],
        payload=error_split_outcome,
    )
    error_split_records[split_transition_index] = replace(
        error_split_records[split_transition_index],
        payload=error_split_transition,
    )
    forged.append(_with_records(denied, error_split_records))

    denied_output_records = list(denied.records)
    denied_output_transition = cast(
        dict[str, JsonValue],
        _thaw_json(denied_output_records[split_transition_index].payload),
    )
    denied_output_observation = cast(
        dict[str, JsonValue],
        denied_output_transition["observation"],
    )
    denied_output_tool_call = cast(
        dict[str, JsonValue],
        denied_output_observation["tool_call"],
    )
    denied_output_tool_call["output"] = {"forged": "secret-from-denied-tool"}
    denied_output_outcome = cast(
        dict[str, JsonValue],
        _thaw_json(denied_output_records[split_outcome_index].payload),
    )
    denied_output_outcome["observation_hash"] = _hash_json_object(
        {"observation": denied_output_observation}
    )
    denied_output_records[split_outcome_index] = replace(
        denied_output_records[split_outcome_index],
        payload=denied_output_outcome,
    )
    denied_output_records[split_transition_index] = replace(
        denied_output_records[split_transition_index],
        payload=denied_output_transition,
    )
    forged.append(_with_records(denied, denied_output_records))

    failed_after_outcome_records = denied.records[:split_transition_index] + (
        replace(
            denied.records[split_transition_index],
            kind="trial.failure",
            payload={
                "phase": "environment",
                "code": "environment_step_error",
                "exception_type": "RuntimeError",
                "message": "forged failure after a committed outcome",
            },
        ),
        replace(
            denied.records[-1],
            payload={"status": "failed", "phase": "environment"},
        ),
    )
    forged.append(
        _with_records(denied, list(failed_after_outcome_records))
    )

    missing_field_records = list(succeeded.records)
    succeeded_outcome_index = next(
        index
        for index, record in enumerate(missing_field_records)
        if record.kind == "tool.call.outcome"
    )
    succeeded_transition_index = next(
        index
        for index, record in enumerate(
            missing_field_records[succeeded_outcome_index + 1 :]
        )
        if record.kind == "environment.transition"
    ) + succeeded_outcome_index + 1
    missing_field_outcome = cast(
        dict[str, JsonValue],
        _thaw_json(missing_field_records[succeeded_outcome_index].payload),
    )
    missing_field_transition = cast(
        dict[str, JsonValue],
        _thaw_json(missing_field_records[succeeded_transition_index].payload),
    )
    missing_field_observation = cast(
        dict[str, JsonValue],
        missing_field_transition["observation"],
    )
    missing_field_tool_call = cast(
        dict[str, JsonValue],
        missing_field_observation["tool_call"],
    )
    missing_field_outcome.pop("error_code")
    missing_field_outcome.pop("message")
    missing_field_tool_call.pop("error_code")
    missing_field_tool_call.pop("message")
    missing_field_tool_call.pop("output")
    missing_field_outcome["observation_hash"] = _hash_json_object(
        {"observation": missing_field_observation}
    )
    missing_field_records[succeeded_outcome_index] = replace(
        missing_field_records[succeeded_outcome_index],
        payload=missing_field_outcome,
    )
    missing_field_records[succeeded_transition_index] = replace(
        missing_field_records[succeeded_transition_index],
        payload=missing_field_transition,
    )
    forged.append(_with_records(succeeded, missing_field_records))

    extra_field_records = list(succeeded.records)
    extra_field_outcome = cast(
        dict[str, JsonValue],
        _thaw_json(extra_field_records[succeeded_outcome_index].payload),
    )
    extra_field_outcome["undeclared"] = "forged"
    extra_field_records[succeeded_outcome_index] = replace(
        extra_field_records[succeeded_outcome_index],
        payload=extra_field_outcome,
    )
    forged.append(_with_records(succeeded, extra_field_records))

    typed_split_records = list(succeeded.records)
    typed_split_transition = cast(
        dict[str, JsonValue],
        _thaw_json(typed_split_records[succeeded_transition_index].payload),
    )
    typed_split_observation = cast(
        dict[str, JsonValue],
        typed_split_transition["observation"],
    )
    typed_split_tool_call = cast(
        dict[str, JsonValue],
        typed_split_observation["tool_call"],
    )
    typed_split_usage = cast(
        dict[str, JsonValue],
        typed_split_tool_call["usage"],
    )
    typed_split_usage["tokens"] = True
    typed_split_outcome = cast(
        dict[str, JsonValue],
        _thaw_json(typed_split_records[succeeded_outcome_index].payload),
    )
    typed_split_outcome["observation_hash"] = _hash_json_object(
        {"observation": typed_split_observation}
    )
    typed_split_records[succeeded_outcome_index] = replace(
        typed_split_records[succeeded_outcome_index],
        payload=typed_split_outcome,
    )
    typed_split_records[succeeded_transition_index] = replace(
        typed_split_records[succeeded_transition_index],
        payload=typed_split_transition,
    )
    forged.append(_with_records(succeeded, typed_split_records))

    final_records = list(succeeded.records)
    final_action_index = max(
        index
        for index, record in enumerate(final_records)
        if record.kind == "agent.action"
    )
    final_transition_index = next(
        index
        for index, record in enumerate(final_records[final_action_index + 1 :])
        if record.kind == "environment.transition"
    ) + final_action_index + 1
    final_transition = cast(
        dict[str, JsonValue],
        _thaw_json(final_records[final_transition_index].payload),
    )
    final_transition["observation"] = "forged"
    final_transition["output"] = "forged"
    final_records[final_transition_index] = replace(
        final_records[final_transition_index],
        payload=final_transition,
    )
    forged.append(_with_records(succeeded, final_records))

    for tampered in forged:
        with pytest.raises(ValueError, match="invalid Trajectory causal order"):
            replay(tampered)


def test_persisted_experiment_resume_never_reexecutes_a_controlled_tool(tmp_path) -> None:
    first_calls = 0
    resumed_calls = 0

    async def first_handler(arguments: Mapping[str, object]) -> ToolResult:
        nonlocal first_calls
        first_calls += 1
        return ToolResult(output=arguments["value"])

    async def bomb_handler(arguments: Mapping[str, object]) -> ToolResult:
        nonlocal resumed_calls
        resumed_calls += 1
        raise AssertionError(f"re-executed persisted Tool: {arguments}")

    def experiment(handler: object) -> Experiment:
        environment = ControlledToolEnvironment(
            tools=(
                Tool(
                    ToolSpec(
                        name="persisted",
                        version="1",
                        input_schema={
                            "type": "object",
                            "properties": {"value": {"type": "string"}},
                            "required": ["value"],
                            "additionalProperties": False,
                        },
                        permission_name="fixture.read",
                    ),
                    handler,  # type: ignore[arg-type]
                ),
            ),
            policy=ExecutionPolicy(
                version="1",
                allowed_tools=("persisted",),
                allowed_permissions=("fixture.read",),
            ),
            budget=ExecutionBudget(
                max_tool_calls=1,
                max_tokens=0,
                max_cost_microunits=0,
                tool_timeout_seconds=1,
                currency="USD",
                pricing_version="fixture-1",
            ),
            name="persisted-environment",
            version="1",
        )
        trial = Trial(
            task=Task(id="persisted-tool", input=None),
            agent=ScriptedAgent(
                [Action.invoke("persisted", {"value": "ok"}), Action.finish("done")],
                name="persisted-tool-agent",
                version="1",
            ),
            environment=environment,
            evaluator=ExactEvaluator("done", version="1"),
            config=TrialConfig(trial_id="persisted-tool-1", max_actions=2),
        )
        return Experiment(
            experiment_id="persisted-controlled-tool",
            version="1",
            baseline="baseline",
            trials={"baseline": (trial,)},
        )

    async def scenario() -> None:
        path = tmp_path / "controlled.jsonl"
        first = await experiment(first_handler).run(JsonlTrajectoryStore(path))
        resumed = await experiment(bomb_handler).run(JsonlTrajectoryStore(path))

        assert first.complete is True
        assert resumed == first
        assert first_calls == 1
        assert resumed_calls == 0
        stored = JsonlTrajectoryStore(path).load()
        assert stored == first
        assert replay(stored.results["baseline"][0].trajectory).status is TrialStatus.COMPLETED

    asyncio.run(scenario())


def test_controlled_environment_is_single_use_and_rejects_duplicate_action_indexes() -> None:
    calls = 0

    async def effect(arguments: Mapping[str, object]) -> ToolResult:
        nonlocal calls
        calls += 1
        return ToolResult(output=arguments)

    async def scenario() -> None:
        environment = ControlledToolEnvironment(
            tools=(
                Tool(
                    ToolSpec(
                        name="effect",
                        version="1",
                        input_schema={
                            "type": "object",
                            "properties": {},
                            "additionalProperties": False,
                        },
                        permission_name="fixture.read",
                    ),
                    effect,
                ),
            ),
            policy=ExecutionPolicy(
                version="1",
                allowed_tools=("effect",),
                allowed_permissions=("fixture.read",),
            ),
            budget=ExecutionBudget(
                max_tool_calls=2,
                max_tokens=0,
                max_cost_microunits=0,
                tool_timeout_seconds=1,
                currency="USD",
                pricing_version="fixture-1",
            ),
            name="single-use",
            version="1",
        )
        task = Task(id="single-use", input=None)
        await environment.reset(task, seed=0)
        await environment.step(Action.invoke("effect"), seed=0, action_index=0)
        assert environment._drain_trajectory_records() == ()
        assert environment._request_nonces == {}

        with pytest.raises(RuntimeError, match="action_index must be contiguous"):
            await environment.step(Action.invoke("effect"), seed=0, action_index=0)
        with pytest.raises(RuntimeError, match="single-use"):
            await environment.reset(task, seed=0)
        assert calls == 1

    asyncio.run(scenario())


def test_concurrent_steps_cannot_execute_after_a_final_action() -> None:
    started: asyncio.Event
    release: asyncio.Event
    calls = 0

    async def effect(arguments: Mapping[str, object]) -> ToolResult:
        nonlocal calls
        del arguments
        calls += 1
        if calls == 1:
            started.set()
            await release.wait()
        return ToolResult(output="effect")

    async def scenario() -> None:
        nonlocal started, release
        started = asyncio.Event()
        release = asyncio.Event()
        environment = ControlledToolEnvironment(
            tools=(
                Tool(
                    ToolSpec(
                        name="effect",
                        version="1",
                        input_schema={
                            "type": "object",
                            "properties": {},
                            "additionalProperties": False,
                        },
                        permission_name="fixture.read",
                    ),
                    effect,
                ),
            ),
            policy=ExecutionPolicy(
                version="1",
                allowed_tools=("effect",),
                allowed_permissions=("fixture.read",),
            ),
            budget=ExecutionBudget(
                max_tool_calls=2,
                max_tokens=0,
                max_cost_microunits=0,
                tool_timeout_seconds=1,
                currency="USD",
                pricing_version="fixture-1",
            ),
            name="concurrent-final",
            version="1",
        )
        await environment.reset(Task(id="concurrent-final", input=None), seed=0)
        first = asyncio.create_task(
            environment.step(Action.invoke("effect"), seed=0, action_index=0)
        )
        await started.wait()
        final = asyncio.create_task(
            environment.step(Action.finish("done"), seed=0, action_index=1)
        )
        await asyncio.sleep(0)
        after_final = asyncio.create_task(
            environment.step(Action.invoke("effect"), seed=0, action_index=2)
        )
        await asyncio.sleep(0)
        release.set()

        await first
        final_transition = await final
        assert final_transition.terminated is True
        with pytest.raises(RuntimeError, match="already terminated"):
            await after_final
        assert calls == 1

    asyncio.run(scenario())


def test_one_controlled_environment_cannot_be_bound_to_two_trials() -> None:
    async def effect(arguments: Mapping[str, object]) -> ToolResult:
        return ToolResult(output=arguments)

    environment = ControlledToolEnvironment(
        tools=(
            Tool(
                ToolSpec(
                    name="effect",
                    version="1",
                    input_schema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                    permission_name="fixture.read",
                ),
                effect,
            ),
        ),
        policy=ExecutionPolicy(
            version="1",
            allowed_tools=("effect",),
            allowed_permissions=("fixture.read",),
        ),
        budget=ExecutionBudget(
            max_tool_calls=1,
            max_tokens=0,
            max_cost_microunits=0,
            tool_timeout_seconds=1,
            currency="USD",
            pricing_version="fixture-1",
        ),
        name="one-binding",
        version="1",
    )

    def bind(trial_id: str) -> Trial:
        return Trial(
            task=Task(id="one-binding", input=None),
            agent=ScriptedAgent(
                [Action.finish("done")],
                name="one-binding-agent",
                version="1",
            ),
            environment=environment,
            evaluator=ExactEvaluator("done", version="1"),
            config=TrialConfig(trial_id=trial_id, max_actions=1),
        )

    first = bind("one-binding-1")
    with pytest.raises(RuntimeError, match="only one Trial"):
        bind("one-binding-2")
    assert first.trajectory.records == ()


def test_schema_enum_comparison_is_deep_and_preserves_large_integer_precision() -> None:
    huge = 10**400
    spec = ToolSpec(
        name="enum",
        version="1",
        input_schema={
            "type": "object",
            "properties": {
                "large": {"type": "integer", "enum": [huge]},
                "nested": {
                    "type": "object",
                    "enum": [{"flag": 1}],
                    "properties": {"flag": {"type": "integer"}},
                    "required": ["flag"],
                    "additionalProperties": False,
                },
            },
            "required": ["large", "nested"],
            "additionalProperties": False,
        },
        permission_name="fixture.read",
    )

    spec.validate(Action.invoke("enum", {"large": huge, "nested": {"flag": 1}}).payload)
    with pytest.raises(ValueError, match="enum values"):
        spec.validate(
            Action.invoke(
                "enum",
                {"large": huge + 1, "nested": {"flag": 1}},
            ).payload
        )
    with pytest.raises(ValueError, match="enum values"):
        spec.validate(
            Action.invoke(
                "enum",
                {"large": huge, "nested": {"flag": True}},
            ).payload
        )


def test_action_rejects_integers_that_cannot_be_canonical_json() -> None:
    with pytest.raises(ValueError, match="JSON integer that is too large"):
        Action.invoke("huge", {"value": 10**5000})


def test_controlled_public_values_reject_noncanonical_json_scalars() -> None:
    with pytest.raises(ValueError, match="JSON integer that is too large"):
        ToolResult(output=None, tokens=10**5000)
    with pytest.raises(ValueError, match="not valid Unicode"):
        ApprovalDecision("sha256:fixture", True, "\ud800")
