from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import Mapping
from dataclasses import replace

import pytest

import iamai
import iamai.harness as harness
from iamai.harness import (
    Action,
    Evaluation,
    ExactEvaluator,
    LookupEnvironment,
    Observation,
    ScriptedAgent,
    Task,
    Trial,
    TrialConfig,
    TrialResult,
    TrialStatus,
    Trajectory,
    TrajectoryRecord,
    replay,
)


def test_provisional_harness_is_not_reexported_from_stable_top_level_api() -> None:
    harness_names = set(harness.__all__)

    assert harness_names.isdisjoint(iamai.__all__)
    for name in harness_names:
        assert not hasattr(iamai, name)


def _capital_trial(*, final_output: str = "Paris", max_actions: int = 2) -> Trial:
    return Trial(
        task=Task(
            id="capital-of-france",
            input={"question": "What is the capital of France?"},
        ),
        agent=ScriptedAgent(
            [
                Action.invoke("lookup", {"key": "france"}),
                Action.finish(final_output),
            ],
            name="scripted-capital-agent",
            version="1",
        ),
        environment=LookupEnvironment(
            {"france": "Paris"},
            name="country-capitals",
            version="1",
        ),
        evaluator=ExactEvaluator("Paris", version="1"),
        config=TrialConfig(
            trial_id="trial-capital-france",
            seed=7,
            max_actions=max_actions,
        ),
    )


def test_scripted_agent_completes_headless_lookup_trial() -> None:
    async def scenario() -> None:
        result = await _capital_trial().run()

        assert result.status is TrialStatus.COMPLETED
        assert result.final_output == "Paris"
        assert result.evaluation is not None
        assert result.evaluation.passed is True
        assert result.evaluation.score == 1.0

    asyncio.run(scenario())


def test_wrong_final_answer_is_completed_but_does_not_pass_evaluation() -> None:
    async def scenario() -> None:
        result = await _capital_trial(final_output="Lyon").run()

        assert result.status is TrialStatus.COMPLETED
        assert result.final_output == "Lyon"
        assert result.evaluation is not None
        assert result.evaluation.passed is False
        assert result.evaluation.score == 0.0

    asyncio.run(scenario())


def test_configuration_hash_tracks_declared_harness_configuration_only() -> None:
    def configured_trial(*, trial_id: str, task_id: str, seed: int) -> Trial:
        return Trial(
            task=Task(id=task_id, input={"seed-specific": seed}),
            agent=ScriptedAgent(
                [Action.finish("done")],
                name="configuration-agent",
                version="1",
            ),
            environment=LookupEnvironment(
                {},
                name="configuration-environment",
                version="1",
            ),
            evaluator=ExactEvaluator("done", version="1"),
            config=TrialConfig(
                trial_id=trial_id,
                seed=seed,
                max_actions=1,
            ),
        )

    first = configured_trial(trial_id="first", task_id="task-a", seed=1)
    second = configured_trial(trial_id="second", task_id="task-b", seed=2)

    assert first.trajectory.config_hash == second.trajectory.config_hash
    assert first.trajectory.trial_id != second.trajectory.trial_id
    assert first.trajectory.seed != second.trajectory.seed


@pytest.mark.parametrize("max_actions", [True, 1.5, "1"])
def test_trial_config_rejects_non_integer_action_budgets(max_actions: object) -> None:
    with pytest.raises(TypeError, match="max_actions must be an integer"):
        TrialConfig(trial_id="invalid-budget", max_actions=max_actions)  # type: ignore[arg-type]


def test_scripted_agent_has_no_hidden_cross_trial_cursor() -> None:
    async def scenario() -> None:
        agent = ScriptedAgent(
            [Action.finish("done")],
            name="reusable-script",
            version="1",
        )

        def trial(trial_id: str) -> Trial:
            return Trial(
                task=Task(id="reusable-script-task", input=None),
                agent=agent,
                environment=LookupEnvironment(
                    {},
                    name="reusable-script-environment",
                    version="1",
                ),
                evaluator=ExactEvaluator("done", version="1"),
                config=TrialConfig(trial_id=trial_id, max_actions=1),
            )

        first = await trial("reusable-script-first").run()
        second = await trial("reusable-script-second").run()

        assert first.status is TrialStatus.COMPLETED
        assert second.status is TrialStatus.COMPLETED
        assert first.trajectory.config_hash == second.trajectory.config_hash

    asyncio.run(scenario())


def test_trial_execution_bindings_cannot_drift_from_trajectory_header() -> None:
    async def scenario() -> None:
        trial = _capital_trial()

        with pytest.raises(AttributeError):
            setattr(
                trial,
                "config",
                TrialConfig(trial_id="replacement", max_actions=1),
            )
        with pytest.raises(AttributeError):
            setattr(
                trial,
                "agent",
                ScriptedAgent(
                    [Action.finish("replacement")],
                    name="replacement-agent",
                    version="1",
                ),
            )

        result = await trial.run()

        assert result.trial_id == result.trajectory.trial_id
        assert replay(result.trajectory).status is TrialStatus.COMPLETED

    asyncio.run(scenario())


def test_builtin_evaluator_cannot_drift_from_declared_configuration() -> None:
    async def scenario() -> None:
        evaluator = ExactEvaluator("Paris", version="1")
        trial = Trial(
            task=Task(id="stable-evaluator", input=None),
            agent=ScriptedAgent(
                [Action.finish("Paris")],
                name="stable-evaluator-agent",
                version="1",
            ),
            environment=LookupEnvironment(
                {},
                name="stable-evaluator-environment",
                version="1",
            ),
            evaluator=evaluator,
            config=TrialConfig(trial_id="trial-stable-evaluator", max_actions=1),
        )

        with pytest.raises(AttributeError):
            setattr(evaluator, "expected", "changed")
        with pytest.raises(AttributeError):
            setattr(evaluator, "version", "changed")
        with pytest.raises(AttributeError):
            setattr(evaluator, "configuration", {})

        result = await trial.run()
        assert result.evaluation is not None
        assert result.evaluation.passed is True

    asyncio.run(scenario())


def test_committed_trajectory_does_not_alias_mutable_task_input() -> None:
    async def scenario() -> None:
        source = {"question": {"parts": ["capital", "france"]}}
        task = Task(id="immutable-task", input=source)
        source["question"]["parts"].append("mutated")
        result = await Trial(
            task=task,
            agent=ScriptedAgent(
                [Action.finish("Paris")],
                name="immutable-agent",
                version="1",
            ),
            environment=LookupEnvironment(
                {},
                name="immutable-environment",
                version="1",
            ),
            evaluator=ExactEvaluator("Paris", version="1"),
            config=TrialConfig(trial_id="trial-immutable", max_actions=1),
        ).run()

        question = result.trajectory.task.input
        assert isinstance(question, Mapping)
        assert question["question"]["parts"] == ("capital", "france")
        with pytest.raises(TypeError):
            result.trajectory.records[-1].payload["status"] = "changed"  # type: ignore[index]

    asyncio.run(scenario())


def test_public_trajectory_constructors_freeze_nested_mappings() -> None:
    payload = {"nested": {"values": [1]}}
    configuration = {"adapter": {"name": "original"}}
    record = TrajectoryRecord(sequence=0, kind="trial.started", payload=payload)
    trajectory = Trajectory(
        format_version="1",
        trial_id="public-constructor",
        task=Task(id="public-constructor-task", input=None),
        seed=0,
        configuration=configuration,
        config_hash="not-used-by-this-test",
        records=(record,),
    )

    payload["nested"]["values"].append(2)
    configuration["adapter"]["name"] = "mutated"

    assert record.payload["nested"]["values"] == (1,)
    assert trajectory.configuration["adapter"]["name"] == "original"
    with pytest.raises(TypeError):
        record.payload["new"] = "value"  # type: ignore[index]


def test_public_trial_result_freezes_direct_final_output() -> None:
    async def scenario() -> None:
        original = await _capital_trial().run()
        output = {"parts": ["Paris"]}
        direct = TrialResult(
            trial_id=original.trial_id,
            status=original.status,
            final_output=output,
            evaluation=original.evaluation,
            trajectory=original.trajectory,
        )

        output["parts"].append("mutated")

        assert direct.final_output["parts"] == ("Paris",)

    asyncio.run(scenario())


def test_cancellation_records_terminal_state_and_propagates() -> None:
    class BlockingAgent:
        name = "blocking-agent"
        version = "1"
        configuration: dict[str, object] = {}

        def __init__(self, started: asyncio.Event) -> None:
            self.started = started

        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            self.started.set()
            await asyncio.Event().wait()
            raise AssertionError("unreachable")

    async def scenario() -> None:
        started = asyncio.Event()
        trial = Trial(
            task=Task(id="cancelled-task", input={"question": "wait"}),
            agent=BlockingAgent(started),
            environment=LookupEnvironment(
                {"unused": "unused"},
                name="cancel-environment",
                version="1",
            ),
            evaluator=ExactEvaluator(None, version="1"),
            config=TrialConfig(trial_id="trial-cancelled", max_actions=1),
        )

        running = asyncio.create_task(trial.run())
        await started.wait()
        running.cancel()

        with pytest.raises(asyncio.CancelledError):
            await running

        assert [record.kind for record in trial.trajectory.records] == [
            "trial.started",
            "environment.reset",
            "trial.cancelled",
            "trial.terminated",
        ]
        assert trial.trajectory.records[-1].payload == {
            "status": "cancelled",
            "phase": "agent",
            "operation": "agent.decide",
        }

        replayed = replay(trial.trajectory)
        assert replayed.status is TrialStatus.CANCELLED
        assert replayed.evaluation is None
        assert replayed.failure is None

    asyncio.run(scenario())


def test_environment_failure_preserves_the_committed_action() -> None:
    class FailingEnvironment:
        name = "failing-environment"
        version = "1"
        configuration: dict[str, object] = {}

        async def reset(self, task: Task, *, seed: int) -> Observation:
            del seed
            return Observation(task.input)

        async def step(self, *args: object, **kwargs: object) -> None:
            del args, kwargs
            raise OSError("world unavailable")

    async def scenario() -> None:
        trial = Trial(
            task=Task(id="failing-world", input={"question": "act"}),
            agent=ScriptedAgent(
                [Action.invoke("act")],
                name="one-action-agent",
                version="1",
            ),
            environment=FailingEnvironment(),
            evaluator=ExactEvaluator(None, version="1"),
            config=TrialConfig(trial_id="trial-environment-failure", max_actions=1),
        )

        result = await trial.run()

        assert result.status is TrialStatus.FAILED
        assert result.failure is not None
        assert result.failure.phase == "environment"
        assert result.failure.exception_type == "OSError"
        assert result.failure.message == "world unavailable"
        assert [record.kind for record in result.trajectory.records] == [
            "trial.started",
            "environment.reset",
            "agent.action",
            "trial.failure",
            "trial.terminated",
        ]

    asyncio.run(scenario())


def test_trial_records_a_replayable_causal_trajectory() -> None:
    async def scenario() -> None:
        result = await _capital_trial().run()

        trajectory = result.trajectory
        assert trajectory.trial_id == "trial-capital-france"
        assert trajectory.task.id == "capital-of-france"
        assert trajectory.seed == 7
        assert trajectory.config_hash.startswith("sha256:")
        assert [record.sequence for record in trajectory.records] == list(range(8))
        assert [record.kind for record in trajectory.records] == [
            "trial.started",
            "environment.reset",
            "agent.action",
            "environment.transition",
            "agent.action",
            "environment.transition",
            "evaluation.recorded",
            "trial.terminated",
        ]
        assert trajectory.records[4].payload["name"] == "final"
        assert trajectory.records[5].payload["terminated"] is True

    asyncio.run(scenario())


def test_trial_records_budget_exhaustion_as_an_evaluated_result() -> None:
    async def scenario() -> None:
        result = await _capital_trial(max_actions=1).run()

        assert result.status is TrialStatus.BUDGET_EXHAUSTED
        assert result.final_output is None
        assert result.evaluation is not None
        assert result.evaluation.passed is False
        assert [record.kind for record in result.trajectory.records] == [
            "trial.started",
            "environment.reset",
            "agent.action",
            "environment.transition",
            "budget.exhausted",
            "evaluation.recorded",
            "trial.terminated",
        ]
        assert result.trajectory.records[-1].payload["status"] == "budget_exhausted"

    asyncio.run(scenario())


def test_budget_exhaustion_cannot_exact_match_an_expected_null_output() -> None:
    async def scenario() -> None:
        result = await Trial(
            task=Task(id="null-output", input=None),
            agent=ScriptedAgent(
                [Action.invoke("lookup", {"key": "unused"})],
                name="null-output-agent",
                version="1",
            ),
            environment=LookupEnvironment(
                {"unused": None},
                name="null-output-environment",
                version="1",
            ),
            evaluator=ExactEvaluator(None, version="1"),
            config=TrialConfig(trial_id="trial-null-output", max_actions=1),
        ).run()

        assert result.status is TrialStatus.BUDGET_EXHAUSTED
        assert result.evaluation is not None
        assert result.evaluation.passed is False
        assert result.evaluation.score == 0.0

    asyncio.run(scenario())


def test_replay_reconstructs_result_without_agent_or_environment() -> None:
    async def scenario() -> None:
        original = await _capital_trial().run()

        replayed = replay(original.trajectory)

        assert replayed.status is original.status
        assert replayed.final_output == original.final_output
        assert replayed.evaluation == original.evaluation
        assert replayed.trajectory == original.trajectory

    asyncio.run(scenario())


def test_replay_rejects_evaluation_before_the_terminating_transition() -> None:
    async def scenario() -> None:
        original = await _capital_trial().run()
        records = list(original.trajectory.records)
        records[5], records[6] = records[6], records[5]
        resequenced = tuple(
            replace(record, sequence=sequence)
            for sequence, record in enumerate(records)
        )
        tampered = replace(original.trajectory, records=resequenced)

        with pytest.raises(ValueError, match="causal order"):
            replay(tampered)

    asyncio.run(scenario())


def test_replay_requires_declared_harness_component_configuration() -> None:
    async def scenario() -> None:
        original = await _capital_trial().run()
        configuration = {"max_actions": 2}
        canonical = json.dumps(
            configuration,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        tampered = replace(
            original.trajectory,
            configuration=configuration,
            config_hash=f"sha256:{hashlib.sha256(canonical).hexdigest()}",
        )

        with pytest.raises(ValueError, match="configuration"):
            replay(tampered)

    asyncio.run(scenario())


def test_replay_rejects_reset_without_a_committed_observation() -> None:
    async def scenario() -> None:
        original = await _capital_trial().run()
        records = list(original.trajectory.records)
        records[1] = replace(records[1], payload={})
        tampered = replace(original.trajectory, records=tuple(records))

        with pytest.raises(ValueError, match="reset observation"):
            replay(tampered)

    asyncio.run(scenario())


def test_replay_rejects_budget_failure_before_the_declared_action_count() -> None:
    class FailingEvaluator:
        name = "budget-failing-evaluator"
        version = "1"
        configuration: dict[str, object] = {}

        async def evaluate(self, *args: object, **kwargs: object) -> Evaluation:
            del args, kwargs
            raise RuntimeError("evaluation failed")

    async def scenario() -> None:
        original = await Trial(
            task=Task(id="tampered-budget-failure", input=None),
            agent=ScriptedAgent(
                [Action.invoke("lookup", {"key": "value"})],
                name="tampered-budget-agent",
                version="1",
            ),
            environment=LookupEnvironment(
                {"value": "observation"},
                name="tampered-budget-environment",
                version="1",
            ),
            evaluator=FailingEvaluator(),
            config=TrialConfig(trial_id="trial-tampered-budget", max_actions=1),
        ).run()
        records = [
            record
            for record in original.trajectory.records
            if record.kind not in {"agent.action", "environment.transition"}
        ]
        records = [
            replace(record, sequence=sequence)
            for sequence, record in enumerate(records)
        ]
        tampered = replace(original.trajectory, records=tuple(records))

        with pytest.raises(ValueError, match="bounded Action loop"):
            replay(tampered)

    asyncio.run(scenario())


def test_replay_binds_failure_phase_to_failure_code() -> None:
    class FailingAgent:
        name = "phase-failing-agent"
        version = "1"
        configuration: dict[str, object] = {}

        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            raise RuntimeError("phase failure")

    async def scenario() -> None:
        original = await Trial(
            task=Task(id="phase-failure", input=None),
            agent=FailingAgent(),
            environment=LookupEnvironment(
                {},
                name="phase-failure-environment",
                version="1",
            ),
            evaluator=ExactEvaluator(None, version="1"),
            config=TrialConfig(trial_id="trial-phase-failure", max_actions=1),
        ).run()
        records = list(original.trajectory.records)
        failure_index = next(
            index for index, record in enumerate(records) if record.kind == "trial.failure"
        )
        records[failure_index] = replace(
            records[failure_index],
            payload={**records[failure_index].payload, "phase": "environment"},
        )
        records[-1] = replace(
            records[-1],
            payload={**records[-1].payload, "phase": "environment"},
        )
        tampered = replace(original.trajectory, records=tuple(records))

        with pytest.raises(ValueError, match="failure code"):
            replay(tampered)

    asyncio.run(scenario())


def test_replay_binds_evaluation_identity_to_configuration() -> None:
    async def scenario() -> None:
        original = await _capital_trial().run()
        records = list(original.trajectory.records)
        evaluation_index = next(
            index
            for index, record in enumerate(records)
            if record.kind == "evaluation.recorded"
        )
        records[evaluation_index] = replace(
            records[evaluation_index],
            payload={
                **records[evaluation_index].payload,
                "evaluator": "other-evaluator",
                "evaluator_version": "999",
            },
        )
        tampered = replace(original.trajectory, records=tuple(records))

        with pytest.raises(ValueError, match="Evaluation identity"):
            replay(tampered)

    asyncio.run(scenario())


def test_replay_rejects_agent_outcomes_after_action_budget_is_spent() -> None:
    async def scenario() -> None:
        original = await _capital_trial(max_actions=1).run()
        committed_prefix = original.trajectory.records[:4]
        forged_outcomes = (
            (
                TrajectoryRecord(
                    sequence=4,
                    kind="trial.failure",
                    payload={
                        "phase": "agent",
                        "code": "agent_decide_error",
                        "exception_type": "RuntimeError",
                        "message": "impossible extra decision",
                    },
                ),
                TrajectoryRecord(
                    sequence=5,
                    kind="trial.terminated",
                    payload={"status": "failed", "phase": "agent"},
                ),
            ),
            (
                TrajectoryRecord(
                    sequence=4,
                    kind="trial.cancelled",
                    payload={"phase": "agent", "operation": "agent.decide"},
                ),
                TrajectoryRecord(
                    sequence=5,
                    kind="trial.terminated",
                    payload={
                        "status": "cancelled",
                        "phase": "agent",
                        "operation": "agent.decide",
                    },
                ),
            ),
        )

        for marker, terminal in forged_outcomes:
            tampered = replace(
                original.trajectory,
                records=(*committed_prefix, marker, terminal),
            )
            with pytest.raises(ValueError, match="execution prefix"):
                replay(tampered)

    asyncio.run(scenario())


def test_agent_failure_becomes_an_attributed_terminal_result() -> None:
    class FailingAgent:
        name = "failing-agent"
        version = "1"
        configuration: dict[str, object] = {}

        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            raise RuntimeError("decision failed")

    async def scenario() -> None:
        trial = Trial(
            task=Task(id="failing-task", input={"question": "fail"}),
            agent=FailingAgent(),
            environment=LookupEnvironment(
                {"unused": "unused"},
                name="failure-environment",
                version="1",
            ),
            evaluator=ExactEvaluator("unused", version="1"),
            config=TrialConfig(trial_id="trial-agent-failure", max_actions=1),
        )

        result = await trial.run()

        assert result.status is TrialStatus.FAILED
        assert result.failure is not None
        assert result.failure.phase == "agent"
        assert result.failure.exception_type == "RuntimeError"
        assert result.failure.message == "decision failed"
        assert [record.kind for record in result.trajectory.records] == [
            "trial.started",
            "environment.reset",
            "trial.failure",
            "trial.terminated",
        ]
        assert result.trajectory.records[-1].payload["status"] == "failed"

    asyncio.run(scenario())


def test_unprintable_exception_still_produces_one_terminal_failure() -> None:
    class UnprintableError(Exception):
        def __str__(self) -> str:
            raise RuntimeError("formatting failed")

    class FailingAgent:
        name = "unprintable-failure-agent"
        version = "1"
        configuration: dict[str, object] = {}

        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            raise UnprintableError()

    async def scenario() -> None:
        result = await Trial(
            task=Task(id="unprintable-failure", input=None),
            agent=FailingAgent(),
            environment=LookupEnvironment(
                {},
                name="unprintable-failure-environment",
                version="1",
            ),
            evaluator=ExactEvaluator(None, version="1"),
            config=TrialConfig(trial_id="trial-unprintable-failure", max_actions=1),
        ).run()

        assert result.status is TrialStatus.FAILED
        assert result.failure is not None
        assert result.failure.exception_type == "UnprintableError"
        assert result.failure.message == "<UnprintableError message unavailable>"
        assert [record.kind for record in result.trajectory.records][-2:] == [
            "trial.failure",
            "trial.terminated",
        ]

    asyncio.run(scenario())


def test_replay_reconstructs_an_attributed_failure() -> None:
    class FailingAgent:
        name = "replay-failing-agent"
        version = "1"
        configuration: dict[str, object] = {}

        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            raise RuntimeError("replay this failure")

    async def scenario() -> None:
        original = await Trial(
            task=Task(id="replay-failure", input=None),
            agent=FailingAgent(),
            environment=LookupEnvironment(
                {},
                name="replay-failure-environment",
                version="1",
            ),
            evaluator=ExactEvaluator(None, version="1"),
            config=TrialConfig(trial_id="trial-replay-failure", max_actions=1),
        ).run()

        replayed = replay(original.trajectory)

        assert replayed.status is TrialStatus.FAILED
        assert replayed.final_output is None
        assert replayed.evaluation is None
        assert replayed.failure == original.failure
        assert replayed.trajectory is original.trajectory

    asyncio.run(scenario())


def test_environment_reset_failure_is_attributed_before_observation() -> None:
    class ResetFailingEnvironment:
        name = "reset-failing-environment"
        version = "1"
        configuration: dict[str, object] = {}

        async def reset(self, *args: object, **kwargs: object) -> Observation:
            del args, kwargs
            raise ConnectionError("reset unavailable")

        async def step(self, *args: object, **kwargs: object) -> None:
            del args, kwargs
            raise AssertionError("unreachable")

    async def scenario() -> None:
        trial = Trial(
            task=Task(id="reset-failure", input=None),
            agent=ScriptedAgent(
                [Action.finish(None)],
                name="unused-agent",
                version="1",
            ),
            environment=ResetFailingEnvironment(),
            evaluator=ExactEvaluator(None, version="1"),
            config=TrialConfig(trial_id="trial-reset-failure", max_actions=1),
        )

        result = await trial.run()

        assert result.status is TrialStatus.FAILED
        assert result.failure is not None
        assert result.failure.phase == "environment"
        assert result.failure.exception_type == "ConnectionError"
        assert [record.kind for record in result.trajectory.records] == [
            "trial.started",
            "trial.failure",
            "trial.terminated",
        ]

    asyncio.run(scenario())


def test_evaluator_failure_keeps_the_terminating_transition() -> None:
    class FailingEvaluator:
        name = "failing-evaluator"
        version = "1"
        configuration: dict[str, object] = {}

        async def evaluate(self, *args: object, **kwargs: object) -> None:
            del args, kwargs
            raise ValueError("evaluation unavailable")

    async def scenario() -> None:
        trial = Trial(
            task=Task(id="evaluation-failure", input=None),
            agent=ScriptedAgent(
                [Action.finish("answer")],
                name="answering-agent",
                version="1",
            ),
            environment=LookupEnvironment(
                {},
                name="answer-environment",
                version="1",
            ),
            evaluator=FailingEvaluator(),
            config=TrialConfig(trial_id="trial-evaluation-failure", max_actions=1),
        )

        result = await trial.run()

        assert result.status is TrialStatus.FAILED
        assert result.failure is not None
        assert result.failure.phase == "evaluator"
        assert result.failure.exception_type == "ValueError"
        assert [record.kind for record in result.trajectory.records] == [
            "trial.started",
            "environment.reset",
            "agent.action",
            "environment.transition",
            "trial.failure",
            "trial.terminated",
        ]

    asyncio.run(scenario())


def test_evaluation_identity_must_match_the_declared_evaluator() -> None:
    class MisidentifiedEvaluator:
        name = "declared-evaluator"
        version = "1"
        configuration: dict[str, object] = {}

        async def evaluate(self, *args: object, **kwargs: object) -> Evaluation:
            del args, kwargs
            self.name = "other-evaluator"
            self.version = "999"
            return Evaluation(
                passed=True,
                score=1.0,
                evaluator="other-evaluator",
                evaluator_version="999",
            )

    async def scenario() -> None:
        result = await Trial(
            task=Task(id="misidentified-evaluation", input=None),
            agent=ScriptedAgent(
                [Action.finish("answer")],
                name="misidentified-evaluation-agent",
                version="1",
            ),
            environment=LookupEnvironment(
                {},
                name="misidentified-evaluation-environment",
                version="1",
            ),
            evaluator=MisidentifiedEvaluator(),
            config=TrialConfig(trial_id="trial-misidentified-evaluation", max_actions=1),
        ).run()

        assert result.status is TrialStatus.FAILED
        assert result.failure is not None
        assert result.failure.phase == "evaluator"
        assert result.failure.code == "evaluator_evaluate_error"
        assert result.evaluation is None

    asyncio.run(scenario())


def test_invalid_environment_reset_result_becomes_a_terminal_failure() -> None:
    class InvalidResetEnvironment:
        name = "invalid-reset-environment"
        version = "1"
        configuration: dict[str, object] = {}

        async def reset(self, *args: object, **kwargs: object) -> object:
            del args, kwargs
            return object()

        async def step(self, *args: object, **kwargs: object) -> None:
            del args, kwargs
            raise AssertionError("unreachable")

    async def scenario() -> None:
        trial = Trial(
            task=Task(id="invalid-reset", input=None),
            agent=ScriptedAgent(
                [Action.finish(None)],
                name="unused-invalid-reset-agent",
                version="1",
            ),
            environment=InvalidResetEnvironment(),
            evaluator=ExactEvaluator(None, version="1"),
            config=TrialConfig(trial_id="trial-invalid-reset", max_actions=1),
        )

        result = await trial.run()

        assert result.status is TrialStatus.FAILED
        assert result.failure is not None
        assert result.failure.phase == "environment"
        assert result.failure.code == "environment_reset_error"
        assert result.failure.exception_type == "TypeError"
        assert [record.kind for record in result.trajectory.records] == [
            "trial.started",
            "trial.failure",
            "trial.terminated",
        ]

    asyncio.run(scenario())
