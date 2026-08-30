"""Immutable domain values for the provisional general-agent harness."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import TypeAlias

JsonValue: TypeAlias = (
    None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
)
FrozenJsonValue: TypeAlias = (
    None
    | bool
    | int
    | float
    | str
    | tuple["FrozenJsonValue", ...]
    | Mapping[str, "FrozenJsonValue"]
)

TRAJECTORY_FORMAT_VERSION = "1"
HARNESS_CONFIGURATION_VERSION = "1"
_MAX_JSON_NESTING_DEPTH = 128


def _freeze_json(
    value: object,
    *,
    path: str = "$",
    _depth: int = 0,
) -> FrozenJsonValue:
    if _depth > _MAX_JSON_NESTING_DEPTH:
        raise ValueError(
            f"{path} exceeds the maximum JSON nesting depth "
            f"of {_MAX_JSON_NESTING_DEPTH}"
        )
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise ValueError(f"{path} contains a string that is not valid Unicode") from exc
        return value
    if isinstance(value, int):
        try:
            json.dumps(value, allow_nan=False)
        except ValueError as exc:
            raise ValueError(f"{path} contains a JSON integer that is too large") from exc
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{path} must contain a finite JSON number")
        return value
    if isinstance(value, Mapping):
        frozen: dict[str, FrozenJsonValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{path} must contain string object keys")
            try:
                key.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise ValueError(
                    f"{path} contains an object key that is not valid Unicode"
                ) from exc
            frozen[key] = _freeze_json(
                item,
                path=f"{path}.{key}",
                _depth=_depth + 1,
            )
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(
            _freeze_json(
                item,
                path=f"{path}[{index}]",
                _depth=_depth + 1,
            )
            for index, item in enumerate(value)
        )
    raise TypeError(f"{path} must contain only JSON-compatible values")


def _thaw_json(value: FrozenJsonValue) -> JsonValue:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def _frozen_object(**values: object) -> Mapping[str, FrozenJsonValue]:
    frozen = _freeze_json(values)
    if not isinstance(frozen, Mapping):
        raise AssertionError("frozen object did not produce a mapping")
    return frozen


def _configuration_hash(configuration: Mapping[str, FrozenJsonValue]) -> str:
    canonical = json.dumps(
        _thaw_json(configuration),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


@dataclass(frozen=True, slots=True)
class Task:
    """Goal and initial input for one Trial."""

    id: str
    input: FrozenJsonValue

    def __post_init__(self) -> None:
        if not isinstance(self.id, str):
            raise TypeError("task id must be a string")
        if not self.id.strip():
            raise ValueError("task id cannot be empty")
        _freeze_json(self.id, path="$.task.id")
        object.__setattr__(self, "input", _freeze_json(self.input, path="$.task.input"))


@dataclass(frozen=True, slots=True)
class TrialConfig:
    """Identity, deterministic seed, and Action budget for one Trial."""

    trial_id: str
    seed: int = 0
    max_actions: int = 8

    def __post_init__(self) -> None:
        if not isinstance(self.trial_id, str):
            raise TypeError("trial_id must be a string")
        if not self.trial_id.strip():
            raise ValueError("trial id cannot be empty")
        _freeze_json(self.trial_id, path="$.trial_config.trial_id")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise TypeError("seed must be an integer")
        _freeze_json(self.seed, path="$.trial_config.seed")
        if isinstance(self.max_actions, bool) or not isinstance(self.max_actions, int):
            raise TypeError("max_actions must be an integer")
        if self.max_actions <= 0:
            raise ValueError("max_actions must be greater than zero")
        _freeze_json(self.max_actions, path="$.trial_config.max_actions")


class TrialStatus(str, Enum):
    """Terminal state of a Trial."""

    COMPLETED = "completed"
    BUDGET_EXHAUSTED = "budget_exhausted"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class Observation:
    """Information exposed by an Environment for the next Agent decision."""

    value: FrozenJsonValue

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _freeze_json(self.value, path="$.observation"))


@dataclass(frozen=True, slots=True)
class Action:
    """An Environment interaction or final answer proposed by an Agent."""

    name: str
    payload: FrozenJsonValue = None
    is_final: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise TypeError("action name must be a string")
        if not self.name.strip():
            raise ValueError("action name cannot be empty")
        _freeze_json(self.name, path="$.action.name")
        if not isinstance(self.is_final, bool):
            raise TypeError("action is_final must be a bool")
        object.__setattr__(
            self,
            "payload",
            _freeze_json(self.payload, path="$.action.payload"),
        )

    @classmethod
    def invoke(
        cls,
        name: str,
        arguments: Mapping[str, JsonValue] | None = None,
    ) -> "Action":
        """Create an Environment invocation."""
        return cls(name=name, payload=_freeze_json(arguments or {}))

    @classmethod
    def finish(cls, output: JsonValue) -> "Action":
        """Create a conventional final-answer Action for compatible Environments."""
        return cls(name="final", payload=_freeze_json(output), is_final=True)


@dataclass(frozen=True, slots=True)
class Transition:
    """Committed outcome of applying one Action to an Environment."""

    observation: Observation
    terminated: bool = False
    output: FrozenJsonValue = None

    def __post_init__(self) -> None:
        if not isinstance(self.observation, Observation):
            raise TypeError("Transition observation must be an Observation")
        if not isinstance(self.terminated, bool):
            raise TypeError("Transition terminated must be a bool")
        object.__setattr__(
            self,
            "output",
            _freeze_json(self.output, path="$.transition.output"),
        )


@dataclass(frozen=True, slots=True)
class Evaluation:
    """Versioned judgment of a committed Trial Trajectory."""

    passed: bool
    score: float
    evaluator: str
    evaluator_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.passed, bool):
            raise TypeError("Evaluation passed must be a bool")
        if isinstance(self.score, bool) or not isinstance(self.score, (int, float)):
            raise TypeError("Evaluation score must be a number")
        score = float(self.score)
        if not math.isfinite(score):
            raise ValueError("Evaluation score must be finite")
        if not isinstance(self.evaluator, str) or not self.evaluator.strip():
            raise ValueError("Evaluation evaluator cannot be empty")
        if not isinstance(self.evaluator_version, str) or not self.evaluator_version.strip():
            raise ValueError("Evaluation evaluator_version cannot be empty")
        _freeze_json(self.evaluator, path="$.evaluation.evaluator")
        _freeze_json(
            self.evaluator_version,
            path="$.evaluation.evaluator_version",
        )
        object.__setattr__(self, "score", score)


@dataclass(frozen=True, slots=True)
class TrajectoryRecord:
    """One immutable, causally ordered fact in a Trajectory."""

    sequence: int
    kind: str
    payload: Mapping[str, FrozenJsonValue]

    def __post_init__(self) -> None:
        if (
            isinstance(self.sequence, bool)
            or not isinstance(self.sequence, int)
            or self.sequence < 0
        ):
            raise ValueError("Trajectory record sequence must be a non-negative integer")
        _freeze_json(self.sequence, path="$.trajectory.record.sequence")
        if not isinstance(self.kind, str) or not self.kind.strip():
            raise ValueError("Trajectory record kind cannot be empty")
        _freeze_json(self.kind, path="$.trajectory.record.kind")
        payload = _freeze_json(self.payload, path="$.trajectory.record.payload")
        if not isinstance(payload, Mapping):
            raise TypeError("Trajectory record payload must be an object")
        object.__setattr__(self, "payload", payload)


@dataclass(frozen=True, slots=True)
class Trajectory:
    """Immutable source of truth for one Trial."""

    format_version: str
    trial_id: str
    task: Task
    seed: int
    configuration: Mapping[str, FrozenJsonValue]
    config_hash: str
    records: tuple[TrajectoryRecord, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.format_version, str) or not self.format_version.strip():
            raise ValueError("Trajectory format version cannot be empty")
        if not isinstance(self.trial_id, str) or not self.trial_id.strip():
            raise ValueError("Trajectory trial id cannot be empty")
        _freeze_json(self.format_version, path="$.trajectory.format_version")
        _freeze_json(self.trial_id, path="$.trajectory.trial_id")
        if not isinstance(self.task, Task):
            raise TypeError("Trajectory task must be a Task")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise TypeError("Trajectory seed must be an integer")
        _freeze_json(self.seed, path="$.trajectory.seed")
        configuration = _freeze_json(
            self.configuration,
            path="$.trajectory.configuration",
        )
        if not isinstance(configuration, Mapping):
            raise TypeError("Trajectory configuration must be an object")
        records = tuple(self.records)
        if not all(isinstance(record, TrajectoryRecord) for record in records):
            raise TypeError("Trajectory records must contain TrajectoryRecord values")
        if not isinstance(self.config_hash, str) or not self.config_hash.strip():
            raise ValueError("Trajectory configuration hash cannot be empty")
        _freeze_json(self.config_hash, path="$.trajectory.config_hash")
        object.__setattr__(self, "configuration", configuration)
        object.__setattr__(self, "records", records)


@dataclass(frozen=True, slots=True)
class TrialFailure:
    """Attributed failure captured while running one Trial phase."""

    phase: str
    code: str
    exception_type: str
    message: str

    def __post_init__(self) -> None:
        for field_name in ("phase", "code", "exception_type"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"TrialFailure {field_name} cannot be empty")
            _freeze_json(value, path=f"$.trial_failure.{field_name}")
        if not isinstance(self.message, str):
            raise TypeError("TrialFailure message must be a string")
        _freeze_json(self.message, path="$.trial_failure.message")


@dataclass(frozen=True, slots=True)
class TrialResult:
    """Terminal public result returned by a Trial."""

    trial_id: str
    status: TrialStatus
    final_output: FrozenJsonValue
    evaluation: Evaluation | None
    trajectory: Trajectory
    failure: TrialFailure | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.trial_id, str) or not self.trial_id.strip():
            raise ValueError("TrialResult trial_id cannot be empty")
        _freeze_json(self.trial_id, path="$.trial_result.trial_id")
        if not isinstance(self.status, TrialStatus):
            raise TypeError("TrialResult status must be a TrialStatus")
        if not isinstance(self.trajectory, Trajectory):
            raise TypeError("TrialResult trajectory must be a Trajectory")
        if self.trial_id != self.trajectory.trial_id:
            raise ValueError("TrialResult trial_id must match its Trajectory")
        if self.evaluation is not None and not isinstance(self.evaluation, Evaluation):
            raise TypeError("TrialResult evaluation must be an Evaluation or None")
        if self.failure is not None and not isinstance(self.failure, TrialFailure):
            raise TypeError("TrialResult failure must be a TrialFailure or None")
        if self.status in {TrialStatus.COMPLETED, TrialStatus.BUDGET_EXHAUSTED}:
            if self.evaluation is None or self.failure is not None:
                raise ValueError("evaluated TrialResult has inconsistent outcome fields")
        elif self.status is TrialStatus.FAILED:
            if self.evaluation is not None or self.failure is None:
                raise ValueError("failed TrialResult has inconsistent outcome fields")
        elif self.evaluation is not None or self.failure is not None:
            raise ValueError("cancelled TrialResult cannot contain Evaluation or failure")
        if self.status is not TrialStatus.COMPLETED and self.final_output is not None:
            raise ValueError("only a completed TrialResult can contain final output")
        object.__setattr__(
            self,
            "final_output",
            _freeze_json(self.final_output, path="$.trial_result.final_output"),
        )


def _action_payload(action: Action) -> Mapping[str, FrozenJsonValue]:
    return _frozen_object(
        name=action.name,
        payload=action.payload,
        is_final=action.is_final,
    )


def _transition_payload(transition: Transition) -> Mapping[str, FrozenJsonValue]:
    return _frozen_object(
        observation=transition.observation.value,
        terminated=transition.terminated,
        output=transition.output,
    )


def _evaluation_payload(evaluation: Evaluation) -> Mapping[str, FrozenJsonValue]:
    return _frozen_object(
        passed=evaluation.passed,
        score=evaluation.score,
        evaluator=evaluation.evaluator,
        evaluator_version=evaluation.evaluator_version,
    )
