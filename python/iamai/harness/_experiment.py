"""Versioned comparison Experiments for the provisional harness."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING

from ._model import (
    FrozenJsonValue,
    JsonValue,
    TRAJECTORY_FORMAT_VERSION,
    Trajectory,
    TrialResult,
    _configuration_hash,
    _freeze_json,
    _frozen_object,
)
from ._replay import _validate_configuration, replay
from ._trial import Trial, _configuration_snapshot

if TYPE_CHECKING:
    from ._jsonl import JsonlTrajectoryStore


def _trajectory_spec(trajectory: Trajectory) -> Mapping[str, FrozenJsonValue]:
    return _frozen_object(
        format_version=trajectory.format_version,
        trial_id=trajectory.trial_id,
        task={"id": trajectory.task.id, "input": trajectory.task.input},
        seed=trajectory.seed,
        configuration=trajectory.configuration,
        config_hash=trajectory.config_hash,
    )


@dataclass(frozen=True, slots=True)
class ExperimentPlan:
    """Immutable, serializable specification for one comparison Experiment."""

    experiment_id: str
    version: str
    trial_specs: Mapping[str, tuple[Trajectory, ...]]
    baseline: str | None
    provenance: Mapping[str, JsonValue | FrozenJsonValue] = field(default_factory=dict)
    plan_hash: str = field(init=False)
    _payload: Mapping[str, FrozenJsonValue] = field(
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.experiment_id, str) or not self.experiment_id.strip():
            raise ValueError("ExperimentPlan experiment_id cannot be empty")
        if not isinstance(self.version, str) or not self.version.strip():
            raise ValueError("ExperimentPlan version cannot be empty")
        if self.baseline is not None and (
            not isinstance(self.baseline, str) or not self.baseline.strip()
        ):
            raise ValueError("ExperimentPlan baseline must be a non-empty string or None")
        if not isinstance(self.trial_specs, Mapping) or not self.trial_specs:
            raise ValueError("ExperimentPlan must contain at least one variant")

        frozen_variants: dict[str, tuple[Trajectory, ...]] = {}
        all_trial_ids: set[str] = set()
        variant_payloads: list[Mapping[str, FrozenJsonValue]] = []
        for variant, raw_specs in self.trial_specs.items():
            if not isinstance(variant, str) or not variant.strip():
                raise ValueError("ExperimentPlan variant names cannot be empty")
            specs = tuple(raw_specs)
            if not specs:
                raise ValueError("ExperimentPlan variants must contain a Trial spec")
            spec_payloads: list[Mapping[str, FrozenJsonValue]] = []
            for position, spec in enumerate(specs):
                if not isinstance(spec, Trajectory):
                    raise TypeError("ExperimentPlan trial_specs must contain Trajectories")
                if spec.records:
                    raise ValueError("ExperimentPlan Trial specs cannot contain records")
                if spec.format_version != TRAJECTORY_FORMAT_VERSION:
                    raise ValueError(
                        f"unsupported ExperimentPlan Trajectory format: {spec.format_version}"
                    )
                if spec.config_hash != _configuration_hash(spec.configuration):
                    raise ValueError(
                        "ExperimentPlan Trial spec configuration hash does not match"
                    )
                _validate_configuration(spec)
                max_actions = spec.configuration.get("max_actions")
                if (
                    isinstance(max_actions, bool)
                    or not isinstance(max_actions, int)
                    or max_actions <= 0
                ):
                    raise ValueError(
                        "ExperimentPlan Trial spec must declare positive max_actions"
                    )
                if spec.trial_id in all_trial_ids:
                    raise ValueError("ExperimentPlan Trial ids must be globally unique")
                all_trial_ids.add(spec.trial_id)
                payload = _trajectory_spec(spec)
                spec_payloads.append(
                    _frozen_object(
                        position=position,
                        spec=payload,
                        spec_hash=_configuration_hash(payload),
                    )
                )
            frozen_variants[variant] = specs
            variant_payloads.append(_frozen_object(name=variant, trials=spec_payloads))

        if self.baseline is not None and self.baseline not in frozen_variants:
            raise ValueError("ExperimentPlan baseline must name a planned variant")
        provenance = _freeze_json(
            self.provenance,
            path="$.experiment.provenance",
        )
        if not isinstance(provenance, Mapping):
            raise TypeError("ExperimentPlan provenance must be an object")
        payload = _frozen_object(
            experiment_id=self.experiment_id,
            version=self.version,
            baseline=self.baseline,
            provenance=provenance,
            variants=variant_payloads,
        )
        object.__setattr__(self, "trial_specs", MappingProxyType(frozen_variants))
        object.__setattr__(self, "provenance", provenance)
        object.__setattr__(self, "_payload", payload)
        object.__setattr__(self, "plan_hash", _configuration_hash(payload))

    @property
    def planned_trial_ids(self) -> Mapping[str, tuple[str, ...]]:
        """Return the planned Trial ids in semantic variant and slot order."""
        return MappingProxyType(
            {
                variant: tuple(spec.trial_id for spec in specs)
                for variant, specs in self.trial_specs.items()
            }
        )

    def _spec_hash(self, variant: str, position: int) -> str:
        return _configuration_hash(_trajectory_spec(self.trial_specs[variant][position]))


@dataclass(frozen=True, slots=True)
class _TrialSlot:
    variant: str
    position: int
    trial: Trial


@dataclass(frozen=True, slots=True)
class ExperimentResult:
    """Immutable projection of a persisted Experiment plan and Trial results."""

    plan: ExperimentPlan
    results: Mapping[str, tuple[TrialResult, ...]]
    started_trial_ids: Mapping[str, tuple[str, ...]]

    def __post_init__(self) -> None:
        if not isinstance(self.plan, ExperimentPlan):
            raise TypeError("ExperimentResult plan must be an ExperimentPlan")
        planned = dict(self.plan.planned_trial_ids)
        results = {
            variant: tuple(variant_results)
            for variant, variant_results in self.results.items()
        }
        started = {
            variant: tuple(trial_ids)
            for variant, trial_ids in self.started_trial_ids.items()
        }
        if set(planned) != set(results) or set(planned) != set(started):
            raise ValueError("ExperimentResult plan and result variants must match")

        for variant, trial_ids in planned.items():
            positions = {trial_id: index for index, trial_id in enumerate(trial_ids)}
            if any(not isinstance(result, TrialResult) for result in results[variant]):
                raise TypeError("ExperimentResult results must contain TrialResult values")
            result_ids = [result.trial_id for result in results[variant]]
            if len(set(result_ids)) != len(result_ids) or any(
                trial_id not in positions for trial_id in result_ids
            ):
                raise ValueError("ExperimentResult contains an unplanned or duplicate Trial")
            if result_ids != sorted(result_ids, key=positions.__getitem__):
                raise ValueError("ExperimentResult Trial results must follow plan order")
            for result in results[variant]:
                position = positions[result.trial_id]
                if (
                    _configuration_hash(_trajectory_spec(result.trajectory))
                    != self.plan._spec_hash(variant, position)
                ):
                    raise ValueError(
                        "ExperimentResult Trial does not match its planned provenance"
                    )
                if replay(result.trajectory) != result:
                    raise ValueError(
                        "ExperimentResult projection does not match its Trajectory"
                    )
            started_ids = started[variant]
            if (
                len(set(started_ids)) != len(started_ids)
                or any(trial_id not in positions for trial_id in started_ids)
                or set(started_ids).intersection(result_ids)
                or list(started_ids) != sorted(started_ids, key=positions.__getitem__)
            ):
                raise ValueError(
                    "ExperimentResult started Trials must be uncommitted and follow plan order"
                )

        object.__setattr__(self, "results", MappingProxyType(results))
        object.__setattr__(self, "started_trial_ids", MappingProxyType(started))

    @property
    def experiment_id(self) -> str:
        return self.plan.experiment_id

    @property
    def version(self) -> str:
        return self.plan.version

    @property
    def baseline(self) -> str | None:
        return self.plan.baseline

    @property
    def plan_hash(self) -> str:
        return self.plan.plan_hash

    @property
    def planned_trial_ids(self) -> Mapping[str, tuple[str, ...]]:
        return self.plan.planned_trial_ids

    @property
    def complete(self) -> bool:
        """Return whether every planned Trial has one committed result."""
        return all(
            len(self.results[variant]) == len(trial_ids)
            for variant, trial_ids in self.planned_trial_ids.items()
        )


class Experiment:
    """Run and persist an explicit set of comparison Trial variants."""

    def __init__(
        self,
        *,
        experiment_id: str,
        version: str,
        trials: Mapping[str, Sequence[Trial]],
        baseline: str | None = None,
        provenance: Mapping[str, JsonValue] | None = None,
    ) -> None:
        if not isinstance(trials, Mapping) or not trials:
            raise ValueError("Experiment trials must contain at least one variant")
        slots_by_variant: dict[str, tuple[_TrialSlot, ...]] = {}
        specs_by_variant: dict[str, tuple[Trajectory, ...]] = {}
        for variant, variant_trials in trials.items():
            if not isinstance(variant, str) or not variant.strip():
                raise ValueError("Experiment variant names cannot be empty")
            planned_trials = tuple(variant_trials)
            if not planned_trials:
                raise ValueError("Experiment variants must contain at least one Trial")
            slots: list[_TrialSlot] = []
            specs: list[Trajectory] = []
            for position, trial in enumerate(planned_trials):
                if not isinstance(trial, Trial):
                    raise TypeError("Experiment variants must contain Trial values")
                spec = trial.trajectory
                if spec.records:
                    raise ValueError("Experiment Trials must not have started")
                slots.append(_TrialSlot(variant=variant, position=position, trial=trial))
                specs.append(spec)
            slots_by_variant[variant] = tuple(slots)
            specs_by_variant[variant] = tuple(specs)
        self._slots = MappingProxyType(slots_by_variant)
        self._recoverable_terminal_slots: set[tuple[str, str]] = set()
        self._plan = ExperimentPlan(
            experiment_id=experiment_id,
            version=version,
            trial_specs=specs_by_variant,
            baseline=baseline,
            provenance={} if provenance is None else provenance,
        )

    @property
    def plan(self) -> ExperimentPlan:
        return self._plan

    @property
    def experiment_id(self) -> str:
        return self.plan.experiment_id

    @property
    def version(self) -> str:
        return self.plan.version

    @property
    def baseline(self) -> str | None:
        return self.plan.baseline

    @property
    def plan_hash(self) -> str:
        return self.plan.plan_hash

    def _validate_pending_slot(self, slot: _TrialSlot) -> None:
        current_spec = slot.trial.trajectory
        if current_spec.records:
            raise RuntimeError(
                f"planned Trial has already started: {current_spec.trial_id}"
            )
        if (
            _configuration_hash(_trajectory_spec(current_spec))
            != self.plan._spec_hash(slot.variant, slot.position)
        ):
            raise ValueError(
                f"planned Trial binding drifted before execution: {current_spec.trial_id}"
            )
        self._validate_live_declarations(slot)

    def _validate_live_declarations(self, slot: _TrialSlot) -> None:
        planned_spec = self.plan.trial_specs[slot.variant][slot.position]
        live_configuration = _configuration_snapshot(
            agent=slot.trial.agent,
            environment=slot.trial.environment,
            evaluator=slot.trial.evaluator,
            max_actions=slot.trial.config.max_actions,
        )
        if live_configuration != planned_spec.configuration:
            raise ValueError(
                "planned Trial declarations drifted: "
                f"{slot.trial.config.trial_id}"
            )

    def _slots_by_trial_id(self) -> Mapping[str, _TrialSlot]:
        return MappingProxyType(
            {
                slot.trial.config.trial_id: slot
                for variant_slots in self._slots.values()
                for slot in variant_slots
            }
        )

    async def run(self, store: JsonlTrajectoryStore) -> ExperimentResult:
        """Run missing Trials sequentially and durably commit each terminal result."""
        with store._writer():
            existing = store._prepare(self.plan)
            started_ids = {
                trial_id
                for variant_ids in existing.started_trial_ids.values()
                for trial_id in variant_ids
            }
            slots_by_trial_id = self._slots_by_trial_id()

            # A prior terminal append may have failed after the in-memory Trial
            # reached a replay-valid terminal state. Finalize that exact outcome;
            # never invoke a started Trial or a replacement Trial automatically.
            for trial_id in started_ids:
                slot = slots_by_trial_id[trial_id]
                started_slot = (str(store.path), trial_id)
                if started_slot not in self._recoverable_terminal_slots:
                    continue
                trajectory = slot.trial.trajectory
                if not trajectory.records:
                    continue
                try:
                    replay(trajectory)
                except ValueError:
                    continue
                store._commit(self.plan, slot, trajectory)
                self._recoverable_terminal_slots.discard(started_slot)

            current = store._load_unlocked()
            if current is None:
                raise RuntimeError("Experiment Store lost its persisted plan")
            committed_ids = {
                result.trial_id
                for variant_results in current.results.values()
                for result in variant_results
            }
            blocked_ids = {
                trial_id
                for variant_ids in current.started_trial_ids.values()
                for trial_id in variant_ids
            }
            pending_slots = tuple(
                slot
                for variant_slots in self._slots.values()
                for slot in variant_slots
                if slot.trial.config.trial_id not in committed_ids | blocked_ids
            )

            # Validate the whole pending batch before emitting any start marker or
            # invoking any Environment effect.
            for slot in pending_slots:
                self._validate_pending_slot(slot)

            for slot in pending_slots:
                self._validate_pending_slot(slot)
                store._start(self.plan, slot)
                started_slot = (str(store.path), slot.trial.config.trial_id)
                try:
                    trial_result = await slot.trial.run()
                except asyncio.CancelledError as cancellation:
                    try:
                        self._validate_live_declarations(slot)
                    except Exception as validation_error:
                        cancellation.add_note(
                            "cancelled Trial declarations drifted; terminal state was "
                            f"not persisted: {validation_error!r}"
                        )
                    else:
                        self._recoverable_terminal_slots.add(started_slot)
                        try:
                            store._commit(self.plan, slot, slot.trial.trajectory)
                        except Exception as persistence_error:
                            cancellation.add_note(
                                "failed to persist the cancelled Trial terminal state: "
                                f"{persistence_error!r}"
                            )
                        else:
                            self._recoverable_terminal_slots.discard(started_slot)
                    raise
                self._validate_live_declarations(slot)
                self._recoverable_terminal_slots.add(started_slot)
                store._commit(self.plan, slot, trial_result.trajectory)
                self._recoverable_terminal_slots.discard(started_slot)

            experiment_result = store._load_unlocked()
            if experiment_result is None:
                raise RuntimeError("Experiment Store lost its persisted plan")
            return experiment_result
