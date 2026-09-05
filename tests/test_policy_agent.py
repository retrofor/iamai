from __future__ import annotations

import asyncio
from collections.abc import Mapping

import pytest

import iamai
import iamai.harness as harness
from iamai.harness import (
    Action,
    ExactEvaluator,
    Experiment,
    JsonlTrajectoryStore,
    LookupEnvironment,
    Observation,
    PolicyAgent,
    PolicyCheckpoint,
    ScriptedPolicy,
    Task,
    TaskDistributionManifest,
    Trial,
    TrialConfig,
    TrialStatus,
    Trajectory,
    compare_experiment,
    replay,
)


def _checkpoint(**overrides: object) -> PolicyCheckpoint:
    values: dict[str, object] = {
        "checkpoint_id": "capital-policy",
        "version": "1",
        "provider": None,
        "model": None,
        "prompt_policy": {"template_version": "fixture-1"},
        "tool_policy": {"allowed_actions": ["lookup", "final"]},
        "memory_policy": {"kind": "none"},
        "context_policy": {"kind": "full-observation"},
        "configuration": {"fixture": True},
    }
    values.update(overrides)
    return PolicyCheckpoint(**values)  # type: ignore[arg-type]


def _policy_agent(
    checkpoint: PolicyCheckpoint,
    *,
    actions: tuple[Action, ...] = (Action.finish("Paris"),),
) -> PolicyAgent:
    return PolicyAgent(
        ScriptedPolicy(actions, name="capital-script", version="1"),
        checkpoint,
        name="capital-policy-agent",
        version="1",
    )


def _trial(
    *,
    trial_id: str,
    agent: PolicyAgent,
    task_id: str = "capital-of-france",
    seed: int = 7,
) -> Trial:
    return Trial(
        task=Task(task_id, {"question": "What is the capital of France?"}),
        agent=agent,
        environment=LookupEnvironment({}, name="country-capitals", version="1"),
        evaluator=ExactEvaluator("Paris", version="1"),
        config=TrialConfig(trial_id=trial_id, seed=seed, max_actions=1),
    )


def test_policy_api_is_provisional_harness_only() -> None:
    names = {"PolicyCheckpoint", "AgentPolicy", "PolicyAgent", "ScriptedPolicy"}

    assert names.issubset(harness.__all__)
    assert "POLICY_CHECKPOINT_FORMAT_VERSION" not in harness.__all__
    for name in names:
        assert not hasattr(iamai, name)


def test_checkpoint_freezes_nested_source_values() -> None:
    source = {"template": {"parts": ["system", "task"]}}
    checkpoint = _checkpoint(prompt_policy=source)

    source["template"]["parts"].append("mutated")

    assert checkpoint.prompt_policy["template"]["parts"] == ("system", "task")
    with pytest.raises(TypeError):
        checkpoint.prompt_policy["new"] = "value"  # type: ignore[index]
    with pytest.raises(TypeError):
        checkpoint.prompt_policy["template"]["parts"] = ()  # type: ignore[index]


def test_checkpoint_hash_is_stable_across_mapping_insertion_order() -> None:
    first = _checkpoint(
        prompt_policy={"alpha": 1, "nested": {"left": True, "right": None}},
    )
    second = _checkpoint(
        prompt_policy={"nested": {"right": None, "left": True}, "alpha": 1},
    )

    assert first.checkpoint_hash == second.checkpoint_hash
    assert first.checkpoint_hash.startswith("sha256:")


@pytest.mark.parametrize(
    "changed",
    (
        {"checkpoint_id": "other-policy"},
        {"version": "2"},
        {"provider": "openai-compatible", "model": "example-model"},
        {"prompt_policy": {"template_version": "fixture-2"}},
        {"tool_policy": {"allowed_actions": ["final"]}},
        {"memory_policy": {"kind": "window", "size": 4}},
        {"context_policy": {"kind": "last-observation"}},
        {"configuration": {"fixture": False}},
    ),
)
def test_checkpoint_hash_binds_every_semantic_field(changed: dict[str, object]) -> None:
    assert _checkpoint(**changed).checkpoint_hash != _checkpoint().checkpoint_hash


@pytest.mark.parametrize(
    ("provider", "model"),
    ((None, None), ("openai-compatible", "example-model")),
)
def test_checkpoint_accepts_paired_provider_and_model(
    provider: str | None,
    model: str | None,
) -> None:
    checkpoint = _checkpoint(provider=provider, model=model)

    assert checkpoint.provider == provider
    assert checkpoint.model == model


@pytest.mark.parametrize(
    ("provider", "model"),
    (("provider", None), (None, "model")),
)
def test_checkpoint_rejects_partial_provider_declaration(
    provider: str | None,
    model: str | None,
) -> None:
    with pytest.raises(ValueError, match="must be declared together"):
        _checkpoint(provider=provider, model=model)


@pytest.mark.parametrize(
    ("provider", "model"),
    (("", "model"), ("provider", ""), ("   ", "model"), ("provider", "   ")),
)
def test_checkpoint_rejects_empty_provider_declaration(
    provider: str,
    model: str,
) -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        _checkpoint(provider=provider, model=model)


@pytest.mark.parametrize(
    "prompt_policy",
    (
        {"value": float("nan")},
        {1: "non-string-key"},
        {"value": object()},
    ),
)
def test_checkpoint_reuses_harness_json_validation(prompt_policy: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        _checkpoint(prompt_policy=prompt_policy)


def test_checkpoint_rejects_excessive_json_nesting() -> None:
    nested: object = "leaf"
    for _ in range(129):
        nested = [nested]

    with pytest.raises(ValueError, match="maximum JSON nesting depth"):
        _checkpoint(context_policy={"nested": nested})


def test_policy_agent_freezes_the_required_configuration_shape() -> None:
    source = {"temperature": 0, "stops": ["done"]}

    class MutablePolicy:
        name = "mutable-policy"
        version = "1"
        configuration = source

        async def decide(
            self,
            task: Task,
            observation: Observation,
            trajectory: Trajectory,
            *,
            seed: int,
            action_index: int,
        ) -> Action:
            del task, observation, trajectory, seed, action_index
            return Action.finish("Paris")

    checkpoint = _checkpoint()
    agent = PolicyAgent(MutablePolicy(), checkpoint)
    source["stops"].append("mutated")

    assert agent.configuration["kind"] == "policy_backed"
    declaration = agent.configuration["policy_checkpoint"]
    implementation = agent.configuration["policy_implementation"]
    assert isinstance(declaration, Mapping)
    assert isinstance(implementation, Mapping)
    assert declaration["checkpoint_hash"] == checkpoint.checkpoint_hash
    assert implementation == {
        "name": "mutable-policy",
        "version": "1",
        "config": {"temperature": 0, "stops": ("done",)},
    }
    with pytest.raises(TypeError):
        implementation["name"] = "changed"  # type: ignore[index]


@pytest.mark.parametrize(
    ("name", "version", "configuration", "error", "match"),
    (
        ("", "1", {}, ValueError, "AgentPolicy name cannot be empty"),
        ("policy", "", {}, ValueError, "AgentPolicy version cannot be empty"),
        ("policy", "1", [], TypeError, "configuration must be an object"),
    ),
)
def test_policy_agent_validates_policy_declaration(
    name: str,
    version: str,
    configuration: object,
    error: type[Exception],
    match: str,
) -> None:
    class InvalidPolicy:
        async def decide(self, *args: object, **kwargs: object) -> Action:
            del args, kwargs
            return Action.finish("unused")

    policy = InvalidPolicy()
    policy.name = name
    policy.version = version
    policy.configuration = configuration

    with pytest.raises(error, match=match):
        PolicyAgent(policy, _checkpoint())  # type: ignore[arg-type]


def test_policy_agent_completes_a_deterministic_trial() -> None:
    async def scenario() -> None:
        agent = _policy_agent(
            _checkpoint(),
            actions=(
                Action.invoke("lookup", {"key": "france"}),
                Action.finish("Paris"),
            ),
        )
        result = await Trial(
            task=Task("capital-of-france", {"question": "Capital?"}),
            agent=agent,
            environment=LookupEnvironment(
                {"france": "Paris"},
                name="country-capitals",
                version="1",
            ),
            evaluator=ExactEvaluator("Paris", version="1"),
            config=TrialConfig("policy-trial", seed=7, max_actions=2),
        ).run()

        assert result.status is TrialStatus.COMPLETED
        assert result.final_output == "Paris"
        assert result.evaluation is not None
        assert result.evaluation.passed

    asyncio.run(scenario())


def test_scripted_policy_has_no_hidden_cross_trial_cursor() -> None:
    async def scenario() -> None:
        policy = ScriptedPolicy((Action.finish("Paris"),))
        agent = PolicyAgent(policy, _checkpoint())

        first = await _trial(trial_id="policy-reuse-1", agent=agent).run()
        second = await _trial(trial_id="policy-reuse-2", agent=agent).run()

        assert first.status is TrialStatus.COMPLETED
        assert second.status is TrialStatus.COMPLETED
        assert first.trajectory.config_hash == second.trajectory.config_hash

    asyncio.run(scenario())


def test_checkpoint_changes_bind_the_trial_configuration_hash() -> None:
    first = _trial(
        trial_id="checkpoint-a",
        agent=_policy_agent(_checkpoint(prompt_policy={"template": "a"})),
    )
    second = _trial(
        trial_id="checkpoint-b",
        agent=_policy_agent(_checkpoint(prompt_policy={"template": "b"})),
    )

    assert first.trajectory.configuration["agent"] != second.trajectory.configuration["agent"]
    assert first.trajectory.config_hash != second.trajectory.config_hash


def test_task_trial_id_and_seed_do_not_pollute_configuration_hash() -> None:
    agent = _policy_agent(_checkpoint())
    first = _trial(trial_id="declaration-a", task_id="task-a", seed=1, agent=agent)
    second = _trial(trial_id="declaration-b", task_id="task-b", seed=2, agent=agent)

    assert first.trajectory.config_hash == second.trajectory.config_hash


def test_replay_does_not_reinvoke_the_policy() -> None:
    class CountingPolicy:
        name = "counting-policy"
        version = "1"
        configuration: dict[str, object] = {}

        def __init__(self) -> None:
            self.calls = 0

        async def decide(
            self,
            task: Task,
            observation: Observation,
            trajectory: Trajectory,
            *,
            seed: int,
            action_index: int,
        ) -> Action:
            del task, observation, trajectory, seed, action_index
            self.calls += 1
            return Action.finish("Paris")

    async def scenario() -> None:
        policy = CountingPolicy()
        result = await _trial(
            trial_id="policy-replay",
            agent=PolicyAgent(policy, _checkpoint()),
        ).run()
        trajectory = result.trajectory

        replayed = replay(trajectory)

        assert policy.calls == 1
        assert replayed.status is result.status
        assert replayed.final_output == result.final_output
        assert replayed.evaluation == result.evaluation

    asyncio.run(scenario())


def test_checkpoint_round_trips_through_paired_experiment_evidence(tmp_path) -> None:
    async def scenario() -> None:
        baseline_checkpoint = _checkpoint(prompt_policy={"template": "baseline"})
        candidate_checkpoint = _checkpoint(prompt_policy={"template": "candidate"})
        store = JsonlTrajectoryStore(tmp_path / "policy-evidence.jsonl")
        result = await Experiment(
            experiment_id="policy-evidence",
            version="1",
            baseline="baseline",
            task_distribution=TaskDistributionManifest(
                suite_id="policy-suite",
                version="1",
                split="test",
                case_ids=("capital-of-france/seed-7",),
                sampling_rule="ordered-full-set-v1",
            ),
            trials={
                "baseline": (
                    _trial(
                        trial_id="policy-baseline",
                        agent=_policy_agent(baseline_checkpoint),
                    ),
                ),
                "candidate": (
                    _trial(
                        trial_id="policy-candidate",
                        agent=_policy_agent(candidate_checkpoint),
                    ),
                ),
            },
        ).run(store)
        loaded = store.load()

        assert loaded is not None
        assert loaded == result
        assert loaded.plan_hash == result.plan_hash
        assert loaded.jsonl_verified is True
        candidate_spec = loaded.plan.trial_specs["candidate"][0]
        agent_declaration = candidate_spec.configuration["agent"]
        assert isinstance(agent_declaration, Mapping)
        agent_configuration = agent_declaration["config"]
        assert isinstance(agent_configuration, Mapping)
        checkpoint_declaration = agent_configuration["policy_checkpoint"]
        assert isinstance(checkpoint_declaration, Mapping)
        assert checkpoint_declaration["checkpoint_hash"] == (
            candidate_checkpoint.checkpoint_hash
        )
        comparison = compare_experiment(loaded, candidate="candidate")
        assert comparison.total_pairs == 1
        assert comparison.pass_rate_delta == 0.0

    asyncio.run(scenario())
