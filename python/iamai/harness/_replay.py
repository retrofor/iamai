"""Pure reconstruction and causal validation of committed Trajectories."""

from __future__ import annotations

from collections.abc import Mapping

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
)


def _causal_error(reason: str) -> ValueError:
    return ValueError(f"invalid Trajectory causal order: {reason}")


def _validate_configuration(
    trajectory: Trajectory,
) -> Mapping[str, FrozenJsonValue]:
    configuration = trajectory.configuration
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
    body = middle[:-1]

    reset_seen = bool(body and body[0].kind == "environment.reset")
    if reset_seen and "observation" not in body[0].payload:
        raise _causal_error("Environment reset observation is missing")
    position = 1 if reset_seen else 0
    pending_action = False
    terminated = False
    budget_exhausted = False
    action_count = 0
    final_output: FrozenJsonValue = None

    for record in body[position:]:
        if record.kind == "agent.action":
            if not reset_seen or pending_action or terminated or budget_exhausted:
                raise _causal_error("Agent Action is outside an active Environment state")
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
            action_count += 1
            if action_count > max_actions:
                raise _causal_error("Action count exceeds max_actions")
            continue

        if record.kind == "environment.transition":
            if not pending_action or terminated or budget_exhausted:
                raise _causal_error("Environment Transition has no pending Agent Action")
            transition_terminated = record.payload.get("terminated")
            if not isinstance(transition_terminated, bool):
                raise _causal_error("Environment Transition termination flag is invalid")
            if "observation" not in record.payload or "output" not in record.payload:
                raise _causal_error("Environment Transition payload is incomplete")
            pending_action = False
            if transition_terminated:
                terminated = True
                final_output = record.payload.get("output")
            continue

        if record.kind == "budget.exhausted":
            declared_budget = record.payload.get("max_actions")
            if (
                not reset_seen
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
