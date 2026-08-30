"""Pure paired evidence projections for persisted Harness Experiments."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from ._experiment import (
    ExperimentResult,
    TaskDistributionManifest,
    _comparison_projection,
    _is_registered_experiment_result,
)
from ._model import (
    TrialResult,
    TrialStatus,
    _configuration_hash,
    _frozen_object,
    _trajectory_hash,
)

EXPERIMENT_COMPARISON_FORMAT_VERSION = "1"


def _is_sha256_identifier(value: str) -> bool:
    prefix = "sha256:"
    digest = value.removeprefix(prefix)
    return (
        value.startswith(prefix)
        and len(digest) == 64
        and all(character in "0123456789abcdef" for character in digest)
    )


@dataclass(frozen=True, slots=True, init=False)
class TrialComparison:
    """One pre-registered baseline/candidate Trial pair."""

    position: int
    case_id: str
    case_hash: str
    task_id: str
    seed: int
    baseline_trial_id: str
    candidate_trial_id: str
    baseline_trajectory_hash: str
    candidate_trajectory_hash: str
    baseline_status: TrialStatus
    candidate_status: TrialStatus
    baseline_passed: bool | None
    candidate_passed: bool | None
    baseline_score: float | None
    candidate_score: float | None
    score_delta: float | None = field(init=False)

    def __init__(self, *args: object, **kwargs: object) -> None:
        del args, kwargs
        raise TypeError("TrialComparison has no public constructor; use compare_experiment")

    def __post_init__(self) -> None:
        if (
            isinstance(self.position, bool)
            or not isinstance(self.position, int)
            or self.position < 0
        ):
            raise ValueError("TrialComparison position must be a non-negative integer")
        for field_name in (
            "case_id",
            "case_hash",
            "task_id",
            "baseline_trial_id",
            "candidate_trial_id",
            "baseline_trajectory_hash",
            "candidate_trajectory_hash",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"TrialComparison {field_name} cannot be empty")
        if not _is_sha256_identifier(self.case_hash):
            raise ValueError("TrialComparison case_hash must be a sha256 identifier")
        for field_name in (
            "baseline_trajectory_hash",
            "candidate_trajectory_hash",
        ):
            if not _is_sha256_identifier(getattr(self, field_name)):
                raise ValueError(f"TrialComparison {field_name} must be a sha256 identifier")
        if self.baseline_trial_id == self.candidate_trial_id:
            raise ValueError("TrialComparison Trial ids must differ")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise TypeError("TrialComparison seed must be an integer")
        if not isinstance(self.baseline_status, TrialStatus) or not isinstance(
            self.candidate_status, TrialStatus
        ):
            raise TypeError("TrialComparison statuses must be TrialStatus values")
        for field_name in ("baseline_passed", "candidate_passed"):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, bool):
                raise TypeError(f"TrialComparison {field_name} must be a bool or None")
        scores: dict[str, float | None] = {}
        for field_name in ("baseline_score", "candidate_score"):
            value = getattr(self, field_name)
            if value is None:
                scores[field_name] = None
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"TrialComparison {field_name} must be a number or None")
            score = float(value)
            if not math.isfinite(score):
                raise ValueError(f"TrialComparison {field_name} must be finite")
            scores[field_name] = score
            object.__setattr__(self, field_name, score)
        if (self.baseline_passed is None) != (self.baseline_score is None):
            raise ValueError("TrialComparison baseline Evaluation fields are inconsistent")
        if (self.candidate_passed is None) != (self.candidate_score is None):
            raise ValueError("TrialComparison candidate Evaluation fields are inconsistent")
        evaluated_statuses = {
            TrialStatus.COMPLETED,
            TrialStatus.BUDGET_EXHAUSTED,
        }
        for side in ("baseline", "candidate"):
            status = getattr(self, f"{side}_status")
            has_evaluation = getattr(self, f"{side}_passed") is not None
            if (status in evaluated_statuses) != has_evaluation:
                raise ValueError(f"TrialComparison {side} status and Evaluation are inconsistent")
        score_delta = (
            None
            if scores["baseline_score"] is None or scores["candidate_score"] is None
            else scores["candidate_score"] - scores["baseline_score"]
        )
        if score_delta is not None and not math.isfinite(score_delta):
            raise ValueError("TrialComparison score_delta must be finite")
        object.__setattr__(self, "score_delta", score_delta)


def _trial_comparison(
    *,
    position: int,
    case_id: str,
    case_hash: str,
    task_id: str,
    seed: int,
    baseline_trial_id: str,
    candidate_trial_id: str,
    baseline_trajectory_hash: str,
    candidate_trajectory_hash: str,
    baseline_status: TrialStatus,
    candidate_status: TrialStatus,
    baseline_passed: bool | None,
    candidate_passed: bool | None,
    baseline_score: float | None,
    candidate_score: float | None,
) -> TrialComparison:
    comparison = object.__new__(TrialComparison)
    values = {
        "position": position,
        "case_id": case_id,
        "case_hash": case_hash,
        "task_id": task_id,
        "seed": seed,
        "baseline_trial_id": baseline_trial_id,
        "candidate_trial_id": candidate_trial_id,
        "baseline_trajectory_hash": baseline_trajectory_hash,
        "candidate_trajectory_hash": candidate_trajectory_hash,
        "baseline_status": baseline_status,
        "candidate_status": candidate_status,
        "baseline_passed": baseline_passed,
        "candidate_passed": candidate_passed,
        "baseline_score": baseline_score,
        "candidate_score": candidate_score,
    }
    for field_name, value in values.items():
        object.__setattr__(comparison, field_name, value)
    comparison.__post_init__()
    return comparison


def _trial_comparison_payload(comparison: TrialComparison) -> dict[str, object]:
    return {
        "position": comparison.position,
        "case_id": comparison.case_id,
        "case_hash": comparison.case_hash,
        "task_id": comparison.task_id,
        "seed": comparison.seed,
        "baseline_trial_id": comparison.baseline_trial_id,
        "candidate_trial_id": comparison.candidate_trial_id,
        "baseline_trajectory_hash": comparison.baseline_trajectory_hash,
        "candidate_trajectory_hash": comparison.candidate_trajectory_hash,
        "baseline_status": comparison.baseline_status.value,
        "candidate_status": comparison.candidate_status.value,
        "baseline_passed": comparison.baseline_passed,
        "candidate_passed": comparison.candidate_passed,
        "baseline_score": comparison.baseline_score,
        "candidate_score": comparison.candidate_score,
        "score_delta": comparison.score_delta,
    }


@dataclass(frozen=True, slots=True, init=False)
class ExperimentComparison:
    """Hash-bound aggregate over one baseline and one candidate variant."""

    experiment_id: str
    plan_hash: str
    task_distribution: TaskDistributionManifest
    baseline: str
    candidate: str
    trials: tuple[TrialComparison, ...]
    comparison_format_version: str = field(init=False)
    total_pairs: int = field(init=False)
    baseline_passes: int = field(init=False)
    candidate_passes: int = field(init=False)
    baseline_pass_rate: float = field(init=False)
    candidate_pass_rate: float = field(init=False)
    pass_rate_delta: float = field(init=False)
    baseline_status_counts: Mapping[TrialStatus, int] = field(init=False)
    candidate_status_counts: Mapping[TrialStatus, int] = field(init=False)
    baseline_status_rates: Mapping[TrialStatus, float] = field(init=False)
    candidate_status_rates: Mapping[TrialStatus, float] = field(init=False)
    paired_score_count: int = field(init=False)
    mean_score_delta: float | None = field(init=False)
    comparison_hash: str = field(init=False)

    def __init__(self, *args: object, **kwargs: object) -> None:
        del args, kwargs
        raise TypeError("ExperimentComparison has no public constructor; use compare_experiment")

    def __post_init__(self) -> None:
        for field_name in ("experiment_id", "plan_hash", "baseline", "candidate"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"ExperimentComparison {field_name} cannot be empty")
        if not _is_sha256_identifier(self.plan_hash):
            raise ValueError("ExperimentComparison plan_hash must be a sha256 identifier")
        if self.baseline == self.candidate:
            raise ValueError("ExperimentComparison candidate must differ from baseline")
        if not isinstance(self.task_distribution, TaskDistributionManifest):
            raise TypeError(
                "ExperimentComparison task_distribution must be a TaskDistributionManifest"
            )
        trials = tuple(self.trials)
        if not trials or not all(isinstance(item, TrialComparison) for item in trials):
            raise ValueError("ExperimentComparison trials cannot be empty")
        if len(trials) != len(self.task_distribution.case_ids):
            raise ValueError("ExperimentComparison trials must match the Task distribution")
        for position, (case_id, trial) in enumerate(
            zip(self.task_distribution.case_ids, trials, strict=True)
        ):
            if trial.position != position or trial.case_id != case_id:
                raise ValueError("ExperimentComparison trials must follow Task distribution order")
        trial_ids = tuple(
            trial_id
            for trial in trials
            for trial_id in (trial.baseline_trial_id, trial.candidate_trial_id)
        )
        if len(set(trial_ids)) != len(trial_ids):
            raise ValueError("ExperimentComparison Trial ids must be globally unique")

        total_pairs = len(trials)
        baseline_passes = sum(item.baseline_passed is True for item in trials)
        candidate_passes = sum(item.candidate_passed is True for item in trials)
        baseline_pass_rate = baseline_passes / total_pairs
        candidate_pass_rate = candidate_passes / total_pairs
        baseline_status_counts = MappingProxyType(
            {
                status: sum(item.baseline_status is status for item in trials)
                for status in TrialStatus
            }
        )
        candidate_status_counts = MappingProxyType(
            {
                status: sum(item.candidate_status is status for item in trials)
                for status in TrialStatus
            }
        )
        baseline_status_rates = MappingProxyType(
            {status: count / total_pairs for status, count in baseline_status_counts.items()}
        )
        candidate_status_rates = MappingProxyType(
            {status: count / total_pairs for status, count in candidate_status_counts.items()}
        )
        paired_deltas = tuple(item.score_delta for item in trials if item.score_delta is not None)
        mean_score_delta = math.fsum(paired_deltas) / len(paired_deltas) if paired_deltas else None
        payload = _frozen_object(
            comparison_format_version=EXPERIMENT_COMPARISON_FORMAT_VERSION,
            experiment_id=self.experiment_id,
            plan_hash=self.plan_hash,
            task_distribution_hash=self.task_distribution.manifest_hash,
            baseline=self.baseline,
            candidate=self.candidate,
            trials=[_trial_comparison_payload(item) for item in trials],
            total_pairs=total_pairs,
            baseline_passes=baseline_passes,
            candidate_passes=candidate_passes,
            baseline_pass_rate=baseline_pass_rate,
            candidate_pass_rate=candidate_pass_rate,
            pass_rate_delta=candidate_pass_rate - baseline_pass_rate,
            baseline_status_counts={
                status.value: count for status, count in baseline_status_counts.items()
            },
            candidate_status_counts={
                status.value: count for status, count in candidate_status_counts.items()
            },
            baseline_status_rates={
                status.value: rate for status, rate in baseline_status_rates.items()
            },
            candidate_status_rates={
                status.value: rate for status, rate in candidate_status_rates.items()
            },
            paired_score_count=len(paired_deltas),
            mean_score_delta=mean_score_delta,
        )
        object.__setattr__(self, "trials", trials)
        object.__setattr__(
            self,
            "comparison_format_version",
            EXPERIMENT_COMPARISON_FORMAT_VERSION,
        )
        object.__setattr__(self, "total_pairs", total_pairs)
        object.__setattr__(self, "baseline_passes", baseline_passes)
        object.__setattr__(self, "candidate_passes", candidate_passes)
        object.__setattr__(self, "baseline_pass_rate", baseline_pass_rate)
        object.__setattr__(self, "candidate_pass_rate", candidate_pass_rate)
        object.__setattr__(
            self,
            "pass_rate_delta",
            candidate_pass_rate - baseline_pass_rate,
        )
        object.__setattr__(self, "baseline_status_counts", baseline_status_counts)
        object.__setattr__(self, "candidate_status_counts", candidate_status_counts)
        object.__setattr__(self, "baseline_status_rates", baseline_status_rates)
        object.__setattr__(self, "candidate_status_rates", candidate_status_rates)
        object.__setattr__(self, "paired_score_count", len(paired_deltas))
        object.__setattr__(self, "mean_score_delta", mean_score_delta)
        object.__setattr__(self, "comparison_hash", _configuration_hash(payload))


def _experiment_comparison(
    *,
    experiment_id: str,
    plan_hash: str,
    task_distribution: TaskDistributionManifest,
    baseline: str,
    candidate: str,
    trials: tuple[TrialComparison, ...],
) -> ExperimentComparison:
    comparison = object.__new__(ExperimentComparison)
    values = {
        "experiment_id": experiment_id,
        "plan_hash": plan_hash,
        "task_distribution": task_distribution,
        "baseline": baseline,
        "candidate": candidate,
        "trials": trials,
    }
    for field_name, value in values.items():
        object.__setattr__(comparison, field_name, value)
    comparison.__post_init__()
    return comparison


def _evaluation_fields(
    result: TrialResult,
) -> tuple[bool | None, float | None]:
    if result.evaluation is None:
        return None, None
    return result.evaluation.passed, result.evaluation.score


def compare_experiment(
    result: ExperimentResult,
    *,
    candidate: str,
) -> ExperimentComparison:
    """Project a complete, pre-registered candidate comparison without execution."""
    if not isinstance(result, ExperimentResult):
        raise TypeError("compare_experiment result must be an ExperimentResult")
    if not _is_registered_experiment_result(result):
        raise ValueError("compare_experiment requires a result verified by JsonlTrajectoryStore")
    if not isinstance(candidate, str) or not candidate.strip():
        raise ValueError("compare_experiment candidate cannot be empty")
    baseline = result.baseline
    if baseline is None:
        raise ValueError("Experiment plan does not declare a baseline")
    task_distribution = result.plan.task_distribution
    if task_distribution is None:
        raise ValueError("Experiment plan did not pre-register a Task distribution")
    if candidate == baseline:
        raise ValueError("compare_experiment candidate must differ from baseline")
    if candidate not in result.results:
        raise ValueError("compare_experiment candidate is not a planned variant")
    planned_candidates = set(result.results).difference({baseline})
    if planned_candidates != {candidate}:
        raise ValueError("compare_experiment candidate must be the sole pre-registered candidate")

    baseline_results = result.results[baseline]
    candidate_results = result.results[candidate]
    baseline_specs = result.plan.trial_specs[baseline]
    candidate_specs = result.plan.trial_specs[candidate]
    expected_pairs = len(task_distribution.case_ids)
    if len(baseline_results) != expected_pairs or len(candidate_results) != expected_pairs:
        raise ValueError("compare_experiment requires complete baseline and candidate variants")

    trials: list[TrialComparison] = []
    for position, case_id in enumerate(task_distribution.case_ids):
        baseline_spec = baseline_specs[position]
        candidate_spec = candidate_specs[position]
        projection = _comparison_projection(baseline_spec, case_id=case_id)
        projection_hash = _configuration_hash(projection)
        if projection_hash != _configuration_hash(
            _comparison_projection(candidate_spec, case_id=case_id)
        ):
            raise ValueError(
                f"compare_experiment Trial pair is not comparable at position {position}"
            )
        baseline_result = baseline_results[position]
        candidate_result = candidate_results[position]
        baseline_passed, baseline_score = _evaluation_fields(baseline_result)
        candidate_passed, candidate_score = _evaluation_fields(candidate_result)
        trials.append(
            _trial_comparison(
                position=position,
                case_id=case_id,
                case_hash=projection_hash,
                task_id=baseline_spec.task.id,
                seed=baseline_spec.seed,
                baseline_trial_id=baseline_result.trial_id,
                candidate_trial_id=candidate_result.trial_id,
                baseline_trajectory_hash=_trajectory_hash(baseline_result.trajectory),
                candidate_trajectory_hash=_trajectory_hash(candidate_result.trajectory),
                baseline_status=baseline_result.status,
                candidate_status=candidate_result.status,
                baseline_passed=baseline_passed,
                candidate_passed=candidate_passed,
                baseline_score=baseline_score,
                candidate_score=candidate_score,
            )
        )
    return _experiment_comparison(
        experiment_id=result.experiment_id,
        plan_hash=result.plan_hash,
        task_distribution=task_distribution,
        baseline=baseline,
        candidate=candidate,
        trials=tuple(trials),
    )
