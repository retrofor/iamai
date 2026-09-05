---
status: accepted
---

# Bind Agent behavior to policy checkpoints

## Decision

The provisional Harness composes `PolicyCheckpoint`, `AgentPolicy`, and
`PolicyAgent` with the existing Agent interface. `ScriptedPolicy` provides an
offline deterministic fixture for tests and examples. Remote provider adapters
are future integrations and do not belong in the Harness core.

`PolicyCheckpoint` freezes caller-declared decision-relevant policy metadata:
provider and model identity when applicable, prompt and tool-use policy, memory
policy, context shaping, and versioned configuration. `PolicyAgent` places the
checkpoint and the policy implementation declaration in its existing Agent
`configuration`.

## Provenance

The existing Agent configuration hash binds the declaration into Trial and
Experiment evidence. The same generic configuration path carries it into Trial
`config_hash`, Experiment spec and plan hashes, JSONL persistence, Replay, and
paired comparison. No policy-specific provenance record, Store, registry, or
Replay path is introduced.

The checkpoint hash is a canonical content integrity identifier. It is not an attestation.
It is also not a signature, trusted timestamp, provider attestation, model binary
fingerprint, or proof of model execution. The Harness does not independently
attest that a remote provider, model, prompt, memory policy, or tool-use policy
matched the declaration, or that a policy implementation faithfully applied it.

## Compatibility

This decision does not change the Harness top-level configuration, Trajectory
format, Experiment Store format, comparison projection version, or Replay
execution model. Replay remains effect-free and does not invoke a policy,
provider, Agent, Environment, or Tool. The stable messaging Runtime remains
separate; these APIs are exported only from provisional `iamai.harness`.

The abstraction is provider-neutral and adds no provider SDK, network request,
prompt engine, memory system, or Tool executor.

## Security boundary

Policy checkpoints are non-secret persisted provenance. They must not contain
API keys, access tokens, credentials, or other private secrets because the
declaration may be persisted in Experiment plans and JSONL evidence. A policy
checkpoint is not a secret store.

`AgentPolicy` controls Agent decisions. It is distinct from `ExecutionPolicy`,
which authorizes Tool execution inside `ControlledToolEnvironment`.
`PolicyCheckpoint.tool_policy` is behavior provenance metadata only; it does not
allow, deny, approve, budget, sandbox, or otherwise authorize a Tool call.
