from __future__ import annotations

import asyncio
import hashlib
import json
import os
import stat
import subprocess
import sys
import time
from collections.abc import Mapping
from dataclasses import replace

import pytest

from iamai.harness import _jsonl as jsonl_module
from iamai.harness import (
    Action,
    ExactEvaluator,
    Experiment,
    ExperimentPlan,
    ExperimentResult,
    JsonlTrajectoryStore,
    LookupEnvironment,
    ScriptedAgent,
    Task,
    Trial,
    TrialConfig,
    TrialStatus,
    replay,
)


def _capital_trial(*, trial_id: str, output: str) -> Trial:
    return Trial(
        task=Task(
            id="capital-of-france",
            input={"question": "What is the capital of France?"},
        ),
        agent=ScriptedAgent(
            [Action.finish(output)],
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


def test_experiment_persists_complete_trajectories_by_variant(tmp_path) -> None:
    async def scenario() -> None:
        path = tmp_path / "capital-comparison.jsonl"
        experiment = Experiment(
            experiment_id="capital-comparison",
            version="1",
            baseline="baseline",
            trials={
                "baseline": (_capital_trial(trial_id="baseline-7", output="Lyon"),),
                "candidate": (_capital_trial(trial_id="candidate-7", output="Paris"),),
            },
        )

        result = await experiment.run(JsonlTrajectoryStore(path))
        loaded = JsonlTrajectoryStore(path).load()

        assert result.complete is True
        assert result.experiment_id == "capital-comparison"
        assert result.version == "1"
        assert result.baseline == "baseline"
        assert result.planned_trial_ids == {
            "baseline": ("baseline-7",),
            "candidate": ("candidate-7",),
        }
        assert result.results["baseline"][0].status is TrialStatus.COMPLETED
        assert result.results["baseline"][0].evaluation is not None
        assert result.results["baseline"][0].evaluation.passed is False
        assert result.results["candidate"][0].evaluation is not None
        assert result.results["candidate"][0].evaluation.passed is True
        assert loaded == result
        assert all(
            replay(trial_result.trajectory) == trial_result
            for variant_results in result.results.values()
            for trial_result in variant_results
        )
        assert len(path.read_text(encoding="utf-8").splitlines()) == 5

    asyncio.run(scenario())


def test_store_reports_and_explicitly_repairs_a_torn_final_record(tmp_path) -> None:
    async def scenario() -> None:
        path = tmp_path / "torn-tail.jsonl"
        store = JsonlTrajectoryStore(path)
        original = await Experiment(
            experiment_id="torn-tail",
            version="1",
            baseline="baseline",
            trials={
                "baseline": (_capital_trial(trial_id="baseline-tail", output="Paris"),),
            },
        ).run(store)
        with path.open("ab") as stream:
            stream.write(b'{"record_type":"trajectory.committed"')

        with pytest.raises(ValueError, match=r"torn-tail\.jsonl:4"):
            store.load()

        assert store.repair_tail() is True
        assert store.load() == original
        assert store.repair_tail() is False
        assert path.read_bytes().endswith(b"\n")

    asyncio.run(scenario())


def test_store_rejects_reordered_complete_records(tmp_path) -> None:
    async def scenario() -> None:
        path = tmp_path / "reordered-records.jsonl"
        store = JsonlTrajectoryStore(path)
        await Experiment(
            experiment_id="reordered-records",
            version="1",
            baseline="baseline",
            trials={
                "baseline": (_capital_trial(trial_id="reordered-a", output="Lyon"),),
                "candidate": (_capital_trial(trial_id="reordered-b", output="Paris"),),
            },
        ).run(store)
        lines = path.read_bytes().splitlines(keepends=True)
        path.write_bytes(b"".join((lines[0], lines[2], lines[1])))

        with pytest.raises(ValueError, match="entry chain"):
            store.load()

    asyncio.run(scenario())


def test_experiment_resume_replays_committed_trials_without_effects(tmp_path) -> None:
    async def scenario() -> None:
        path = tmp_path / "resume.jsonl"
        first = Experiment(
            experiment_id="resume",
            version="1",
            baseline="baseline",
            trials={
                "baseline": (_capital_trial(trial_id="resume-a", output="Lyon"),),
                "candidate": (_capital_trial(trial_id="resume-b", output="Paris"),),
            },
        )
        original = await first.run(JsonlTrajectoryStore(path))
        line_count = len(path.read_bytes().splitlines())

        resumed_baseline = _capital_trial(trial_id="resume-a", output="Lyon")
        resumed_candidate = _capital_trial(trial_id="resume-b", output="Paris")
        resumed = await Experiment(
            experiment_id="resume",
            version="1",
            baseline="baseline",
            trials={
                "baseline": (resumed_baseline,),
                "candidate": (resumed_candidate,),
            },
        ).run(JsonlTrajectoryStore(path))

        assert resumed == original
        assert resumed_baseline.trajectory.records == ()
        assert resumed_candidate.trajectory.records == ()
        assert len(path.read_bytes().splitlines()) == line_count

    asyncio.run(scenario())


def test_store_does_not_commit_a_complete_json_object_without_final_lf(tmp_path) -> None:
    async def scenario() -> None:
        path = tmp_path / "missing-commit-marker.jsonl"
        store = JsonlTrajectoryStore(path)
        await Experiment(
            experiment_id="missing-commit-marker",
            version="1",
            baseline="baseline",
            trials={
                "baseline": (_capital_trial(trial_id="missing-lf", output="Paris"),),
            },
        ).run(store)
        path.write_bytes(path.read_bytes()[:-1])

        with pytest.raises(ValueError, match="torn JSONL Store record"):
            store.load()

        assert store.repair_tail() is True
        recovered = store.load()
        assert recovered is not None
        assert recovered.complete is False
        assert recovered.results == {"baseline": ()}

    asyncio.run(scenario())


def test_interrupted_trial_is_not_reexecuted_while_pending_trials_continue(
    tmp_path,
) -> None:
    class SimulatedProcessCrash(BaseException):
        pass

    class CrashingAgent:
        name = "interruptible-agent"
        version = "1"
        configuration: Mapping[str, object] = {"policy": "fixture"}

        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            raise SimulatedProcessCrash

    class ReplacementAgent:
        name = "interruptible-agent"
        version = "1"
        configuration: Mapping[str, object] = {"policy": "fixture"}

        def __init__(self) -> None:
            self.calls = 0

        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            self.calls += 1
            return Action.finish("Paris")

    def trial(agent: object) -> Trial:
        return Trial(
            task=Task(id="interrupted-task", input=None),
            agent=agent,  # type: ignore[arg-type]
            environment=LookupEnvironment(
                {},
                name="interrupted-environment",
                version="1",
            ),
            evaluator=ExactEvaluator("Paris", version="1"),
            config=TrialConfig(trial_id="interrupted-trial", max_actions=1),
        )

    async def scenario() -> None:
        path = tmp_path / "interrupted.jsonl"
        store = JsonlTrajectoryStore(path)
        never_started = _capital_trial(
            trial_id="never-started-trial",
            output="Paris",
        )
        with pytest.raises(SimulatedProcessCrash):
            await Experiment(
                experiment_id="interrupted",
                version="1",
                baseline="baseline",
                trials={
                    "baseline": (trial(CrashingAgent()),),
                    "candidate": (never_started,),
                },
            ).run(store)

        interrupted = store.load()
        assert interrupted is not None
        assert interrupted.complete is False
        assert interrupted.started_trial_ids == {
            "baseline": ("interrupted-trial",),
            "candidate": (),
        }
        assert never_started.trajectory.records == ()

        replacement = ReplacementAgent()
        pending = _capital_trial(trial_id="never-started-trial", output="Paris")
        resumed = await Experiment(
            experiment_id="interrupted",
            version="1",
            baseline="baseline",
            trials={
                "baseline": (trial(replacement),),
                "candidate": (pending,),
            },
        ).run(store)

        assert replacement.calls == 0
        assert pending.trajectory.records
        assert resumed.complete is False
        assert resumed.started_trial_ids == {
            "baseline": ("interrupted-trial",),
            "candidate": (),
        }
        assert [result.trial_id for result in resumed.results["candidate"]] == [
            "never-started-trial"
        ]

    asyncio.run(scenario())


def test_experiment_plan_exposes_deeply_immutable_pending_provenance(tmp_path) -> None:
    async def scenario() -> None:
        provenance = {
            "source_revision": "abc123",
            "datasets": {"capitals": ["sha256:fixture"]},
        }
        experiment = Experiment(
            experiment_id="inspectable-plan",
            version="1",
            baseline="baseline",
            provenance=provenance,
            trials={
                "baseline": (_capital_trial(trial_id="inspectable", output="Paris"),),
            },
        )
        provenance["datasets"]["capitals"].append("mutated")

        assert isinstance(experiment.plan, ExperimentPlan)
        assert experiment.plan.provenance == {
            "source_revision": "abc123",
            "datasets": {"capitals": ("sha256:fixture",)},
        }
        planned = experiment.plan.trial_specs["baseline"][0]
        assert planned.task.id == "capital-of-france"
        assert planned.seed == 7
        assert planned.configuration["max_actions"] == 1
        assert planned.records == ()
        with pytest.raises(TypeError):
            experiment.plan.provenance["changed"] = True  # type: ignore[index]

        stored = await experiment.run(
            JsonlTrajectoryStore(tmp_path / "inspectable-plan.jsonl")
        )
        assert stored.plan == experiment.plan

    asyncio.run(scenario())


def test_experiment_rejects_non_object_provenance_instead_of_dropping_it() -> None:
    with pytest.raises(TypeError, match="provenance must be an object"):
        Experiment(
            experiment_id="invalid-provenance",
            version="1",
            baseline="baseline",
            trials={
                "baseline": (
                    _capital_trial(trial_id="invalid-provenance", output="Paris"),
                ),
            },
            provenance=[],  # type: ignore[arg-type]
        )


def test_store_rejects_a_second_writer_before_trial_effects(tmp_path) -> None:
    class BlockingAgent:
        name = "single-writer-agent"
        version = "1"
        configuration: Mapping[str, object] = {}

        def __init__(self, started: asyncio.Event) -> None:
            self.started = started

        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            self.started.set()
            await asyncio.Event().wait()
            raise AssertionError("unreachable")

    def trial(trial_id: str, agent: object) -> Trial:
        return Trial(
            task=Task(id="single-writer", input=None),
            agent=agent,  # type: ignore[arg-type]
            environment=LookupEnvironment(
                {},
                name="single-writer-environment",
                version="1",
            ),
            evaluator=ExactEvaluator(None, version="1"),
            config=TrialConfig(trial_id=trial_id, max_actions=1),
        )

    async def scenario() -> None:
        path = tmp_path / "single-writer.jsonl"
        first_started = asyncio.Event()
        first = asyncio.create_task(
            Experiment(
                experiment_id="single-writer",
                version="1",
                baseline="baseline",
                trials={
                    "baseline": (
                        trial("single-writer-trial", BlockingAgent(first_started)),
                    )
                },
            ).run(JsonlTrajectoryStore(path))
        )
        await first_started.wait()

        second_started = asyncio.Event()
        second_trial = trial(
            "single-writer-trial",
            BlockingAgent(second_started),
        )
        with pytest.raises(RuntimeError, match="active writer"):
            await Experiment(
                experiment_id="single-writer",
                version="1",
                baseline="baseline",
                trials={"baseline": (second_trial,)},
            ).run(JsonlTrajectoryStore(path))
        assert second_started.is_set() is False
        assert second_trial.trajectory.records == ()
        with pytest.raises(RuntimeError, match="active writer"):
            JsonlTrajectoryStore(path).repair_tail()
        with pytest.raises(RuntimeError, match="active writer"):
            JsonlTrajectoryStore(path).load()

        first.cancel()
        with pytest.raises(asyncio.CancelledError):
            await first

    asyncio.run(scenario())


@pytest.mark.skipif(os.name == "nt", reason="this probe targets POSIX flock")
def test_store_lock_blocks_cross_process_load_and_repair_then_recovers(tmp_path) -> None:
    async def prepare() -> ExperimentResult:
        return await Experiment(
            experiment_id="cross-process-lock",
            version="1",
            trials={
                "candidate": (
                    _capital_trial(trial_id="cross-process-lock", output="Paris"),
                ),
            },
        ).run(JsonlTrajectoryStore(tmp_path / "cross-process-lock.jsonl"))

    original = asyncio.run(prepare())
    path = tmp_path / "cross-process-lock.jsonl"
    ready = tmp_path / "writer-ready"
    release = tmp_path / "writer-release"
    program = (
        "import sys, time\n"
        "from pathlib import Path\n"
        "from iamai.harness import JsonlTrajectoryStore\n"
        "path, ready, release = map(Path, sys.argv[1:])\n"
        "with JsonlTrajectoryStore(path)._writer():\n"
        "    ready.touch()\n"
        "    deadline = time.monotonic() + 10\n"
        "    while not release.exists():\n"
        "        if time.monotonic() >= deadline:\n"
        "            raise TimeoutError('release signal was not received')\n"
        "        time.sleep(0.01)\n"
    )
    process = subprocess.Popen(
        [sys.executable, "-c", program, str(path), str(ready), str(release)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 10
        while not ready.exists():
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                pytest.fail(f"lock process exited early: {stdout}\n{stderr}")
            if time.monotonic() >= deadline:
                pytest.fail("lock process did not become ready")
            time.sleep(0.01)

        store = JsonlTrajectoryStore(path)
        with pytest.raises(RuntimeError, match="active writer"):
            store.load()
        with pytest.raises(RuntimeError, match="active writer"):
            store.repair_tail()

        release.touch()
        stdout, stderr = process.communicate(timeout=10)
        assert process.returncode == 0, f"{stdout}\n{stderr}"
        assert store.load() == original
        assert store.repair_tail() is False
    finally:
        if process.poll() is None:
            release.touch()
            process.terminate()
            process.wait(timeout=10)


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits are not portable")
def test_store_fails_closed_when_an_existing_lock_is_unreadable(tmp_path) -> None:
    async def scenario() -> None:
        path = tmp_path / "unreadable-lock.jsonl"
        store = JsonlTrajectoryStore(path)
        await Experiment(
            experiment_id="unreadable-lock",
            version="1",
            trials={
                "candidate": (
                    _capital_trial(trial_id="unreadable-lock", output="Paris"),
                ),
            },
        ).run(store)
        lock_path = path.with_name(f"{path.name}.lock")
        lock_path.chmod(0)
        try:
            with pytest.raises(PermissionError):
                store.load()
        finally:
            lock_path.chmod(0o600)

    asyncio.run(scenario())


def test_store_rejects_duplicate_json_object_keys(tmp_path) -> None:
    async def scenario() -> None:
        path = tmp_path / "duplicate-key.jsonl"
        store = JsonlTrajectoryStore(path)
        await Experiment(
            experiment_id="duplicate-key",
            version="1",
            baseline="baseline",
            trials={
                "baseline": (_capital_trial(trial_id="duplicate-key", output="Paris"),),
            },
        ).run(store)
        lines = path.read_bytes().splitlines(keepends=True)
        lines[0] = b'{"record_type":"experiment.plan",' + lines[0][1:]
        path.write_bytes(b"".join(lines))

        with pytest.raises(ValueError, match="duplicate JSON object key"):
            store.load()

    asyncio.run(scenario())


def test_store_rejects_noncanonical_number_spelling_even_when_value_is_equal(
    tmp_path,
) -> None:
    async def scenario() -> None:
        path = tmp_path / "noncanonical-number.jsonl"
        store = JsonlTrajectoryStore(path)
        await Experiment(
            experiment_id="noncanonical-number",
            version="1",
            baseline="baseline",
            trials={
                "baseline": (
                    _capital_trial(trial_id="noncanonical", output="Lyon"),
                ),
            },
        ).run(store)
        content = path.read_bytes()
        assert b'"score":0.0' in content
        path.write_bytes(content.replace(b'"score":0.0', b'"score":1e-999', 1))

        with pytest.raises(ValueError, match="not canonical JSON"):
            store.load()

    asyncio.run(scenario())


def test_store_rejects_bool_entry_sequence_even_with_a_matching_digest(tmp_path) -> None:
    async def scenario() -> None:
        path = tmp_path / "bool-sequence.jsonl"
        store = JsonlTrajectoryStore(path)
        await Experiment(
            experiment_id="bool-sequence",
            version="1",
            baseline="baseline",
            trials={
                "baseline": (_capital_trial(trial_id="bool-sequence", output="Paris"),),
            },
        ).run(store)
        manifest = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
        manifest["entry_sequence"] = False
        manifest.pop("entry_digest")
        encoded_payload = json.dumps(
            manifest,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        manifest["entry_digest"] = (
            f"sha256:{hashlib.sha256(encoded_payload).hexdigest()}"
        )
        encoded_manifest = json.dumps(
            manifest,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        path.write_bytes(encoded_manifest + b"\n")

        with pytest.raises(ValueError, match="entry chain"):
            store.load()

    asyncio.run(scenario())


def test_experiment_persists_cancelled_trial_before_propagating_cancellation(
    tmp_path,
) -> None:
    class BlockingAgent:
        name = "cancelled-experiment-agent"
        version = "1"
        configuration: Mapping[str, object] = {}

        def __init__(self, started: asyncio.Event) -> None:
            self.started = started

        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            self.started.set()
            await asyncio.Event().wait()
            raise AssertionError("unreachable")

    async def scenario() -> None:
        path = tmp_path / "cancelled-experiment.jsonl"
        started = asyncio.Event()
        trial = Trial(
            task=Task(id="cancelled-experiment", input=None),
            agent=BlockingAgent(started),
            environment=LookupEnvironment(
                {},
                name="cancelled-experiment-environment",
                version="1",
            ),
            evaluator=ExactEvaluator(None, version="1"),
            config=TrialConfig(trial_id="cancelled-experiment-trial", max_actions=1),
        )
        running = asyncio.create_task(
            Experiment(
                experiment_id="cancelled-experiment",
                version="1",
                baseline=None,
                trials={"candidate": (trial,)},
            ).run(JsonlTrajectoryStore(path))
        )
        await started.wait()
        running.cancel()

        with pytest.raises(asyncio.CancelledError):
            await running

        stored = JsonlTrajectoryStore(path).load()
        assert stored is not None
        assert stored.complete is True
        assert stored.started_trial_ids == {"candidate": ()}
        assert stored.results["candidate"][0].status is TrialStatus.CANCELLED
        assert replay(stored.results["candidate"][0].trajectory).status is TrialStatus.CANCELLED

    asyncio.run(scenario())


def test_cancellation_remains_primary_when_terminal_commit_fails(tmp_path) -> None:
    class FailCommitStore(JsonlTrajectoryStore):
        fail_commits = True

        def _append(self, payload: Mapping[str, object]) -> None:
            if self.fail_commits and payload.get("record_type") == "trajectory.committed":
                raise OSError("simulated cancellation commit failure")
            super()._append(payload)

    class BlockingAgent:
        name = "cancel-commit-agent"
        version = "1"
        configuration: Mapping[str, object] = {}

        def __init__(self, started: asyncio.Event) -> None:
            self.started = started
            self.calls = 0

        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            self.calls += 1
            self.started.set()
            await asyncio.Event().wait()
            raise AssertionError("unreachable")

    async def scenario() -> None:
        path = tmp_path / "cancel-commit-failure.jsonl"
        started = asyncio.Event()
        agent = BlockingAgent(started)
        trial = Trial(
            task=Task(id="cancel-commit-failure", input=None),
            agent=agent,
            environment=LookupEnvironment(
                {},
                name="cancel-commit-environment",
                version="1",
            ),
            evaluator=ExactEvaluator(None, version="1"),
            config=TrialConfig(trial_id="cancel-commit-failure", max_actions=1),
        )
        experiment = Experiment(
            experiment_id="cancel-commit-failure",
            version="1",
            trials={"candidate": (trial,)},
        )
        store = FailCommitStore(path)
        running = asyncio.create_task(experiment.run(store))
        await started.wait()
        running.cancel()

        with pytest.raises(asyncio.CancelledError) as cancelled:
            await running
        assert any(
            "simulated cancellation commit failure" in note
            for note in getattr(cancelled.value, "__notes__", ())
        )
        assert agent.calls == 1
        interrupted = store.load()
        assert interrupted is not None
        assert interrupted.started_trial_ids == {
            "candidate": ("cancel-commit-failure",),
        }

        store.fail_commits = False
        recovered = await experiment.run(store)
        assert recovered.complete is True
        assert recovered.results["candidate"][0].status is TrialStatus.CANCELLED
        assert agent.calls == 1

    asyncio.run(scenario())


def test_cancellation_remains_primary_when_writer_unlock_fails(
    tmp_path,
    monkeypatch,
) -> None:
    class BlockingAgent:
        name = "cancel-unlock-agent"
        version = "1"
        configuration: Mapping[str, object] = {}

        def __init__(self, started: asyncio.Event) -> None:
            self.started = started

        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            self.started.set()
            await asyncio.Event().wait()
            raise AssertionError("unreachable")

    async def scenario() -> None:
        path = tmp_path / "cancel-unlock.jsonl"
        started = asyncio.Event()
        experiment = Experiment(
            experiment_id="cancel-unlock",
            version="1",
            trials={
                "candidate": (
                    Trial(
                        task=Task(id="cancel-unlock", input=None),
                        agent=BlockingAgent(started),
                        environment=LookupEnvironment(
                            {},
                            name="cancel-unlock-environment",
                            version="1",
                        ),
                        evaluator=ExactEvaluator(None, version="1"),
                        config=TrialConfig(trial_id="cancel-unlock", max_actions=1),
                    ),
                ),
            },
        )
        running = asyncio.create_task(experiment.run(JsonlTrajectoryStore(path)))
        await started.wait()
        real_unlock = jsonl_module._unlock_stream

        def fail_unlock(stream: object) -> None:
            del stream
            raise OSError("simulated unlock failure")

        monkeypatch.setattr(jsonl_module, "_unlock_stream", fail_unlock)
        running.cancel()
        with pytest.raises(asyncio.CancelledError) as cancelled:
            await running
        assert any(
            "simulated unlock failure" in note
            for note in getattr(cancelled.value, "__notes__", ())
        )

        monkeypatch.setattr(jsonl_module, "_unlock_stream", real_unlock)
        stored = JsonlTrajectoryStore(path).load()
        assert stored is not None
        assert stored.complete is True
        assert stored.results["candidate"][0].status is TrialStatus.CANCELLED

    asyncio.run(scenario())


def test_terminal_commit_failure_can_be_finalized_without_reexecuting(tmp_path) -> None:
    class FailOnceCommitStore(JsonlTrajectoryStore):
        fail_next_commit = True

        def _append(self, payload: Mapping[str, object]) -> None:
            if (
                self.fail_next_commit
                and payload.get("record_type") == "trajectory.committed"
            ):
                self.fail_next_commit = False
                raise OSError("simulated terminal commit failure")
            super()._append(payload)

    class CountingAgent:
        name = "retry-agent"
        version = "1"
        configuration: Mapping[str, object] = {}

        def __init__(self) -> None:
            self.calls = 0

        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            self.calls += 1
            return Action.finish("Paris")

    async def scenario() -> None:
        path = tmp_path / "retry-terminal-commit.jsonl"
        agent = CountingAgent()
        experiment = Experiment(
            experiment_id="retry-terminal-commit",
            version="1",
            baseline="baseline",
            trials={
                "baseline": (
                    Trial(
                        task=Task(id="retry-terminal-commit", input=None),
                        agent=agent,
                        environment=LookupEnvironment(
                            {},
                            name="retry-environment",
                            version="1",
                        ),
                        evaluator=ExactEvaluator("Paris", version="1"),
                        config=TrialConfig(
                            trial_id="retry-terminal-commit",
                            max_actions=1,
                        ),
                    ),
                ),
            },
        )
        store = FailOnceCommitStore(path)

        with pytest.raises(OSError, match="simulated terminal commit failure"):
            await experiment.run(store)
        assert agent.calls == 1
        interrupted = store.load()
        assert interrupted is not None
        assert interrupted.complete is False

        recovered = await experiment.run(store)
        assert recovered.complete is True
        assert agent.calls == 1

    asyncio.run(scenario())


def test_store_never_grafts_a_different_execution_onto_an_interrupted_start(
    tmp_path,
) -> None:
    class SimulatedProcessCrash(BaseException):
        pass

    class AttemptAgent:
        name = "attempt-agent"
        version = "1"
        configuration: Mapping[str, object] = {}

        def __init__(self, *, crash: bool) -> None:
            self.crash = crash
            self.calls = 0

        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            self.calls += 1
            if self.crash:
                raise SimulatedProcessCrash
            return Action.finish("Paris")

    def make_trial(agent: AttemptAgent) -> Trial:
        return Trial(
            task=Task(id="attempt-binding", input=None),
            agent=agent,
            environment=LookupEnvironment(
                {},
                name="attempt-environment",
                version="1",
            ),
            evaluator=ExactEvaluator("Paris", version="1"),
            config=TrialConfig(trial_id="attempt-slot", max_actions=1),
        )

    async def scenario() -> None:
        path = tmp_path / "attempt-binding.jsonl"
        with pytest.raises(SimulatedProcessCrash):
            await Experiment(
                experiment_id="attempt-binding",
                version="1",
                trials={"candidate": (make_trial(AttemptAgent(crash=True)),)},
            ).run(JsonlTrajectoryStore(path))

        external_agent = AttemptAgent(crash=False)
        external_trial = make_trial(external_agent)
        replacement = Experiment(
            experiment_id="attempt-binding",
            version="1",
            trials={"candidate": (external_trial,)},
        )
        external_result = await external_trial.run()
        assert external_result.status is TrialStatus.COMPLETED

        stored = await replacement.run(JsonlTrajectoryStore(path))
        assert stored.complete is False
        assert stored.results == {"candidate": ()}
        assert stored.started_trial_ids == {"candidate": ("attempt-slot",)}
        assert external_agent.calls == 1
        assert len(path.read_bytes().splitlines()) == 2

    asyncio.run(scenario())


def test_experiment_rejects_plan_drift_before_new_trial_effects(tmp_path) -> None:
    async def scenario() -> None:
        path = tmp_path / "plan-conflict.jsonl"
        await Experiment(
            experiment_id="plan-conflict",
            version="1",
            baseline="baseline",
            trials={
                "baseline": (_capital_trial(trial_id="same-id", output="Paris"),),
            },
        ).run(JsonlTrajectoryStore(path))
        original_bytes = path.read_bytes()

        changed = Trial(
            task=Task(id="changed-task", input={"question": "changed"}),
            agent=ScriptedAgent(
                [Action.finish("Paris")],
                name="same-id-agent",
                version="1",
            ),
            environment=LookupEnvironment(
                {},
                name="country-capitals",
                version="1",
            ),
            evaluator=ExactEvaluator("Paris", version="1"),
            config=TrialConfig(trial_id="same-id", seed=7, max_actions=1),
        )
        with pytest.raises(ValueError, match="different Experiment plan"):
            await Experiment(
                experiment_id="plan-conflict",
                version="1",
                baseline="baseline",
                trials={"baseline": (changed,)},
            ).run(JsonlTrajectoryStore(path))

        assert changed.trajectory.records == ()
        assert path.read_bytes() == original_bytes

    asyncio.run(scenario())


def test_store_binds_recomputed_trajectory_bytes_to_the_planned_provenance(
    tmp_path,
) -> None:
    def digest(value: object) -> str:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return f"sha256:{hashlib.sha256(encoded).hexdigest()}"

    async def scenario() -> None:
        path = tmp_path / "tampered-provenance.jsonl"
        store = JsonlTrajectoryStore(path)
        await Experiment(
            experiment_id="tampered-provenance",
            version="1",
            baseline="baseline",
            trials={
                "baseline": (_capital_trial(trial_id="tampered", output="Paris"),),
            },
        ).run(store)
        lines = path.read_text(encoding="utf-8").splitlines()
        committed = json.loads(lines[-1])
        committed["trajectory"]["task"]["input"]["question"] = "tampered"
        committed["trajectory_digest"] = digest(committed["trajectory"])
        digest_payload = dict(committed)
        digest_payload.pop("entry_digest")
        committed["entry_digest"] = digest(digest_payload)
        lines[-1] = json.dumps(
            committed,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        with pytest.raises(ValueError, match="provenance does not match"):
            store.load()

    asyncio.run(scenario())


def test_tail_repair_never_hides_a_malformed_complete_record(tmp_path) -> None:
    async def scenario() -> None:
        path = tmp_path / "bad-prefix.jsonl"
        store = JsonlTrajectoryStore(path)
        await Experiment(
            experiment_id="bad-prefix",
            version="1",
            baseline="baseline",
            trials={
                "baseline": (_capital_trial(trial_id="bad-prefix", output="Paris"),),
            },
        ).run(store)
        lines = path.read_bytes().splitlines(keepends=True)
        lines[1] = b"{malformed}\n"
        corrupted = b"".join(lines) + b'{"torn":'
        path.write_bytes(corrupted)

        with pytest.raises(ValueError, match=r"bad-prefix\.jsonl:2"):
            store.repair_tail()
        assert path.read_bytes() == corrupted

    asyncio.run(scenario())


def test_fsync_failure_stops_before_trial_effects_and_leaves_a_valid_prefix(
    tmp_path,
    monkeypatch,
) -> None:
    class CountingAgent:
        name = "fsync-agent"
        version = "1"
        configuration: Mapping[str, object] = {}

        def __init__(self) -> None:
            self.calls = 0

        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            self.calls += 1
            return Action.finish("Paris")

    async def scenario() -> None:
        path = tmp_path / "fsync-failure.jsonl"
        agent = CountingAgent()
        real_fsync = os.fsync
        fsync_calls = 0

        failure_call = 3 if os.name != "nt" else 2

        def fail_start_fsync(file_descriptor: int) -> None:
            nonlocal fsync_calls
            fsync_calls += 1
            if fsync_calls == failure_call:
                raise OSError("simulated fsync failure")
            real_fsync(file_descriptor)

        monkeypatch.setattr(os, "fsync", fail_start_fsync)
        with pytest.raises(OSError, match="simulated fsync failure"):
            await Experiment(
                experiment_id="fsync-failure",
                version="1",
                baseline="baseline",
                trials={
                    "baseline": (
                        Trial(
                            task=Task(id="fsync-failure", input=None),
                            agent=agent,
                            environment=LookupEnvironment(
                                {},
                                name="fsync-environment",
                                version="1",
                            ),
                            evaluator=ExactEvaluator("Paris", version="1"),
                            config=TrialConfig(
                                trial_id="fsync-failure-trial",
                                max_actions=1,
                            ),
                        ),
                    )
                },
            ).run(JsonlTrajectoryStore(path))

        assert agent.calls == 0
        stored = JsonlTrajectoryStore(path).load()
        assert stored is not None
        assert stored.complete is False
        assert stored.started_trial_ids == {
            "baseline": ("fsync-failure-trial",),
        }

    asyncio.run(scenario())


@pytest.mark.skipif(os.name == "nt", reason="directory fsync is POSIX-specific")
def test_retry_reconfirms_parent_directory_durability_before_effects(
    tmp_path,
    monkeypatch,
) -> None:
    sync_state = {"directory_calls": 0}

    class CountingAgent:
        name = "directory-fsync-agent"
        version = "1"
        configuration: Mapping[str, object] = {}

        def __init__(self) -> None:
            self.calls = 0

        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            assert sync_state["directory_calls"] >= 1
            self.calls += 1
            return Action.finish("Paris")

    async def scenario() -> None:
        path = tmp_path / "directory-fsync-retry.jsonl"
        agent = CountingAgent()
        experiment = Experiment(
            experiment_id="directory-fsync-retry",
            version="1",
            trials={
                "candidate": (
                    Trial(
                        task=Task(id="directory-fsync-retry", input=None),
                        agent=agent,
                        environment=LookupEnvironment(
                            {},
                            name="directory-fsync-environment",
                            version="1",
                        ),
                        evaluator=ExactEvaluator("Paris", version="1"),
                        config=TrialConfig(
                            trial_id="directory-fsync-retry",
                            max_actions=1,
                        ),
                    ),
                ),
            },
        )
        real_fsync = os.fsync
        failed = False

        def fail_first_directory_fsync(file_descriptor: int) -> None:
            nonlocal failed
            if stat.S_ISDIR(os.fstat(file_descriptor).st_mode) and not failed:
                failed = True
                raise OSError("simulated directory fsync failure")
            real_fsync(file_descriptor)

        monkeypatch.setattr(os, "fsync", fail_first_directory_fsync)
        with pytest.raises(OSError, match="simulated directory fsync failure"):
            await experiment.run(JsonlTrajectoryStore(path))
        assert agent.calls == 0
        assert path.exists()

        def track_directory_fsync(file_descriptor: int) -> None:
            if stat.S_ISDIR(os.fstat(file_descriptor).st_mode):
                sync_state["directory_calls"] += 1
            real_fsync(file_descriptor)

        monkeypatch.setattr(os, "fsync", track_directory_fsync)
        recovered = await experiment.run(JsonlTrajectoryStore(path))
        assert recovered.complete is True
        assert agent.calls == 1
        assert sync_state["directory_calls"] >= 2

    asyncio.run(scenario())


@pytest.mark.skipif(os.name == "nt", reason="directory fsync is POSIX-specific")
def test_retry_flushes_a_visible_terminal_record_before_returning(
    tmp_path,
    monkeypatch,
) -> None:
    class CountingAgent:
        name = "terminal-fsync-agent"
        version = "1"
        configuration: Mapping[str, object] = {}

        def __init__(self) -> None:
            self.calls = 0

        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            self.calls += 1
            return Action.finish("Paris")

    async def scenario() -> None:
        path = tmp_path / "terminal-fsync-retry.jsonl"
        agent = CountingAgent()
        experiment = Experiment(
            experiment_id="terminal-fsync-retry",
            version="1",
            trials={
                "candidate": (
                    Trial(
                        task=Task(id="terminal-fsync-retry", input=None),
                        agent=agent,
                        environment=LookupEnvironment(
                            {},
                            name="terminal-fsync-environment",
                            version="1",
                        ),
                        evaluator=ExactEvaluator("Paris", version="1"),
                        config=TrialConfig(
                            trial_id="terminal-fsync-retry",
                            max_actions=1,
                        ),
                    ),
                ),
            },
        )
        real_fsync = os.fsync
        fsync_calls = 0

        def fail_terminal_file_fsync(file_descriptor: int) -> None:
            nonlocal fsync_calls
            fsync_calls += 1
            if fsync_calls == 5:
                raise OSError("simulated terminal fsync failure")
            real_fsync(file_descriptor)

        monkeypatch.setattr(os, "fsync", fail_terminal_file_fsync)
        with pytest.raises(OSError, match="simulated terminal fsync failure"):
            await experiment.run(JsonlTrajectoryStore(path))
        assert agent.calls == 1
        assert len(path.read_bytes().splitlines()) == 3

        sync_state = {"file": 0, "directory": 0}

        def track_retry_fsync(file_descriptor: int) -> None:
            if stat.S_ISDIR(os.fstat(file_descriptor).st_mode):
                sync_state["directory"] += 1
            else:
                sync_state["file"] += 1
            real_fsync(file_descriptor)

        monkeypatch.setattr(os, "fsync", track_retry_fsync)
        recovered = await experiment.run(JsonlTrajectoryStore(path))
        assert recovered.complete is True
        assert agent.calls == 1
        assert sync_state == {"file": 1, "directory": 1}

    asyncio.run(scenario())


def test_oversized_manifest_is_rejected_before_store_creation_or_trial_effects(
    tmp_path,
) -> None:
    async def scenario() -> None:
        path = tmp_path / "oversized.jsonl"
        trial = Trial(
            task=Task(id="oversized", input={"value": "x" * (16 * 1024 * 1024)}),
            agent=ScriptedAgent(
                [Action.finish("done")],
                name="oversized-agent",
                version="1",
            ),
            environment=LookupEnvironment(
                {},
                name="oversized-environment",
                version="1",
            ),
            evaluator=ExactEvaluator("done", version="1"),
            config=TrialConfig(trial_id="oversized-trial", max_actions=1),
        )

        with pytest.raises(ValueError, match="record is too large"):
            await Experiment(
                experiment_id="oversized",
                version="1",
                baseline=None,
                trials={"candidate": (trial,)},
            ).run(JsonlTrajectoryStore(path))

        assert path.exists() is False
        assert trial.trajectory.records == ()

    asyncio.run(scenario())


def test_experiment_plan_rejects_a_trial_spec_with_invalid_configuration_hash() -> None:
    spec = _capital_trial(trial_id="invalid-spec", output="Paris").trajectory

    with pytest.raises(ValueError, match="configuration hash"):
        ExperimentPlan(
            experiment_id="invalid-spec",
            version="1",
            baseline="baseline",
            trial_specs={
                "baseline": (replace(spec, config_hash="sha256:invalid"),),
            },
        )


def test_experiment_result_rejects_a_result_outside_its_planned_provenance() -> None:
    async def scenario() -> None:
        trial = _capital_trial(trial_id="forged-result", output="Paris")
        plan = Experiment(
            experiment_id="forged-result",
            version="1",
            baseline="baseline",
            trials={"baseline": (trial,)},
        ).plan
        result = await trial.run()
        forged_trajectory = replace(
            result.trajectory,
            task=Task(id="different-task", input=None),
        )
        forged_result = replace(result, trajectory=forged_trajectory)

        with pytest.raises(ValueError, match="planned provenance"):
            ExperimentResult(
                plan=plan,
                results={"baseline": (forged_result,)},
                started_trial_ids={"baseline": ()},
            )

    asyncio.run(scenario())


def test_experiment_rejects_live_declaration_drift_before_starting_trial(
    tmp_path,
) -> None:
    class MutableAgent:
        name = "mutable-agent"
        version = "1"
        configuration: Mapping[str, object] = {"policy": "fixed"}

        def __init__(self) -> None:
            self.calls = 0

        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            self.calls += 1
            return Action.finish("Paris")

    async def scenario() -> None:
        path = tmp_path / "declaration-drift.jsonl"
        agent = MutableAgent()
        trial = Trial(
            task=Task(id="declaration-drift", input=None),
            agent=agent,
            environment=LookupEnvironment(
                {},
                name="declaration-drift-environment",
                version="1",
            ),
            evaluator=ExactEvaluator("Paris", version="1"),
            config=TrialConfig(trial_id="declaration-drift-trial", max_actions=1),
        )
        experiment = Experiment(
            experiment_id="declaration-drift",
            version="1",
            baseline="baseline",
            trials={"baseline": (trial,)},
        )
        agent.version = "2"

        with pytest.raises(ValueError, match="declarations drifted"):
            await experiment.run(JsonlTrajectoryStore(path))

        assert agent.calls == 0
        assert trial.trajectory.records == ()
        stored = JsonlTrajectoryStore(path).load()
        assert stored is not None
        assert stored.results == {"baseline": ()}
        assert stored.started_trial_ids == {"baseline": ()}

    asyncio.run(scenario())


def test_experiment_rechecks_later_slot_after_earlier_trial_effects(tmp_path) -> None:
    class LaterAgent:
        name = "later-agent"
        version = "1"
        configuration: Mapping[str, object] = {}

        def __init__(self) -> None:
            self.calls = 0

        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            self.calls += 1
            return Action.finish("Paris")

    class MutatingAgent:
        name = "mutating-agent"
        version = "1"
        configuration: Mapping[str, object] = {}

        def __init__(self, later: LaterAgent) -> None:
            self.later = later

        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            self.later.version = "2"
            return Action.finish("Paris")

    async def scenario() -> None:
        path = tmp_path / "between-slot-drift.jsonl"
        later_agent = LaterAgent()
        first = Trial(
            task=Task(id="mutate-later", input=None),
            agent=MutatingAgent(later_agent),
            environment=LookupEnvironment({}, name="first-environment", version="1"),
            evaluator=ExactEvaluator("Paris", version="1"),
            config=TrialConfig(trial_id="mutate-later", max_actions=1),
        )
        later = Trial(
            task=Task(id="later", input=None),
            agent=later_agent,
            environment=LookupEnvironment({}, name="later-environment", version="1"),
            evaluator=ExactEvaluator("Paris", version="1"),
            config=TrialConfig(trial_id="later", max_actions=1),
        )

        with pytest.raises(ValueError, match="declarations drifted"):
            await Experiment(
                experiment_id="between-slot-drift",
                version="1",
                baseline="baseline",
                trials={"baseline": (first,), "candidate": (later,)},
            ).run(JsonlTrajectoryStore(path))

        assert later_agent.calls == 0
        assert later.trajectory.records == ()
        stored = JsonlTrajectoryStore(path).load()
        assert stored is not None
        assert stored.complete is False
        assert len(stored.results["baseline"]) == 1
        assert stored.results["candidate"] == ()
        assert stored.started_trial_ids == {"baseline": (), "candidate": ()}

    asyncio.run(scenario())


def test_experiment_rechecks_declarations_before_terminal_commit(tmp_path) -> None:
    class SelfMutatingAgent:
        name = "self-mutating-agent"
        version = "1"
        configuration: Mapping[str, object] = {}

        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            self.version = "2"
            return Action.finish("Paris")

    async def scenario() -> None:
        path = tmp_path / "in-trial-drift.jsonl"
        agent = SelfMutatingAgent()
        experiment = Experiment(
            experiment_id="in-trial-drift",
            version="1",
            trials={
                "candidate": (
                    Trial(
                        task=Task(id="in-trial-drift", input=None),
                        agent=agent,
                        environment=LookupEnvironment(
                            {},
                            name="in-trial-environment",
                            version="1",
                        ),
                        evaluator=ExactEvaluator("Paris", version="1"),
                        config=TrialConfig(trial_id="in-trial-drift", max_actions=1),
                    ),
                ),
            },
        )

        with pytest.raises(ValueError, match="declarations drifted"):
            await experiment.run(JsonlTrajectoryStore(path))

        stored = JsonlTrajectoryStore(path).load()
        assert stored is not None
        assert stored.complete is False
        assert stored.results == {"candidate": ()}
        assert stored.started_trial_ids == {"candidate": ("in-trial-drift",)}

        agent.version = "1"
        still_interrupted = await experiment.run(JsonlTrajectoryStore(path))
        assert still_interrupted.complete is False
        assert still_interrupted.results == {"candidate": ()}

    asyncio.run(scenario())


def test_experiment_preflights_every_pending_trial_before_any_start(tmp_path) -> None:
    async def scenario() -> None:
        path = tmp_path / "batch-preflight.jsonl"
        first = _capital_trial(trial_id="batch-first", output="Paris")
        already_run = _capital_trial(trial_id="batch-second", output="Paris")
        experiment = Experiment(
            experiment_id="batch-preflight",
            version="1",
            baseline="baseline",
            trials={"baseline": (first, already_run)},
        )
        await already_run.run()

        with pytest.raises(RuntimeError, match="already started"):
            await experiment.run(JsonlTrajectoryStore(path))

        assert first.trajectory.records == ()
        stored = JsonlTrajectoryStore(path).load()
        assert stored is not None
        assert stored.results == {"baseline": ()}
        assert stored.started_trial_ids == {"baseline": ()}
        assert len(path.read_bytes().splitlines()) == 1

    asyncio.run(scenario())


def test_completed_experiment_object_cannot_poison_a_new_store(tmp_path) -> None:
    async def scenario() -> None:
        trial = _capital_trial(trial_id="one-shot", output="Paris")
        experiment = Experiment(
            experiment_id="one-shot",
            version="1",
            baseline="baseline",
            trials={"baseline": (trial,)},
        )
        await experiment.run(JsonlTrajectoryStore(tmp_path / "first.jsonl"))

        second_path = tmp_path / "second.jsonl"
        with pytest.raises(RuntimeError, match="already started"):
            await experiment.run(JsonlTrajectoryStore(second_path))

        stored = JsonlTrajectoryStore(second_path).load()
        assert stored is not None
        assert stored.results == {"baseline": ()}
        assert stored.started_trial_ids == {"baseline": ()}
        assert len(second_path.read_bytes().splitlines()) == 1

    asyncio.run(scenario())


@pytest.mark.skipif(os.name == "nt", reason="POSIX file modes are not portable")
def test_store_creates_private_artifacts_and_loads_a_read_only_copy(tmp_path) -> None:
    async def scenario() -> None:
        path = tmp_path / "private.jsonl"
        original = await Experiment(
            experiment_id="private-artifact",
            version="1",
            baseline="baseline",
            trials={
                "baseline": (_capital_trial(trial_id="private", output="Paris"),),
            },
        ).run(JsonlTrajectoryStore(path))
        assert stat.S_IMODE(path.stat().st_mode) & 0o077 == 0

        archive = tmp_path / "archive"
        archive.mkdir()
        copy = archive / "private.jsonl"
        copy.write_bytes(path.read_bytes())
        copy.chmod(0o400)
        archive.chmod(0o500)
        try:
            assert JsonlTrajectoryStore(copy).load() == original
        finally:
            archive.chmod(0o700)
            copy.chmod(0o600)

    asyncio.run(scenario())


def test_loading_a_missing_store_has_no_filesystem_side_effect(tmp_path) -> None:
    path = tmp_path / "missing-parent" / "missing.jsonl"

    assert JsonlTrajectoryStore(path).load() is None
    assert path.parent.exists() is False
