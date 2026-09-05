"""Provider-neutral policy declarations for provisional Harness Agents."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol

from ._model import (
    Action,
    FrozenJsonValue,
    JsonValue,
    Observation,
    Task,
    Trajectory,
    _action_payload,
    _configuration_hash,
    _freeze_json,
    _frozen_object,
    _thaw_json,
)


POLICY_CHECKPOINT_FORMAT_VERSION = "1"


def _required_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} cannot be empty")
    frozen = _freeze_json(value, path=f"$.{field_name.replace(' ', '_')}")
    if not isinstance(frozen, str):
        raise AssertionError("JSON string did not remain a string")
    return frozen


def _frozen_mapping(value: object, *, path: str, field_name: str) -> Mapping[str, FrozenJsonValue]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be an object")
    frozen = _freeze_json(value, path=path)
    if not isinstance(frozen, Mapping):
        raise AssertionError("JSON object did not remain an object")
    return frozen


@dataclass(frozen=True, slots=True)
class PolicyCheckpoint:
    """Immutable caller declaration of decision-relevant Agent policy metadata."""

    checkpoint_id: str
    version: str
    provider: str | None = None
    model: str | None = None
    prompt_policy: Mapping[str, JsonValue] = field(default_factory=dict)
    tool_policy: Mapping[str, JsonValue] = field(default_factory=dict)
    memory_policy: Mapping[str, JsonValue] = field(default_factory=dict)
    context_policy: Mapping[str, JsonValue] = field(default_factory=dict)
    configuration: Mapping[str, JsonValue] = field(default_factory=dict)
    checkpoint_hash: str = field(init=False)

    def __post_init__(self) -> None:
        checkpoint_id = _required_text(
            self.checkpoint_id,
            field_name="PolicyCheckpoint checkpoint_id",
        )
        version = _required_text(
            self.version,
            field_name="PolicyCheckpoint version",
        )
        provider = self.provider
        model = self.model
        if (provider is None) != (model is None):
            raise ValueError(
                "PolicyCheckpoint provider and model must be declared together"
            )
        if provider is not None:
            provider = _required_text(
                provider,
                field_name="PolicyCheckpoint provider",
            )
            model = _required_text(
                model,
                field_name="PolicyCheckpoint model",
            )

        frozen_policies = {
            field_name: _frozen_mapping(
                getattr(self, field_name),
                path=f"$.policy_checkpoint.{field_name}",
                field_name=f"PolicyCheckpoint {field_name}",
            )
            for field_name in (
                "prompt_policy",
                "tool_policy",
                "memory_policy",
                "context_policy",
                "configuration",
            )
        }
        payload = _frozen_object(
            policy_checkpoint_format_version=POLICY_CHECKPOINT_FORMAT_VERSION,
            checkpoint_id=checkpoint_id,
            version=version,
            provider=provider,
            model=model,
            **frozen_policies,
        )
        object.__setattr__(self, "checkpoint_id", checkpoint_id)
        object.__setattr__(self, "version", version)
        object.__setattr__(self, "provider", provider)
        object.__setattr__(self, "model", model)
        for field_name, value in frozen_policies.items():
            object.__setattr__(self, field_name, value)
        object.__setattr__(self, "checkpoint_hash", _configuration_hash(payload))


def _checkpoint_declaration(
    checkpoint: PolicyCheckpoint,
) -> Mapping[str, FrozenJsonValue]:
    return _frozen_object(
        policy_checkpoint_format_version=POLICY_CHECKPOINT_FORMAT_VERSION,
        checkpoint_id=checkpoint.checkpoint_id,
        version=checkpoint.version,
        provider=checkpoint.provider,
        model=checkpoint.model,
        prompt_policy=checkpoint.prompt_policy,
        tool_policy=checkpoint.tool_policy,
        memory_policy=checkpoint.memory_policy,
        context_policy=checkpoint.context_policy,
        configuration=checkpoint.configuration,
        checkpoint_hash=checkpoint.checkpoint_hash,
    )


class AgentPolicy(Protocol):
    """Replaceable decision implementation used by a :class:`PolicyAgent`."""

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


class PolicyAgent:
    """Bind a decision policy and checkpoint to the existing Agent interface."""

    def __init__(
        self,
        policy: AgentPolicy,
        checkpoint: PolicyCheckpoint,
        *,
        name: str = "policy-agent",
        version: str = "1",
    ) -> None:
        if not isinstance(checkpoint, PolicyCheckpoint):
            raise TypeError("PolicyAgent checkpoint must be a PolicyCheckpoint")
        policy_name = _required_text(
            getattr(policy, "name", None),
            field_name="AgentPolicy name",
        )
        policy_version = _required_text(
            getattr(policy, "version", None),
            field_name="AgentPolicy version",
        )
        policy_configuration = _frozen_mapping(
            getattr(policy, "configuration", None),
            path="$.agent_policy.configuration",
            field_name="AgentPolicy configuration",
        )
        self._policy = policy
        self._checkpoint = checkpoint
        self._name = _required_text(name, field_name="PolicyAgent name")
        self._version = _required_text(version, field_name="PolicyAgent version")
        self._configuration = _frozen_object(
            kind="policy_backed",
            policy_checkpoint=_checkpoint_declaration(checkpoint),
            policy_implementation={
                "name": policy_name,
                "version": policy_version,
                "config": policy_configuration,
            },
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
        """Delegate one decision to the bound policy implementation."""
        return await self._policy.decide(
            task,
            observation,
            trajectory,
            seed=seed,
            action_index=action_index,
        )


class ScriptedPolicy:
    """Deterministic reusable AgentPolicy fixture backed by predefined Actions."""

    def __init__(
        self,
        actions: Sequence[Action],
        *,
        name: str = "scripted-policy",
        version: str = "1",
    ) -> None:
        self._name = _required_text(name, field_name="AgentPolicy name")
        self._version = _required_text(version, field_name="AgentPolicy version")
        self._actions = tuple(actions)
        if any(not isinstance(action, Action) for action in self._actions):
            raise TypeError("ScriptedPolicy actions must contain Action values")
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
        """Return the Action declared at the supplied Trial action index."""
        del task, observation, trajectory, seed
        if action_index < 0 or action_index >= len(self._actions):
            raise RuntimeError("scripted policy ran out of actions")
        return self._actions[action_index]
