# iamai General-Agent Harness

iamai is evolving toward a harness for auditable, replayable experiments on increasingly general agents. The harness keeps task execution, environment interaction, evidence, and evaluation independent from any one model, platform, or agent pattern.

## Language

**AGI North Star**:
The research direction of building agents that transfer across explicit Task and Environment distributions, operate reliably over longer horizons, learn from evidence, and remain controllable. It is not a shipped capability, release claim, or single benchmark threshold.
_Avoid_: AGI feature, AGI score

**Runtime**:
The stable messaging lifecycle host that loads Adapters and Plugins and dispatches Events. It is not the Harness or a Trial executor.
_Avoid_: Harness, Agent runtime

**Event**:
The stable normalized messaging envelope dispatched by the Runtime. It is not an Observation or a Trajectory record.
_Avoid_: Observation, Transition

**SessionManager**:
The stable messaging waiter and backlog coordinator. It is not an Experiment store, Trial, or Trajectory store.
_Avoid_: Trial session, episode store

**Harness**:
The headless execution system that runs and records Experiments and Trials. It is independent from the stable messaging Runtime, which may host a messaging Environment.
_Avoid_: Agent runtime, bot framework

**Experiment**:
A versioned comparison plan and its collected results over one or more Trials. Its task distribution, seeds, budgets, Agent versions, Environment versions, Evaluations, baselines, and caller-declared provenance are explicit.
_Avoid_: Benchmark run, test batch

**Trial**:
One bounded attempt by an Agent to complete a Task in an Environment under a fixed seed, budget, and configuration.
_Avoid_: Run, episode, session

**Task**:
The goal and initial data presented to a Trial. Evaluation criteria are declared by the selected Evaluator.
_Avoid_: Prompt, request

**Agent**:
The decision-maker in a Trial. An Agent consumes Observations and proposes Actions; it may use a model, rules, search, memory, or human input internally.
_Avoid_: LLM, bot, plugin

**Environment**:
The authoritative world a Trial interacts with. It produces Observations and commits the consequences of Actions.
_Avoid_: Tool registry, adapter, runtime

**Observation**:
Information exposed by an Environment for an Agent's next decision. It may be partial, noisy, delayed, or adversarial.
_Avoid_: Message, event, tool result

**Action**:
An Agent's proposed interaction with an Environment or its final answer for the Task.
_Avoid_: Tool call, command, response

**Transition**:
The committed outcome of applying an Action to an Environment, including the next Observation and termination state.
_Avoid_: Callback result, event

**Tool Specification**:
A frozen, versioned declaration for one asynchronous Tool, including its supported input schema, permission label, runtime capability claims, approval requirement, and token or cost reservation. Its metadata enables validation and audit; it does not isolate the implementation.
_Avoid_: Runtime ToolRegistry entry, sandbox policy

**Tool Call**:
One non-final Action presented to a Controlled Tool Environment as an invocation attempt. It may be rejected before matching a Tool Specification; its Harness-visible outcome does not prove that an external effect occurred exactly once.
_Avoid_: Plugin command, final answer

**Execution Policy**:
A versioned, static, default-deny declaration over Tool names, permission labels, and declared runtime capabilities. It is not the stable Runtime Permission, dynamic authorization, or containment.
_Avoid_: Permission, sandbox, policy engine

**Approval**:
An Approver decision hash-bound to one Tool invocation through a fresh request nonce, Trial Action, Tool Specification, arguments, Execution Policy, Execution Budget, and reservation. It is not blanket permission or proof of safety.
_Avoid_: Permission grant, safety check

**Execution Budget**:
Run-scoped Tool-attempt and reservation ceilings plus a per-call cooperative timeout shared by approval and Tool execution. It is not a Trial-wide deadline, an independently verified bill, or external-effect rollback.
_Avoid_: Trial budget, billing guarantee

**Trajectory**:
The append-only, causally ordered evidence of a Trial. It records decision-relevant inputs and committed outcomes so the Trial can be audited and replayed without claiming access to hidden reasoning.
_Avoid_: Trace, transcript, log

**Trajectory Store**:
Append-only persistence for versioned Experiment plans, Trial start markers, and immutable terminal Trajectories. It validates provenance and Replay before projecting results; it is not the messaging StateStore or SessionManager.
_Avoid_: StateStore, SessionManager, log database

**Evaluation**:
A versioned judgment derived from a committed Trajectory under the selected Evaluator's declared criteria.
_Avoid_: Reward, assertion, score only

**Replay**:
Reconstruction of Trial projections and Evaluation from an existing Trajectory without repeating Agent decisions or external effects.
_Avoid_: Re-execution, retry

**Re-execution**:
A fresh Trial using the same declared specification. It produces the same result only when every participating component and dependency is deterministic.
_Avoid_: Replay

**Policy Checkpoint**:
An immutable version of the Agent behavior selected for an Experiment, including the model, prompts, memory policy, and action policy that affect decisions.
_Avoid_: Latest model, mutable agent state
