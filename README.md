<p align="center">
  <img src="https://raw.githubusercontent.com/retrofor/iamai/dev/docs/_static/brand/iamai-logo.svg" alt="iamai runtime mark" width="128">
</p>

<h1 align="center">iamai</h1>

<p align="center">
  <em>A compact Python + Rust runtime for cross-platform messaging, plugins, and auditable AI agents.</em>
</p>

<p align="center">
  <a href="https://github.com/retrofor/iamai"><img src="https://img.shields.io/github/stars/retrofor/iamai?logo=github" alt="GitHub stars"></a>
  <a href="https://pypi.org/project/iamai/"><img src="https://img.shields.io/pypi/v/iamai?color=e8462f" alt="PyPI"></a>
  <a href="https://pypi.org/project/iamai/"><img src="https://img.shields.io/pypi/pyversions/iamai" alt="Python versions"></a>
  <a href="https://github.com/retrofor/iamai/actions/workflows/check.yml"><img src="https://github.com/retrofor/iamai/actions/workflows/check.yml/badge.svg?branch=dev" alt="CI"></a>
  <a href="https://github.com/retrofor/iamai/tree/dev/docs"><img src="https://img.shields.io/badge/docs-source-17212b?logo=readthedocs&logoColor=white" alt="Documentation source"></a>
  <a href="https://github.com/retrofor/iamai/blob/dev/LICENSE"><img src="https://img.shields.io/badge/license-MIT-2a9d78" alt="MIT license"></a>
  <br>
  <img src="https://img.shields.io/badge/Python_3.11+-17212b?logo=python&logoColor=white" alt="Python 3.11 or newer">
  <img src="https://img.shields.io/badge/Rust_Core-17212b?logo=rust&logoColor=white" alt="Rust core">
  <img src="https://img.shields.io/badge/PyO3-17212b" alt="PyO3">
  <img src="https://img.shields.io/badge/asyncio-17212b" alt="asyncio">
</p>

<p align="center">
  <b>English</b> · <a href="https://github.com/retrofor/iamai/blob/dev/README.zh.md">中文</a>
</p>

---

## What Is iamai

**iamai** is an open-source runtime for chatbots, event-driven applications, and lightweight AI agents. It keeps platform protocols at the edge and lets business logic stay in ordinary async Python plugins.

Adapters normalize terminal, WebSocket, HTTP, Telegram, and OneBot payloads into stable `Event`, `Message`, and `Context` objects. The runtime then handles discovery, lifecycle, dispatch, rules, permissions, dependency injection, middleware, state, sessions, and observability. Selected message and normalization primitives run in a Rust extension through PyO3.

iamai is deliberately a runtime, not an all-in-one agent platform. You can use the built-in agent primitives, replace them, or run without an LLM at all.

---

## How It Works

```text
external platform
  -> Adapter validates and normalizes a payload
  -> Runtime matches handlers and evaluates Rule + Permission + DI
  -> Plugin executes inside event-scoped Context
  -> Context.reply() delegates the response back to the Adapter
```

| Layer | Responsibility | Source |
|---|---|---|
| **Adapter** | Networking, authentication, signatures, protocol conversion, outbound APIs | [`python/iamai/adapters`](https://github.com/retrofor/iamai/tree/dev/python/iamai/adapters) |
| **Runtime** | Configuration, extension discovery, lifecycle, dispatch, DI, middleware, state, sessions, hot reload | [`python/iamai`](https://github.com/retrofor/iamai/tree/dev/python/iamai) |
| **Plugin** | Commands, message/event handlers, rules, permissions, and application behavior | [`examples`](https://github.com/retrofor/iamai/tree/dev/examples) |
| **Rust core** | Message-chain operations, OneBot normalization, JSON merge helpers | [`src`](https://github.com/retrofor/iamai/tree/dev/src) |

The complete lifecycle, including admission, middleware, reload, and shutdown semantics, is documented in the [architecture guide](https://github.com/retrofor/iamai/blob/dev/docs/guides/architecture.rst).

---

## Features

- **Protocol-neutral plugins**: write against `Event`, `Message`, and `Context`, not platform payloads.
- **Explicit extension model**: load plugins and adapters by import path or standard Python entry points.
- **Structured dispatch**: commands, message handlers, event handlers, composable rules, permissions, DI, and middleware.
- **Stateful workflows**: memory, JSON, and SQLite state stores plus event-scoped session waiters.
- **Operational controls**: configuration validation, versioned JSON Schema, health and metrics views, audit events, and management commands.
- **Safe development loop**: plugin/config hot reload with rollback when the replacement fails.
- **Agent building blocks**: OpenAI-compatible model calls, tool metadata, approval hooks, traces, and output guardrails.
- **Stable contracts**: versioned serialization, lifecycle, configuration, deprecation, and extension conformance rules.

---

## Quick Start

### Install the latest stable package

```bash
python -m pip install iamai
```

The `dev` branch may be ahead of the latest PyPI release. To run the repository examples against the current source:

```bash
git clone https://github.com/retrofor/iamai.git
cd iamai
uv sync --locked --all-packages --group dev

# Validate the complete runtime configuration before starting it.
uv run --package echo-runtime iamai \
  --config examples/echo-runtime/config.terminal.toml config-check

# Start the local TerminalAdapter example.
uv run --package echo-runtime iamai \
  --config examples/echo-runtime/config.terminal.toml
```

At the prompt, enter:

```text
/echo hello iamai
```

### Write a plugin

```python
from iamai import Context, Plugin, command


class HelloPlugin(Plugin):
    name = "hello"

    @command("hello")
    async def hello(self, ctx: Context) -> None:
        await ctx.reply("Hello from iamai.")
```

Add the plugin import path to `[runtime].plugins`, run `config-check`, and restart the runtime. The [quickstart](https://github.com/retrofor/iamai/blob/dev/docs/quickstart.rst) follows this path from configuration to the first reply.

---

## Adapters

| Adapter | Transport | Typical use |
|---|---|---|
| `TerminalAdapter` | stdin / stdout | Local development and deterministic testing |
| `OneBot11Adapter` | HTTP, WebSocket, reverse WebSocket | QQ ecosystems such as Lagrange and LLOneBot |
| `TelegramAdapter` | Long polling | Telegram bots |
| `WebhookAdapter` | HTTP POST with optional signature checks | Generic webhooks and service integrations |
| Custom adapter | Any protocol | Subclass `Adapter`; implement `start()` and `send_message()`, then override `close()` when cleanup is required |

Adapters own the network and trust boundary. The [adapter guide](https://github.com/retrofor/iamai/blob/dev/docs/guides/adapters.rst) covers authentication, payload normalization, outbound calls, and production constraints.

---

## Agent Building Blocks

iamai includes small, composable primitives for agent-style plugins. They are optional and do not change the core runtime model.

| Component | Purpose |
|---|---|
| `LLMClient` | Async OpenAI-compatible text and JSON calls; live calls require the optional `openai` package |
| `ToolRegistry` | Named tools with input schema, permission name, approval requirement, and audit fields |
| `AgentTrace` | Append-only model/tool/observation records with JSON serialization |
| `Guardrail` | Case-normalized substring checks for blocked output |
| `LLMConfig` | TOML/environment configuration for endpoint, model, credentials, temperature, token limit, and timeout |

Runnable patterns live in the repository:

| Pattern | What it demonstrates | Example |
|---|---|---|
| ReAct | Tool selection, observations, memory, and trace inspection | [`react-runtime`](https://github.com/retrofor/iamai/tree/dev/examples/react-runtime) |
| Planner-Executor | Structured planning followed by staged execution | [`planner-executor-runtime`](https://github.com/retrofor/iamai/tree/dev/examples/planner-executor-runtime) |
| Supervisor-Team | Role-specialized workers coordinated by a supervisor | [`supervisor-team-runtime`](https://github.com/retrofor/iamai/tree/dev/examples/supervisor-team-runtime) |
| Skill Chat | Tool/skill routing in a conversational runtime | [`skill-chat-runtime`](https://github.com/retrofor/iamai/tree/dev/examples/skill-chat-runtime) |

See the [agent runtime guide](https://github.com/retrofor/iamai/blob/dev/docs/guides/agent-runtime.rst) for dependency and security boundaries.

---

## Extensions and Contracts

Third-party packages can publish `iamai.plugins` and `iamai.adapters` entry points. The runtime provides deterministic discovery errors, versioned configuration schemas, secret annotations, and conformance helpers for independently distributed extensions.

The 1.x compatibility surface is documented rather than implied:

- [Extension packaging and discovery](https://github.com/retrofor/iamai/blob/dev/docs/reference/extensions.rst)
- [Serialization contract](https://github.com/retrofor/iamai/blob/dev/docs/reference/serialization-contract.rst)
- [Lifecycle contract](https://github.com/retrofor/iamai/blob/dev/docs/reference/public-api-lifecycle.rst)
- [Public API conformance matrix](https://github.com/retrofor/iamai/blob/dev/docs/reference/public-api-conformance.rst)
- [0.3 to 1.0 migration guide](https://github.com/retrofor/iamai/blob/dev/docs/guides/migration-0.3-to-1.0.rst)

---

## Examples and Documentation

| Resource | Start here when you want to... |
|---|---|
| [Quickstart](https://github.com/retrofor/iamai/blob/dev/docs/quickstart.rst) | Validate a config and run the terminal example |
| [Tutorials](https://github.com/retrofor/iamai/tree/dev/docs/tutorials) | Build a runtime step by step |
| [Guides](https://github.com/retrofor/iamai/tree/dev/docs/guides) | Design plugins, adapters, state, operations, and agents |
| [API reference](https://github.com/retrofor/iamai/tree/dev/docs/api) | Inspect public Python classes and functions |
| [`examples/`](https://github.com/retrofor/iamai/tree/dev/examples) | Run complete local projects and agent patterns |
| [Ecosystem comparison](https://github.com/retrofor/iamai/blob/dev/docs/guides/ecosystem-comparison.rst) | Understand where iamai fits and what it intentionally does not replace |

---

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

Open pull requests against `dev`. Keep runtime behavior covered by tests and update the relevant contract documentation when changing a public boundary. See [GitHub Issues](https://github.com/retrofor/iamai/issues) and [Discussions](https://github.com/retrofor/iamai/discussions) for active work.

---

## License

[MIT](https://github.com/retrofor/iamai/blob/dev/LICENSE) © iamai contributors

## Acknowledgments

iamai draws lessons from [NoneBot](https://github.com/nonebot/nonebot2), [Koishi](https://github.com/koishijs/koishi), and [AliceBot](https://github.com/AliceBotProject/alicebot). Its agent examples are informed by the [ReAct paper](https://arxiv.org/abs/2210.03629) and the wider agent-runtime community.
