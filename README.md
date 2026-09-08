<p align="center">
  <img src="https://raw.githubusercontent.com/retrofor/iamai/dev/docs/_static/brand/iamai-logo.svg" alt="iamai gateway mark" width="120">
</p>

<h1 align="center">iamai</h1>

<p align="center">
  <strong>The message runtime between platforms and your logic.</strong>
</p>

<p align="center">
  Normalize events once. Run typed async Python plugins, optional agent workflows,<br>
  and Rust-backed message operations across every adapter.
</p>

<p align="center">
  <a href="https://github.com/retrofor/iamai"><img src="https://img.shields.io/github/stars/retrofor/iamai?logo=github&label=Stars" alt="GitHub stars"></a>
  <a href="https://pypi.org/project/iamai/"><img src="https://img.shields.io/pypi/v/iamai?color=e8462f&label=PyPI" alt="PyPI version"></a>
  <a href="https://pypi.org/project/iamai/"><img src="https://img.shields.io/badge/Python_3.11+-17212b?logo=python&logoColor=white" alt="Python 3.11 or newer"></a>
  <a href="https://github.com/retrofor/iamai/actions/workflows/check.yml"><img src="https://github.com/retrofor/iamai/actions/workflows/check.yml/badge.svg?branch=dev" alt="CI status"></a>
  <a href="https://github.com/retrofor/iamai/blob/dev/LICENSE"><img src="https://img.shields.io/badge/license-MIT-159b7a" alt="MIT license"></a>
</p>

<p align="center">
  <a href="https://github.com/retrofor/iamai/blob/dev/docs/quickstart.rst">Quickstart</a> ·
  <a href="https://github.com/retrofor/iamai/tree/dev/docs/tutorials">Tutorials</a> ·
  <a href="https://github.com/retrofor/iamai/tree/dev/examples">Examples</a> ·
  <a href="https://github.com/retrofor/iamai/blob/dev/docs/reference/extensions.rst">Extension contract</a> ·
  <a href="https://github.com/retrofor/iamai/releases/tag/v1.0.0">v1.0.0</a>
</p>

<p align="center">
  <b>English</b> · <a href="https://github.com/retrofor/iamai/blob/dev/README.zh.md">中文</a>
</p>

---

## Why iamai

Chat platforms disagree about payloads, transports, authentication, and reply APIs. Your
application logic should not have to.

iamai puts a small, explicit runtime between those two worlds:

| Boundary | What iamai makes stable |
|---|---|
| **Platform edge** | Adapters normalize Terminal, OneBot, Telegram, and Webhook traffic into `Event` and `Message` objects. |
| **Application code** | Plugins use `Context`, commands, rules, permissions, dependency injection, middleware, state, and sessions. |
| **Runtime lifecycle** | Discovery, startup, shutdown, reload, rollback, configuration, and observability have documented behavior. |
| **Agent execution** | Optional model calls, Tool metadata, approval hooks, traces, and example guardrails remain explicit and auditable. |

iamai is a runtime, not an all-in-one bot dashboard. It does not require an LLM, hide the
network boundary, or force application code into a platform-specific SDK. Python owns the
behavior that changes; Rust accelerates selected message and normalization paths.

> **Stable contract:** `v1.0.0` is the current 1.x compatibility line. Third-party extensions
> should declare `iamai>=1,<2` and run the public conformance helpers before release.

## General-agent research harness

iamai is evolving beyond its stable messaging Runtime toward recorded, replayable experiments on
increasingly general agents. The provisional `iamai.harness` namespace now provides the first
headless, model-independent slice:

```text
Task → Agent → Environment → Trajectory → Evaluation
```

It runs bounded Trials, records immutable causal Trajectories, attributes failure and cancellation,
and can replay results without repeating Agent decisions or Environment effects. The included
`ScriptedAgent`, `LookupEnvironment`, and `ExactEvaluator` are deterministic baselines; they do not
require a chat platform or an LLM.

Versioned `Experiment` plans can group explicit baseline and candidate variants. A
`JsonlTrajectoryStore` persists the plan, caller-declared provenance, Trial start markers, and full
terminal Trajectories as integrity-checked JSONL, then resumes already committed Trials without
repeating their effects. A start-only interrupted Trial is never re-executed automatically; other
never-started Trials in the same plan may continue and the result remains explicitly incomplete.

For paired experiment evidence, a `TaskDistributionManifest` pre-registers the suite, split,
ordered case IDs, and sampling rule together with exactly one baseline and one candidate.
`compare_experiment` accepts only a complete, `JsonlTrajectoryStore`-verified result and returns
read-only `TrialComparison` and `ExperimentComparison` values over the fixed denominator, including
failed and budget-exhausted Trials. The resulting hashes are stable identifiers and integrity checks
for descriptive evidence; they are not signatures, statistical significance tests, or proof of
generalization beyond the declared distribution.

Policy-backed Agents can now bind a provider-neutral, caller-declared `PolicyCheckpoint` into the
same Trial, Experiment, and JSONL provenance path. The checkpoint records non-secret policy metadata
and exposes a canonical integrity hash; it is not an attestation, provider/model identity proof,
prompt or Tool enforcement mechanism, or secret store. Remote provider integration remains future work.

For declared asynchronous Tools, `ControlledToolEnvironment` adds strict `ToolSpec` input
validation, a static default-deny `ExecutionPolicy`, approvals bound to one exact request, and
run-scoped reservation ledgers for Tool calls, tokens, and integer cost microunits. Each handled
non-final Action records a `tool.call.outcome`; final Actions still terminate through the
Environment without becoming Tool calls.

These controls apply only to declared Harness Tool calls.
They are not an OS, process, or network sandbox, a proof of safety, or an exactly-once guarantee.
`tool_timeout_seconds` is a cooperative
per-call timeout shared by approval and Tool execution, while `ToolResult` usage remains a trusted
report from the Tool adapter rather than an independently verified provider bill.

This namespace is deliberately not re-exported from top-level `iamai` and is not part of the stable
1.x messaging contract yet. AGI is the research north star, not a shipped capability: progress must
name the task/environment distribution, seeds, budgets, component versions, and baseline. See the
[research harness guide](https://github.com/retrofor/iamai/blob/dev/docs/guides/research-harness.rst)
and [roadmap](https://github.com/retrofor/iamai/blob/dev/docs/guides/roadmap.rst).

## Run a real message through it

Install the stable runtime in your own project:

```bash
python -m pip install "iamai>=1,<2"
```

To exercise the complete Adapter → Runtime → Plugin → reply path, run the maintained terminal
example from this repository:

```bash
git clone --depth 1 https://github.com/retrofor/iamai.git
cd iamai
uv sync --locked --all-packages --group dev

# Validate config, extension discovery, and plugin schemas before startup.
uv run --package echo-runtime iamai \
  --config examples/echo-runtime/config.terminal.toml config-check

# Start the local TerminalAdapter runtime.
uv run --package echo-runtime iamai \
  --config examples/echo-runtime/config.terminal.toml
```

At the prompt, enter:

```text
/echo hello iamai
```

The example replies through the same adapter that accepted the event. The
[quickstart](https://github.com/retrofor/iamai/blob/dev/docs/quickstart.rst) explains the
configuration and the objects involved.

Your application code remains ordinary async Python:

```python
from iamai import Context, Plugin, command


class HelloPlugin(Plugin):
    name = "hello"

    @command("hello")
    async def hello(self, ctx: Context) -> None:
        await ctx.reply("Hello from iamai.")
```

## One runtime, hard boundaries

```text
Terminal · OneBot · Telegram · Webhook · your protocol
                         │
                         ▼
                      Adapter
              payload → Event + Message
                         │
                         ▼
       Rules · Permissions · DI · Middleware
                       Runtime
                         │
                         ▼
              Plugin or agent workflow
                         │
                         └──── Context.reply() ────► Adapter ────► platform
```

| Layer | Owns | Source |
|---|---|---|
| **Adapter** | Networking, trust, protocol conversion, reconnection, and outbound APIs | [`python/iamai/adapters`](https://github.com/retrofor/iamai/tree/dev/python/iamai/adapters) |
| **Runtime** | Configuration, extension discovery, lifecycle, dispatch, DI, middleware, state, sessions, and reload | [`python/iamai`](https://github.com/retrofor/iamai/tree/dev/python/iamai) |
| **Plugin** | Commands, event handlers, rules, permissions, and product behavior | [`examples`](https://github.com/retrofor/iamai/tree/dev/examples) |
| **Rust core** | Message-chain operations, OneBot normalization, and JSON data helpers | [`src`](https://github.com/retrofor/iamai/tree/dev/src) |

The [architecture guide](https://github.com/retrofor/iamai/blob/dev/docs/guides/architecture.rst)
defines admission, dispatch, reload, invalidation, and shutdown semantics in detail.

## What ships in 1.0

| Surface | Included capabilities |
|---|---|
| **Messaging** | `TerminalAdapter`, OneBot 11 over HTTP/WebSocket/reverse WebSocket, Telegram long polling, generic webhooks with optional signature verification, and custom adapters |
| **Application model** | Commands, message and event handlers, composable `Rule` and `Permission`, dependency injection, middleware, and event-scoped `Context` |
| **Stateful workflows** | Memory, JSON, and SQLite state backends plus session waiters keyed by adapter, channel, and user |
| **Operations** | Strict configuration validation, versioned JSON Schema, health/metrics views, audit events, management commands, and transactional hot reload |
| **Agent primitives** | OpenAI-compatible calls, `ToolRegistry`, approval hooks, append-only `AgentTrace`, and output guardrails; all optional |
| **Public contracts** | Versioned serialization, deterministic extension discovery, lifecycle rules, deprecation policy, migration guide, and conformance helpers |

## Start from a runnable shape

The repository examples are complete workspace packages, not isolated snippets.

| Example | Start here for... |
|---|---|
| [`echo-runtime`](https://github.com/retrofor/iamai/tree/dev/examples/echo-runtime) | The smallest terminal, OneBot, and Webhook runtime |
| [`state-runtime`](https://github.com/retrofor/iamai/tree/dev/examples/state-runtime) | State backends and session-scoped conversations |
| [`group-assistant-runtime`](https://github.com/retrofor/iamai/tree/dev/examples/group-assistant-runtime) | Permissions, group workflows, and tool routing |
| [`react-runtime`](https://github.com/retrofor/iamai/tree/dev/examples/react-runtime) | ReAct tools, memory, and trace inspection |
| [`planner-executor-runtime`](https://github.com/retrofor/iamai/tree/dev/examples/planner-executor-runtime) | Structured planning followed by staged execution |
| [`supervisor-team-runtime`](https://github.com/retrofor/iamai/tree/dev/examples/supervisor-team-runtime) | Role-specialized workers coordinated by a supervisor |

Agent components do not replace the runtime model. They are plugin building blocks with explicit
dependency and security boundaries, documented in the
[agent runtime guide](https://github.com/retrofor/iamai/blob/dev/docs/guides/agent-runtime.rst).

## Extend it without forking it

Third-party packages can publish `iamai.plugins` and `iamai.adapters` Python entry points. iamai
rejects duplicate, reserved, invalid, or incompatible extensions instead of selecting one
ambiguously, and exposes reusable adapter/plugin conformance helpers for package authors.

- [Extension packaging and discovery](https://github.com/retrofor/iamai/blob/dev/docs/reference/extensions.rst)
- [Serialization contract](https://github.com/retrofor/iamai/blob/dev/docs/reference/serialization-contract.rst)
- [Lifecycle contract](https://github.com/retrofor/iamai/blob/dev/docs/reference/public-api-lifecycle.rst)
- [Public API conformance matrix](https://github.com/retrofor/iamai/blob/dev/docs/reference/public-api-conformance.rst)
- [0.3 → 1.0 migration guide](https://github.com/retrofor/iamai/blob/dev/docs/guides/migration-0.3-to-1.0.rst)

## Find the right entry point

| If you want to... | Go to |
|---|---|
| Run the first local message | [Quickstart](https://github.com/retrofor/iamai/blob/dev/docs/quickstart.rst) |
| Build one feature end to end | [Progressive tutorials](https://github.com/retrofor/iamai/tree/dev/docs/tutorials) |
| Design plugins, adapters, state, or operations | [Guides](https://github.com/retrofor/iamai/tree/dev/docs/guides) |
| Inspect public Python classes and functions | [API reference source](https://github.com/retrofor/iamai/tree/dev/docs/api) |
| Publish or discover an extension | [Community store](https://github.com/retrofor/iamai/blob/dev/docs/community/store.rst) |
| Compare iamai with platform and agent frameworks | [Ecosystem comparison](https://github.com/retrofor/iamai/blob/dev/docs/guides/ecosystem-comparison.rst) |
| Run a recorded, replayable headless agent Trial | [Research harness guide](https://github.com/retrofor/iamai/blob/dev/docs/guides/research-harness.rst) |

## Development

```bash
uv sync --locked --all-packages --group dev --group docs
uv run ruff check .
uv run python -m mypy
uv run pytest
cargo test --no-default-features
bash scripts/check_example_configs.sh
uv run sphinx-build -W --keep-going -b html docs docs/_build/html
```

Open pull requests against `dev`. Public behavior changes require tests and the corresponding
contract documentation. Active work lives in [Issues](https://github.com/retrofor/iamai/issues);
design discussions live in [Discussions](https://github.com/retrofor/iamai/discussions).

## License and acknowledgements

[MIT](https://github.com/retrofor/iamai/blob/dev/LICENSE) © iamai contributors.

iamai draws lessons from [NoneBot](https://github.com/nonebot/nonebot2),
[Koishi](https://github.com/koishijs/koishi), and
[AliceBot](https://github.com/AliceBotProject/alicebot). Its agent examples are informed by the
[ReAct paper](https://arxiv.org/abs/2210.03629) and the wider agent-runtime community.
