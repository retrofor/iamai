"""Deterministic reference adapters for headless Trials."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ._model import (
    Action,
    Evaluation,
    FrozenJsonValue,
    JsonValue,
    Observation,
    Task,
    Trajectory,
    Transition,
    _action_payload,
    _freeze_json,
    _frozen_object,
    _thaw_json,
)


class ScriptedAgent:
    """Deterministic Agent Adapter for examples, tests, and baseline Trials."""

    def __init__(self, actions: Sequence[Action], *, name: str, version: str) -> None:
        self._name = name
        self._version = version
        self._actions = tuple(actions)
        self._configuration = _frozen_object(
            actions=[_thaw_json(_action_payload(action)) for action in self._actions]
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def configuration(self) -> Mapping[str, FrozenJsonValue]:
        return self._configuration

    async def decide(
        self,
        task: Task,
        observation: Observation,
        trajectory: Trajectory,
        *,
        seed: int,
        action_index: int,
    ) -> Action:
        """Return the next predefined Action."""
        del task, observation, trajectory, seed
        if action_index >= len(self._actions):
            raise RuntimeError("scripted agent ran out of actions")
        return self._actions[action_index]


class LookupEnvironment:
    """Deterministic key/value Environment Adapter for headless reference Trials."""

    def __init__(
        self,
        values: Mapping[str, JsonValue],
        *,
        name: str,
        version: str,
    ) -> None:
        self._name = name
        self._version = version
        frozen_values = _freeze_json(values, path="$.environment.values")
        if not isinstance(frozen_values, Mapping):
            raise AssertionError("lookup values did not produce a mapping")
        self._values = frozen_values
        self._configuration = _frozen_object(values=frozen_values)

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def configuration(self) -> Mapping[str, FrozenJsonValue]:
        return self._configuration

    async def reset(self, task: Task, *, seed: int) -> Observation:
        """Expose the Task input as the initial Observation."""
        del seed
        return Observation(task.input)

    async def step(self, action: Action, *, seed: int, action_index: int) -> Transition:
        """Commit a lookup or conventional final-answer Action."""
        del seed, action_index
        if action.is_final:
            return Transition(
                observation=Observation(action.payload),
                terminated=True,
                output=action.payload,
            )
        if action.name != "lookup" or not isinstance(action.payload, Mapping):
            raise ValueError(f"unsupported lookup action: {action.name}")
        key = action.payload.get("key")
        if not isinstance(key, str) or key not in self._values:
            raise KeyError(f"unknown lookup key: {key}")
        return Transition(observation=Observation(self._values[key]))


class ExactEvaluator:
    """Evaluator Adapter that requires an exact final value."""

    def __init__(self, expected: JsonValue, *, version: str) -> None:
        self._expected = _freeze_json(expected, path="$.evaluator.expected")
        self._version = version
        self._configuration = _frozen_object(expected=self._expected)

    @property
    def name(self) -> str:
        return "exact"

    @property
    def expected(self) -> FrozenJsonValue:
        return self._expected

    @property
    def version(self) -> str:
        return self._version

    @property
    def configuration(self) -> Mapping[str, FrozenJsonValue]:
        return self._configuration

    async def evaluate(
        self,
        task: Task,
        trajectory: Trajectory,
        output: FrozenJsonValue,
    ) -> Evaluation:
        """Return a binary exact-match Evaluation."""
        del task
        has_committed_output = any(
            record.kind == "environment.transition"
            and record.payload.get("terminated") is True
            for record in trajectory.records
        )
        passed = has_committed_output and output == self._expected
        return Evaluation(
            passed=passed,
            score=1.0 if passed else 0.0,
            evaluator=self.name,
            evaluator_version=self.version,
        )
