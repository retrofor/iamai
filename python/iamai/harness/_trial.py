"""Headless Trial execution for the provisional general-agent harness."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Mapping
from typing import Protocol, TypeVar

from ._model import (
    HARNESS_CONFIGURATION_VERSION,
    TRAJECTORY_FORMAT_VERSION,
    Action,
    Evaluation,
    FrozenJsonValue,
    Observation,
    Task,
    Trajectory,
    TrajectoryRecord,
    Transition,
    TrialConfig,
    TrialFailure,
    TrialResult,
    TrialStatus,
    _action_payload,
    _configuration_hash,
    _evaluation_payload,
    _frozen_object,
    _transition_payload,
)

_AwaitedT = TypeVar("_AwaitedT")


def _safe_exception_message(error: Exception) -> str:
    try:
        return str(error)
    except Exception:
        return f"<{type(error).__name__} message unavailable>"


class _Agent(Protocol):
    name: str
    version: str
    configuration: Mapping[str, FrozenJsonValue]

    async def decide(
        self,
        task: Task,
        observation: Observation,
        trajectory: Trajectory,
        *,
        seed: int,
        action_index: int,
    ) -> Action: ...


class _Environment(Protocol):
    name: str
    version: str
    configuration: Mapping[str, FrozenJsonValue]

    async def reset(self, task: Task, *, seed: int) -> Observation: ...

    async def step(self, action: Action, *, seed: int, action_index: int) -> Transition: ...


class _Evaluator(Protocol):
    name: str
    version: str
    configuration: Mapping[str, FrozenJsonValue]

    async def evaluate(
        self,
        task: Task,
        trajectory: Trajectory,
        output: FrozenJsonValue,
    ) -> Evaluation: ...


def _declared_adapter(
    value: _Agent | _Environment | _Evaluator,
) -> Mapping[str, FrozenJsonValue]:
    if not isinstance(value.name, str) or not value.name.strip():
        raise ValueError("Harness component name cannot be empty")
    if not isinstance(value.version, str) or not value.version.strip():
        raise ValueError("Harness component version cannot be empty")
    if not isinstance(value.configuration, Mapping):
        raise TypeError("Harness component configuration must be an object")
    return _frozen_object(
        name=value.name,
        version=value.version,
        config=value.configuration,
    )


def _configuration_snapshot(
    *,
    agent: _Agent,
    environment: _Environment,
    evaluator: _Evaluator,
    max_actions: int,
) -> Mapping[str, FrozenJsonValue]:
    return _frozen_object(
        harness_configuration_version=HARNESS_CONFIGURATION_VERSION,
        agent=_declared_adapter(agent),
        environment=_declared_adapter(environment),
        evaluator=_declared_adapter(evaluator),
        max_actions=max_actions,
    )


class _TrajectoryBuilder:
    def __init__(
        self,
        *,
        config: TrialConfig,
        task: Task,
        configuration: Mapping[str, FrozenJsonValue],
    ) -> None:
        self._config = config
        self._task = task
        self._configuration = configuration
        self._config_hash = _configuration_hash(configuration)
        self._records: list[TrajectoryRecord] = []

    def append(self, kind: str, payload: Mapping[str, object] | None = None) -> None:
        self._records.append(
            TrajectoryRecord(
                sequence=len(self._records),
                kind=kind,
                payload=_frozen_object(**dict(payload or {})),
            )
        )

    def snapshot(self) -> Trajectory:
        return Trajectory(
            format_version=TRAJECTORY_FORMAT_VERSION,
            trial_id=self._config.trial_id,
            task=self._task,
            seed=self._config.seed,
            configuration=self._configuration,
            config_hash=self._config_hash,
            records=tuple(self._records),
        )


class Trial:
    """Run one bounded Agent attempt in one Environment."""

    def __init__(
        self,
        *,
        task: Task,
        agent: _Agent,
        environment: _Environment,
        evaluator: _Evaluator,
        config: TrialConfig,
    ) -> None:
        self._task = task
        self._agent = agent
        self._environment = environment
        self._evaluator = evaluator
        self._config = config
        self._started = False
        configuration = _configuration_snapshot(
            agent=agent,
            environment=environment,
            evaluator=evaluator,
            max_actions=config.max_actions,
        )
        declared_evaluator = configuration["evaluator"]
        if not isinstance(declared_evaluator, Mapping):
            raise AssertionError("Evaluator declaration did not produce an object")
        evaluator_name = declared_evaluator["name"]
        evaluator_version = declared_evaluator["version"]
        if not isinstance(evaluator_name, str) or not isinstance(evaluator_version, str):
            raise AssertionError("Evaluator identity did not produce strings")
        self._declared_evaluator_identity = (evaluator_name, evaluator_version)
        self._trajectory = _TrajectoryBuilder(
            config=config,
            task=task,
            configuration=configuration,
        )

    @property
    def task(self) -> Task:
        """Return the Task bound into this Trial's Trajectory header."""
        return self._task

    @property
    def agent(self) -> _Agent:
        """Return the Agent bound into this Trial's configuration snapshot."""
        return self._agent

    @property
    def environment(self) -> _Environment:
        """Return the Environment bound into this Trial's configuration snapshot."""
        return self._environment

    @property
    def evaluator(self) -> _Evaluator:
        """Return the Evaluator bound into this Trial's configuration snapshot."""
        return self._evaluator

    @property
    def config(self) -> TrialConfig:
        """Return the immutable configuration bound into this Trial."""
        return self._config

    @property
    def trajectory(self) -> Trajectory:
        """Return the committed Trajectory prefix."""
        return self._trajectory.snapshot()

    def _fail(self, *, phase: str, code: str, error: Exception) -> TrialResult:
        failure = TrialFailure(
            phase=phase,
            code=code,
            exception_type=type(error).__name__,
            message=_safe_exception_message(error),
        )
        self._trajectory.append(
            "trial.failure",
            {
                "phase": failure.phase,
                "code": failure.code,
                "exception_type": failure.exception_type,
                "message": failure.message,
            },
        )
        self._trajectory.append(
            "trial.terminated",
            {"status": TrialStatus.FAILED.value, "phase": failure.phase},
        )
        return TrialResult(
            trial_id=self.config.trial_id,
            status=TrialStatus.FAILED,
            final_output=None,
            evaluation=None,
            trajectory=self.trajectory,
            failure=failure,
        )

    def _cancel(self, *, phase: str, operation: str) -> None:
        self._trajectory.append(
            "trial.cancelled",
            {"phase": phase, "operation": operation},
        )
        self._trajectory.append(
            "trial.terminated",
            {
                "status": TrialStatus.CANCELLED.value,
                "phase": phase,
                "operation": operation,
            },
        )

    async def _await_phase(
        self,
        awaitable: Awaitable[_AwaitedT],
        *,
        phase: str,
        operation: str,
    ) -> _AwaitedT:
        try:
            return await awaitable
        except asyncio.CancelledError:
            self._cancel(phase=phase, operation=operation)
            raise

    def _validate_evaluation_identity(self, evaluation: Evaluation) -> None:
        if (
            evaluation.evaluator,
            evaluation.evaluator_version,
        ) != self._declared_evaluator_identity:
            raise ValueError(
                "Evaluation identity must match the declared Evaluator name and version"
            )

    async def run(self) -> TrialResult:
        """Run the Trial to a terminating Transition and Evaluation."""
        if self._started:
            raise RuntimeError("a Trial can only be run once")
        self._started = True
        self._trajectory.append("trial.started")
        try:
            observation = await self._await_phase(
                self.environment.reset(self.task, seed=self.config.seed),
                phase="environment",
                operation="environment.reset",
            )
            if not isinstance(observation, Observation):
                raise TypeError("Environment.reset() must return Observation")
            self._trajectory.append(
                "environment.reset",
                {"observation": observation.value},
            )
        except Exception as error:
            return self._fail(
                phase="environment",
                code="environment_reset_error",
                error=error,
            )
        for action_index in range(self.config.max_actions):
            try:
                action = await self._await_phase(
                    self.agent.decide(
                        self.task,
                        observation,
                        self.trajectory,
                        seed=self.config.seed,
                        action_index=action_index,
                    ),
                    phase="agent",
                    operation="agent.decide",
                )
                if not isinstance(action, Action):
                    raise TypeError("Agent.decide() must return Action")
                self._trajectory.append("agent.action", _action_payload(action))
            except Exception as error:
                return self._fail(
                    phase="agent",
                    code="agent_decide_error",
                    error=error,
                )
            try:
                transition = await self._await_phase(
                    self.environment.step(
                        action,
                        seed=self.config.seed,
                        action_index=action_index,
                    ),
                    phase="environment",
                    operation="environment.step",
                )
                if not isinstance(transition, Transition):
                    raise TypeError("Environment.step() must return Transition")
                self._trajectory.append(
                    "environment.transition",
                    _transition_payload(transition),
                )
            except Exception as error:
                return self._fail(
                    phase="environment",
                    code="environment_step_error",
                    error=error,
                )
            observation = transition.observation
            if not transition.terminated:
                continue
            try:
                evaluation = await self._await_phase(
                    self.evaluator.evaluate(
                        self.task,
                        self.trajectory,
                        transition.output,
                    ),
                    phase="evaluator",
                    operation="evaluator.evaluate",
                )
                if not isinstance(evaluation, Evaluation):
                    raise TypeError("Evaluator.evaluate() must return Evaluation")
                self._validate_evaluation_identity(evaluation)
                self._trajectory.append(
                    "evaluation.recorded",
                    _evaluation_payload(evaluation),
                )
            except Exception as error:
                return self._fail(
                    phase="evaluator",
                    code="evaluator_evaluate_error",
                    error=error,
                )
            self._trajectory.append(
                "trial.terminated",
                {"status": TrialStatus.COMPLETED.value},
            )
            return TrialResult(
                trial_id=self.config.trial_id,
                status=TrialStatus.COMPLETED,
                final_output=transition.output,
                evaluation=evaluation,
                trajectory=self.trajectory,
            )
        self._trajectory.append(
            "budget.exhausted",
            {"max_actions": self.config.max_actions},
        )
        try:
            evaluation = await self._await_phase(
                self.evaluator.evaluate(
                    self.task,
                    self.trajectory,
                    None,
                ),
                phase="evaluator",
                operation="evaluator.evaluate",
            )
            if not isinstance(evaluation, Evaluation):
                raise TypeError("Evaluator.evaluate() must return Evaluation")
            self._validate_evaluation_identity(evaluation)
            self._trajectory.append(
                "evaluation.recorded",
                _evaluation_payload(evaluation),
            )
        except Exception as error:
            return self._fail(
                phase="evaluator",
                code="evaluator_evaluate_error",
                error=error,
            )
        self._trajectory.append(
            "trial.terminated",
            {"status": TrialStatus.BUDGET_EXHAUSTED.value},
        )
        return TrialResult(
            trial_id=self.config.trial_id,
            status=TrialStatus.BUDGET_EXHAUSTED,
            final_output=None,
            evaluation=evaluation,
            trajectory=self.trajectory,
        )
