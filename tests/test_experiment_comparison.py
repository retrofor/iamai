from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import replace

import pytest

from iamai.harness import (
    Action,
    ExactEvaluator,
    Experiment,
    ExperimentComparison,
    ExperimentPlan,
    ExperimentResult,
    JsonlTrajectoryStore,
    LookupEnvironment,
    ScriptedAgent,
    Task,
    TaskDistributionManifest,
    Trial,
    TrialComparison,
    TrialConfig,
    TrialStatus,
    compare_experiment,
)


def _capital_trial(*, trial_id: str, answer: str) -> Trial:
    return Trial(
        task=Task(
            id="capital-of-france",
            input={"question": "What is the capital of France?"},
        ),
        agent=ScriptedAgent(
            [Action.finish(answer)],
            name=f"{trial_id}-agent",
            version="1",
        ),
        environment=LookupEnvironment(
            {},
            name="country-capitals",
            version="1",
        ),
        evaluator=ExactEvaluator("Paris", version="1"),
        config=TrialConfig(trial_id=trial_id, seed=7, max_actions=1),
    )


def _digest(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _rewrite_jsonl_chain(path, entries: list[dict[str, object]]) -> None:
    previous_digest: str | None = None
    encoded_entries: list[str] = []
    for sequence, entry in enumerate(entries):
        entry["entry_sequence"] = sequence
        entry["previous_entry_digest"] = previous_digest
        entry.pop("entry_digest", None)
        entry["entry_digest"] = _digest(entry)
        previous_digest = entry["entry_digest"]  # type: ignore[assignment]
        encoded_entries.append(
            json.dumps(
                entry,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
    path.write_text("\n".join(encoded_entries) + "\n", encoding="utf-8")


def test_compare_persisted_experiment_reports_paired_baseline_evidence(tmp_path) -> None:
    async def scenario() -> None:
        distribution = TaskDistributionManifest(
            suite_id="capital-suite",
            version="1",
            split="test",
            case_ids=("capital-of-france/seed-7",),
            sampling_rule="ordered-full-set-v1",
        )
        path = tmp_path / "capital-evidence.jsonl"
        result = await Experiment(
            experiment_id="capital-evidence",
            version="1",
            baseline="baseline",
            task_distribution=distribution,
            trials={
                "baseline": (_capital_trial(trial_id="baseline-capital", answer="Lyon"),),
                "candidate": (_capital_trial(trial_id="candidate-capital", answer="Paris"),),
            },
        ).run(JsonlTrajectoryStore(path))
        loaded = JsonlTrajectoryStore(path).load()

        assert loaded is not None
        assert result.jsonl_verified
        assert loaded.jsonl_verified
        comparison = compare_experiment(loaded, candidate="candidate")

        assert comparison == compare_experiment(result, candidate="candidate")
        assert result.task_distribution == distribution
        assert loaded.task_distribution == distribution
        assert comparison.experiment_id == "capital-evidence"
        assert comparison.plan_hash == result.plan_hash
        assert comparison.task_distribution == distribution
        assert comparison.baseline == "baseline"
        assert comparison.candidate == "candidate"
        assert comparison.total_pairs == 1
        assert comparison.baseline_pass_rate == 0.0
        assert comparison.candidate_pass_rate == 1.0
        assert comparison.pass_rate_delta == 1.0
        assert comparison.paired_score_count == 1
        assert comparison.mean_score_delta == 1.0
        assert comparison.trials[0].task_id == "capital-of-france"
        assert comparison.trials[0].score_delta == 1.0
        assert comparison.comparison_format_version == "1"
        assert comparison.comparison_hash.startswith("sha256:")
        entries = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        candidate_commit = next(
            entry
            for entry in entries
            if entry["record_type"] == "trajectory.committed" and entry["variant"] == "candidate"
        )
        assert (
            comparison.trials[0].candidate_trajectory_hash == candidate_commit["trajectory_digest"]
        )
        with pytest.raises(TypeError, match="no public constructor"):
            ExperimentComparison(
                experiment_id=comparison.experiment_id,
                plan_hash=comparison.plan_hash,
                task_distribution=comparison.task_distribution,
                baseline=comparison.baseline,
                candidate=comparison.candidate,
                trials=comparison.trials,
            )

    asyncio.run(scenario())


def test_comparison_keeps_failed_and_budget_exhausted_pairs_in_the_denominator(
    tmp_path,
) -> None:
    class FailingAgent:
        name = "failing-agent"
        version = "1"
        configuration = {"failure": "fixture"}

        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            raise RuntimeError("fixture failure")

    def trial(*, trial_id: str, agent: object) -> Trial:
        return Trial(
            task=Task(id="paired-case", input={"question": "answer"}),
            agent=agent,  # type: ignore[arg-type]
            environment=LookupEnvironment(
                {"answer": "Paris"},
                name="paired-environment",
                version="1",
            ),
            evaluator=ExactEvaluator("Paris", version="1"),
            config=TrialConfig(trial_id=trial_id, seed=11, max_actions=1),
        )

    def scripted(trial_id: str, action: Action) -> Trial:
        return trial(
            trial_id=trial_id,
            agent=ScriptedAgent((action,), name=f"{trial_id}-agent", version="1"),
        )

    async def scenario() -> None:
        result = await Experiment(
            experiment_id="status-evidence",
            version="1",
            baseline="baseline",
            task_distribution=TaskDistributionManifest(
                suite_id="status-suite",
                version="1",
                split="test",
                case_ids=("failed-candidate", "budget-candidate"),
                sampling_rule="ordered-full-set-v1",
            ),
            trials={
                "baseline": (
                    scripted("baseline-failed-pair", Action.finish("Paris")),
                    scripted("baseline-budget-pair", Action.finish("Paris")),
                ),
                "candidate": (
                    trial(trial_id="candidate-failed", agent=FailingAgent()),
                    scripted(
                        "candidate-budget",
                        Action.invoke("lookup", {"key": "answer"}),
                    ),
                ),
            },
        ).run(JsonlTrajectoryStore(tmp_path / "status-evidence.jsonl"))

        comparison = compare_experiment(result, candidate="candidate")

        assert comparison.total_pairs == 2
        assert comparison.candidate_pass_rate == 0.0
        assert comparison.candidate_status_counts == {
            TrialStatus.COMPLETED: 0,
            TrialStatus.BUDGET_EXHAUSTED: 1,
            TrialStatus.FAILED: 1,
            TrialStatus.CANCELLED: 0,
        }
        assert comparison.candidate_status_rates[TrialStatus.FAILED] == 0.5
        assert comparison.candidate_status_rates[TrialStatus.BUDGET_EXHAUSTED] == 0.5
        assert comparison.paired_score_count == 1
        assert comparison.mean_score_delta == -1.0

    asyncio.run(scenario())


def test_comparison_hash_binds_the_exact_persisted_trajectories(tmp_path) -> None:
    class MessageFailingAgent:
        name = "message-failing-agent"
        version = "1"
        configuration = {"fixture": "same-declaration"}

        def __init__(self, message: str) -> None:
            self.message = message

        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            raise RuntimeError(self.message)

    def failing_candidate(message: str) -> Trial:
        return Trial(
            task=Task(
                id="capital-of-france",
                input={"question": "What is the capital of France?"},
            ),
            agent=MessageFailingAgent(message),
            environment=LookupEnvironment(
                {},
                name="country-capitals",
                version="1",
            ),
            evaluator=ExactEvaluator("Paris", version="1"),
            config=TrialConfig(
                trial_id="trajectory-hash-candidate",
                seed=7,
                max_actions=1,
            ),
        )

    async def run(path, failure_message: str):
        result = await Experiment(
            experiment_id="trajectory-hash-evidence",
            version="1",
            baseline="baseline",
            task_distribution=TaskDistributionManifest(
                suite_id="trajectory-hash-suite",
                version="1",
                split="test",
                case_ids=("capital/seed-7",),
                sampling_rule="ordered-full-set-v1",
            ),
            trials={
                "baseline": (
                    _capital_trial(
                        trial_id="trajectory-hash-baseline",
                        answer="Paris",
                    ),
                ),
                "candidate": (failing_candidate(failure_message),),
            },
        ).run(JsonlTrajectoryStore(path))
        return compare_experiment(result, candidate="candidate")

    async def scenario() -> None:
        first = await run(tmp_path / "trajectory-first.jsonl", "first failure")
        second = await run(tmp_path / "trajectory-second.jsonl", "second failure")

        assert first.plan_hash == second.plan_hash
        assert first.candidate_status_counts == second.candidate_status_counts
        assert (
            first.trials[0].candidate_trajectory_hash != second.trials[0].candidate_trajectory_hash
        )
        assert first.comparison_hash != second.comparison_hash

    asyncio.run(scenario())


def test_task_distribution_rejects_a_string_as_case_sequence() -> None:
    with pytest.raises(TypeError, match="case_ids must be a sequence"):
        TaskDistributionManifest(
            suite_id="invalid-suite",
            version="1",
            split="test",
            case_ids="not-a-case-sequence",  # type: ignore[arg-type]
            sampling_rule="ordered-full-set-v1",
        )


def test_experiment_plan_preserves_positional_provenance_compatibility() -> None:
    baseline = _capital_trial(trial_id="positional-baseline", answer="Lyon")
    candidate = _capital_trial(trial_id="positional-candidate", answer="Paris")

    plan = ExperimentPlan(
        "positional-provenance",
        "1",
        {
            "baseline": (baseline.trajectory,),
            "candidate": (candidate.trajectory,),
        },
        "baseline",
        {"source_revision": "legacy-positional-call"},
    )

    assert plan.provenance == {"source_revision": "legacy-positional-call"}
    assert plan.task_distribution is None


def test_trial_comparison_cannot_be_publicly_constructed() -> None:
    with pytest.raises(TypeError, match="no public constructor"):
        TrialComparison(
            position=0,
            case_id="public-forgery",
            case_hash=f"sha256:{'0' * 64}",
            task_id="public-forgery-task",
            seed=0,
            baseline_trial_id="public-baseline",
            candidate_trial_id="public-candidate",
            baseline_status=TrialStatus.COMPLETED,
            candidate_status=TrialStatus.COMPLETED,
            baseline_passed=True,
            candidate_passed=True,
            baseline_score=1.0,
            candidate_score=1.0,
        )
    with pytest.raises(TypeError, match="no public constructor"):
        TrialComparison()
    with pytest.raises(TypeError, match="no public constructor"):
        ExperimentComparison()


def test_distribution_rejects_unpaired_task_input_before_trials_start() -> None:
    baseline = _capital_trial(trial_id="baseline-preflight", answer="Paris")
    candidate = Trial(
        task=Task(
            id="capital-of-france",
            input={"question": "What is the capital of Italy?"},
        ),
        agent=ScriptedAgent(
            (Action.finish("Rome"),),
            name="candidate-preflight-agent",
            version="1",
        ),
        environment=LookupEnvironment(
            {},
            name="country-capitals",
            version="1",
        ),
        evaluator=ExactEvaluator("Paris", version="1"),
        config=TrialConfig(
            trial_id="candidate-preflight",
            seed=7,
            max_actions=1,
        ),
    )

    with pytest.raises(ValueError, match="differ only by Agent declaration"):
        Experiment(
            experiment_id="preflight-evidence",
            version="1",
            baseline="baseline",
            task_distribution=TaskDistributionManifest(
                suite_id="preflight-suite",
                version="1",
                split="test",
                case_ids=("capital/seed-7",),
                sampling_rule="ordered-full-set-v1",
            ),
            trials={"baseline": (baseline,), "candidate": (candidate,)},
        )

    assert baseline.trajectory.records == ()
    assert candidate.trajectory.records == ()


def test_distribution_uses_json_type_identity_for_pairing() -> None:
    def trial(*, trial_id: str, task_value: object) -> Trial:
        return Trial(
            task=Task(id="json-type-case", input={"value": task_value}),
            agent=ScriptedAgent(
                (Action.finish("done"),),
                name=f"{trial_id}-agent",
                version="1",
            ),
            environment=LookupEnvironment(
                {},
                name="json-type-environment",
                version="1",
            ),
            evaluator=ExactEvaluator("done", version="1"),
            config=TrialConfig(trial_id=trial_id, seed=0, max_actions=1),
        )

    baseline = trial(trial_id="json-bool", task_value=True)
    candidate = trial(trial_id="json-int", task_value=1)

    with pytest.raises(ValueError, match="differ only by Agent declaration"):
        Experiment(
            experiment_id="json-type-evidence",
            version="1",
            baseline="baseline",
            task_distribution=TaskDistributionManifest(
                suite_id="json-type-suite",
                version="1",
                split="test",
                case_ids=("json-type/seed-0",),
                sampling_rule="ordered-full-set-v1",
            ),
            trials={"baseline": (baseline,), "candidate": (candidate,)},
        )


def test_result_projection_uses_json_type_identity(tmp_path) -> None:
    async def scenario() -> None:
        trial = Trial(
            task=Task(id="json-result-type", input=None),
            agent=ScriptedAgent(
                (Action.finish(True),),
                name="json-result-agent",
                version="1",
            ),
            environment=LookupEnvironment(
                {},
                name="json-result-environment",
                version="1",
            ),
            evaluator=ExactEvaluator(True, version="1"),
            config=TrialConfig(trial_id="json-result", seed=0, max_actions=1),
        )
        result = await Experiment(
            experiment_id="json-result-projection",
            version="1",
            trials={"only": (trial,)},
        ).run(JsonlTrajectoryStore(tmp_path / "json-result-projection.jsonl"))
        forged = replace(result.results["only"][0], final_output=1)

        with pytest.raises(ValueError, match="does not match its Trajectory"):
            ExperimentResult(
                plan=result.plan,
                results={"only": (forged,)},
                started_trial_ids={"only": ()},
            )

    asyncio.run(scenario())


def test_live_declaration_drift_uses_json_type_identity(tmp_path) -> None:
    class MutableAgent:
        name = "mutable-agent"
        version = "1"

        def __init__(self) -> None:
            self.configuration = {"mode": True}
            self.calls = 0

        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            self.calls += 1
            return Action.finish("done")

    async def scenario() -> None:
        agent = MutableAgent()
        experiment = Experiment(
            experiment_id="json-live-declaration",
            version="1",
            trials={
                "only": (
                    Trial(
                        task=Task(id="json-live-declaration", input=None),
                        agent=agent,
                        environment=LookupEnvironment(
                            {},
                            name="json-live-environment",
                            version="1",
                        ),
                        evaluator=ExactEvaluator("done", version="1"),
                        config=TrialConfig(
                            trial_id="json-live-trial",
                            seed=0,
                            max_actions=1,
                        ),
                    ),
                )
            },
        )
        agent.configuration["mode"] = 1

        with pytest.raises(ValueError, match="declarations drifted"):
            await experiment.run(JsonlTrajectoryStore(tmp_path / "json-live-declaration.jsonl"))

        assert agent.calls == 0

    asyncio.run(scenario())


def test_distribution_preregisters_exactly_one_candidate() -> None:
    with pytest.raises(ValueError, match="exactly one baseline and one candidate"):
        Experiment(
            experiment_id="candidate-selection",
            version="1",
            baseline="baseline",
            task_distribution=TaskDistributionManifest(
                suite_id="candidate-selection-suite",
                version="1",
                split="test",
                case_ids=("capital/seed-7",),
                sampling_rule="ordered-full-set-v1",
            ),
            trials={
                "baseline": (_capital_trial(trial_id="selection-baseline", answer="Lyon"),),
                "candidate-a": (_capital_trial(trial_id="selection-a", answer="Paris"),),
                "candidate-b": (_capital_trial(trial_id="selection-b", answer="Paris"),),
            },
        )


def test_comparison_rejects_a_legacy_plan_without_preregistered_distribution(
    tmp_path,
) -> None:
    async def scenario() -> None:
        path = tmp_path / "legacy-comparison.jsonl"
        result = await Experiment(
            experiment_id="legacy-comparison",
            version="1",
            baseline="baseline",
            trials={
                "baseline": (_capital_trial(trial_id="legacy-baseline", answer="Lyon"),),
                "candidate": (_capital_trial(trial_id="legacy-candidate", answer="Paris"),),
            },
        ).run(JsonlTrajectoryStore(path))

        manifest = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
        assert "task_distribution" not in manifest["plan"]

        with pytest.raises(ValueError, match="did not pre-register"):
            compare_experiment(result, candidate="candidate")

    asyncio.run(scenario())


def test_comparison_rejects_an_incomplete_candidate_without_changing_denominator(
    tmp_path,
) -> None:
    class InterruptedHarness(BaseException):
        pass

    class InterruptingAgent:
        name = "interrupting-agent"
        version = "1"
        configuration = {"fixture": "interrupt-after-start"}

        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            raise InterruptedHarness

    async def scenario() -> None:
        path = tmp_path / "incomplete-comparison.jsonl"
        candidate = Trial(
            task=Task(
                id="capital-of-france",
                input={"question": "What is the capital of France?"},
            ),
            agent=InterruptingAgent(),
            environment=LookupEnvironment(
                {},
                name="country-capitals",
                version="1",
            ),
            evaluator=ExactEvaluator("Paris", version="1"),
            config=TrialConfig(
                trial_id="incomplete-candidate",
                seed=7,
                max_actions=1,
            ),
        )
        experiment = Experiment(
            experiment_id="incomplete-comparison",
            version="1",
            baseline="baseline",
            task_distribution=TaskDistributionManifest(
                suite_id="incomplete-suite",
                version="1",
                split="test",
                case_ids=("capital/seed-7",),
                sampling_rule="ordered-full-set-v1",
            ),
            trials={
                "baseline": (_capital_trial(trial_id="incomplete-baseline", answer="Lyon"),),
                "candidate": (candidate,),
            },
        )
        store = JsonlTrajectoryStore(path)

        with pytest.raises(InterruptedHarness):
            await experiment.run(store)
        incomplete = store.load()

        assert incomplete is not None
        assert incomplete.results["baseline"]
        assert incomplete.results["candidate"] == ()
        assert incomplete.started_trial_ids["candidate"] == ("incomplete-candidate",)
        with pytest.raises(ValueError, match="requires complete"):
            compare_experiment(incomplete, candidate="candidate")

    asyncio.run(scenario())


def test_comparison_rejects_a_publicly_reconstructed_post_hoc_subset(tmp_path) -> None:
    async def scenario() -> None:
        original = await Experiment(
            experiment_id="post-hoc-subset",
            version="1",
            baseline="baseline",
            task_distribution=TaskDistributionManifest(
                suite_id="post-hoc-suite",
                version="1",
                split="test",
                case_ids=("no-change", "successful-only"),
                sampling_rule="ordered-full-set-v1",
            ),
            trials={
                "baseline": (
                    _capital_trial(trial_id="subset-baseline-0", answer="Lyon"),
                    _capital_trial(trial_id="subset-baseline-1", answer="Lyon"),
                ),
                "candidate": (
                    _capital_trial(trial_id="subset-candidate-0", answer="Lyon"),
                    _capital_trial(trial_id="subset-candidate-1", answer="Paris"),
                ),
            },
        ).run(JsonlTrajectoryStore(tmp_path / "post-hoc-subset.jsonl"))
        subset_plan = ExperimentPlan(
            experiment_id="post-hoc-subset-forged",
            version="1",
            trial_specs={
                "baseline": (original.plan.trial_specs["baseline"][1],),
                "candidate": (original.plan.trial_specs["candidate"][1],),
            },
            baseline="baseline",
            task_distribution=TaskDistributionManifest(
                suite_id="post-hoc-suite",
                version="1",
                split="test",
                case_ids=("successful-only",),
                sampling_rule="post-hoc-subset",
            ),
        )
        reconstructed = ExperimentResult(
            plan=subset_plan,
            results={
                "baseline": (original.results["baseline"][1],),
                "candidate": (original.results["candidate"][1],),
            },
            started_trial_ids={"baseline": (), "candidate": ()},
        )
        clone = replace(original)

        assert not reconstructed.jsonl_verified
        assert not clone.jsonl_verified
        assert clone != original
        with pytest.raises(ValueError, match="verified by JsonlTrajectoryStore"):
            compare_experiment(reconstructed, candidate="candidate")
        with pytest.raises(ValueError, match="verified by JsonlTrajectoryStore"):
            compare_experiment(clone, candidate="candidate")

    asyncio.run(scenario())


def test_store_rejects_distribution_drift_before_replacement_trials_run(
    tmp_path,
) -> None:
    class CountingAgent:
        name = "counting-agent"
        version = "1"
        configuration = {"answer": "Paris"}

        def __init__(self) -> None:
            self.calls = 0

        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            self.calls += 1
            return Action.finish("Paris")

    def trial(*, trial_id: str, agent: CountingAgent) -> Trial:
        return Trial(
            task=Task(id="distribution-drift", input=None),
            agent=agent,
            environment=LookupEnvironment(
                {},
                name="distribution-drift-environment",
                version="1",
            ),
            evaluator=ExactEvaluator("Paris", version="1"),
            config=TrialConfig(trial_id=trial_id, seed=3, max_actions=1),
        )

    def manifest(split: str) -> TaskDistributionManifest:
        return TaskDistributionManifest(
            suite_id="distribution-drift-suite",
            version="1",
            split=split,
            case_ids=("distribution-drift/seed-3",),
            sampling_rule="ordered-full-set-v1",
        )

    async def scenario() -> None:
        path = tmp_path / "distribution-drift.jsonl"
        await Experiment(
            experiment_id="distribution-drift",
            version="1",
            baseline="baseline",
            task_distribution=manifest("dev"),
            trials={
                "baseline": (trial(trial_id="drift-baseline", agent=CountingAgent()),),
                "candidate": (trial(trial_id="drift-candidate", agent=CountingAgent()),),
            },
        ).run(JsonlTrajectoryStore(path))

        replacement_baseline = CountingAgent()
        replacement_candidate = CountingAgent()
        replacement_trials = {
            "baseline": (trial(trial_id="drift-baseline", agent=replacement_baseline),),
            "candidate": (trial(trial_id="drift-candidate", agent=replacement_candidate),),
        }
        changed = Experiment(
            experiment_id="distribution-drift",
            version="1",
            baseline="baseline",
            task_distribution=manifest("test"),
            trials=replacement_trials,
        )

        with pytest.raises(ValueError, match="different Experiment plan"):
            await changed.run(JsonlTrajectoryStore(path))

        assert replacement_baseline.calls == 0
        assert replacement_candidate.calls == 0
        assert all(
            planned_trial.trajectory.records == ()
            for variant in replacement_trials.values()
            for planned_trial in variant
        )

    asyncio.run(scenario())


def test_store_rejects_a_tampered_task_distribution_manifest(tmp_path) -> None:
    async def scenario() -> None:
        path = tmp_path / "tampered-distribution.jsonl"
        store = JsonlTrajectoryStore(path)
        await Experiment(
            experiment_id="tampered-distribution",
            version="1",
            baseline="baseline",
            task_distribution=TaskDistributionManifest(
                suite_id="tampered-suite",
                version="1",
                split="test",
                case_ids=("capital/seed-7",),
                sampling_rule="ordered-full-set-v1",
            ),
            trials={
                "baseline": (_capital_trial(trial_id="tampered-baseline", answer="Lyon"),),
                "candidate": (_capital_trial(trial_id="tampered-candidate", answer="Paris"),),
            },
        ).run(store)
        entries = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        plan = entries[0]["plan"]
        assert isinstance(plan, dict)
        distribution = plan["task_distribution"]
        assert isinstance(distribution, dict)
        distribution["split"] = "dev"
        entries[0]["plan_hash"] = _digest(plan)
        _rewrite_jsonl_chain(path, entries)

        with pytest.raises(ValueError, match="Task distribution hash is invalid"):
            store.load()

    asyncio.run(scenario())


def test_store_rejects_unhashed_post_hoc_plan_claims(tmp_path) -> None:
    async def scenario() -> None:
        path = tmp_path / "post-hoc-plan-claim.jsonl"
        store = JsonlTrajectoryStore(path)
        await Experiment(
            experiment_id="post-hoc-plan-claim",
            version="1",
            baseline="baseline",
            trials={
                "baseline": (_capital_trial(trial_id="post-hoc-baseline", answer="Lyon"),),
                "candidate": (_capital_trial(trial_id="post-hoc-candidate", answer="Paris"),),
            },
        ).run(store)
        entries = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        plan = entries[0]["plan"]
        assert isinstance(plan, dict)
        plan["post_hoc_claim"] = {"split": "test"}
        _rewrite_jsonl_chain(path, entries)

        with pytest.raises(ValueError, match="plan payload hash does not match"):
            store.load()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "location",
    ("entry", "trajectory", "task", "record", "record_payload"),
)
def test_store_rejects_unknown_evidence_fields_with_recomputed_digests(
    tmp_path,
    location: str,
) -> None:
    async def scenario() -> None:
        path = tmp_path / f"unknown-{location}.jsonl"
        store = JsonlTrajectoryStore(path)
        await Experiment(
            experiment_id=f"unknown-{location}",
            version="1",
            trials={
                "only": (
                    _capital_trial(
                        trial_id=f"unknown-{location}-trial",
                        answer="Paris",
                    ),
                )
            },
        ).run(store)
        entries = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        committed = entries[-1]
        trajectory = committed["trajectory"]
        assert isinstance(trajectory, dict)
        records = trajectory["records"]
        assert isinstance(records, list)
        first_record = records[0]
        assert isinstance(first_record, dict)

        if location == "entry":
            committed["post_hoc_claim"] = "forged"
        elif location == "trajectory":
            trajectory["claimed_final_output"] = "forged"
        elif location == "task":
            task = trajectory["task"]
            assert isinstance(task, dict)
            task["post_hoc_claim"] = "forged"
        elif location == "record":
            first_record["post_hoc_claim"] = "forged"
        else:
            payload = first_record["payload"]
            assert isinstance(payload, dict)
            payload["post_hoc_claim"] = "forged"

        if location != "entry":
            committed["trajectory_digest"] = _digest(trajectory)
        _rewrite_jsonl_chain(path, entries)

        with pytest.raises(ValueError, match="fields are invalid"):
            store.load()

    asyncio.run(scenario())


def test_store_requires_the_initial_previous_digest_field(tmp_path) -> None:
    async def scenario() -> None:
        path = tmp_path / "missing-previous-digest.jsonl"
        store = JsonlTrajectoryStore(path)
        await Experiment(
            experiment_id="missing-previous-digest",
            version="1",
            trials={
                "only": (
                    _capital_trial(
                        trial_id="missing-previous-digest-trial",
                        answer="Paris",
                    ),
                )
            },
        ).run(store)
        entries = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        entries[0].pop("previous_entry_digest")
        entries[0].pop("entry_digest")
        entries[0]["entry_digest"] = _digest(entries[0])
        previous_digest = entries[0]["entry_digest"]
        for entry in entries[1:]:
            entry["previous_entry_digest"] = previous_digest
            entry.pop("entry_digest")
            entry["entry_digest"] = _digest(entry)
            previous_digest = entry["entry_digest"]
        path.write_text(
            "".join(
                f"{json.dumps(entry, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(',', ':'))}\n"
                for entry in entries
            ),
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match="entry chain"):
            store.load()

    asyncio.run(scenario())
