<p align="center">
  <img src="docs/_static/brand/iamai-logo-wide.svg" alt="iamai" width="640">
</p>

<p align="center">
  <a href="https://pypi.org/project/iamai/"><img src="https://img.shields.io/pypi/v/iamai?color=blue" alt="PyPI"></a>
  <a href="https://pypi.org/project/iamai/"><img src="https://img.shields.io/pypi/pyversions/iamai" alt="Python"></a>
  <a href="https://github.com/retrofor/iamai/blob/main/Cargo.toml"><img src="https://img.shields.io/badge/core-rust%20%2B%20pyo3-orange" alt="Rust"></a>
  <a href="https://github.com/retrofor/iamai/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
  <a href="https://github.com/retrofor/iamai/actions/workflows/check.yml"><img src="https://github.com/retrofor/iamai/actions/workflows/check.yml/badge.svg" alt="CI"></a>
  <a href="https://iamai.readthedocs.io/"><img src="https://readthedocs.org/projects/iamai/badge/?version=latest" alt="Docs"></a>
</p>

<p align="center">
  <strong>A cross-platform chatbot framework with native AI agent support. Rust core, Python plugins.</strong>
</p>

<p align="center">
  <a href="https://github.com/retrofor/iamai/blob/main/README.zh.md">中文文档</a>
</p>

---

## Overview

iamai is a cross-platform chatbot framework built on Rust and Python. It combines a high-performance message engine (Rust, via PyO3) with a flexible plugin system (Python), and includes built-in primitives for building LLM-powered agents.

The architecture follows a three-layer pattern: **Adapter** (platform protocol), **Runtime** (plugin orchestration), and **Plugin** (business logic). Adapters normalize platform-specific payloads into unified `Event`, `Message`, and `Context` objects, so plugins can be written once and deployed across multiple platforms.

---

## AI Agent Support

iamai ships with agent primitives in the core package — no additional SDKs or integrations required.

| Component | Description |
|-----------|-------------|
| `LLMClient` | Async OpenAI-compatible client with `chat_text()` and `chat_json()` methods. Configurable via TOML or environment variables. Supports a mock mode (`IAMAI_LLM_MOCK=1`) that returns deterministic responses for testing. |
| `ToolRegistry` | Named tool registry supporting `input_schema`, `permission_name`, `requires_approval`, and `audit_fields`. Includes an optional approval callback for human-in-the-loop workflows. |
| `AgentTrace` | Append-only trace recording each model call, tool invocation, and observation. Serializable to JSON. Powers the built-in `/trace` management command. |
| `Guardrail` | Token-level output filter. Blocks configured substrings and raises on match. |
| `LLMConfig` | Unified configuration object, read from TOML config or `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL` environment variables. |

### Agent Patterns (Examples)

The `examples/` directory contains runnable agent projects demonstrating different orchestration patterns:

**ReAct** — [`examples/react-runtime`](examples/react-runtime)

A think-act-observe loop with tool calling. The LLM decides at each turn whether to invoke a tool or return a final answer. Includes sandboxed tools (math via AST eval, keyword-search notes), a configurable turn limit, and trace inspection.

```bash
export OPENAI_API_KEY="sk-..."
uv run --package react-runtime python -m iamai --config examples/react-runtime/config.terminal.toml
```

**Planner-Executor** — [`examples/planner-executor-runtime`](examples/planner-executor-runtime)

A two-stage pipeline: the planner (low temperature) produces a structured plan with steps and deliverables; the executor (higher temperature) executes each step and produces a summary. Run history is stored for context across sessions.

```bash
uv run --package planner-executor-runtime python -m iamai --config examples/planner-executor-runtime/config.terminal.toml
```

**Supervisor-Team** — [`examples/supervisor-team-runtime`](examples/supervisor-team-runtime)

A supervisor-worker pattern: the supervisor decomposes a goal, dispatches to role-specialized workers (strategist, builder, skeptic) with fixed persona prompts, then synthesizes the results.

```bash
uv run --package supervisor-team-runtime python -m iamai --config examples/supervisor-team-runtime/config.terminal.toml
```

> More examples: group assistant, life simulator, persona role-play, and others in [`examples/`](examples/).

---

## Adapters

Adapters handle networking, authentication, and protocol conversion. Plugins interact only with normalized objects — write once, deploy on any supported platform.

| Adapter | Protocol | Typical Use |
|---------|----------|-------------|
| `TerminalAdapter` | stdin/stdout | Local development and debugging |
| `OneBot11Adapter` | WS / WS-Reverse / HTTP | QQ, Lagrange, LLOneBot |
| `TelegramAdapter` | Long polling | Telegram bots |
| `WebhookAdapter` | HTTP POST | DingTalk, Feishu, WeCom, and generic webhooks |
| Custom | Any | Subclass `Adapter` and implement `start()` / `send()` |

---

## Quick Start

### Installation

```bash
pip install iamai
```

### Running the examples

```bash
git clone https://github.com/retrofor/iamai.git && cd iamai
uv sync

# Terminal echo bot (no API key required)
uv run python -m iamai --config examples/echo-runtime/config.terminal.toml

# ReAct agent (requires OPENAI_API_KEY)
export OPENAI_API_KEY="sk-..."
uv run --package react-runtime python -m iamai --config examples/react-runtime/config.terminal.toml
```

### Writing a plugin

```python
from iamai import Plugin, command

class MyPlugin(Plugin):
    @command("hello")
    async def handle(self, ctx):
        await ctx.reply("Hello from iamai!")
```

Plugins support `@command`, `@message_handler`, `@event_handler`, middleware (`before` / `around` / `after` / `error`), and dependency injection via type annotations or `depends()`.

---

## Comparison

|   | iamai | NoneBot | Koishi | LangChain |
|---|-------|---------|--------|-----------|
| Agent runtime | Built-in | — | — | Core focus |
| Bot framework | Built-in | Core focus | Core focus | — |
| Plugin model | Decorator + DI | Decorator + DI | Hook + Service | — |
| Hot reload | File-watch auto reload | — | Plugin-level | — |
| Core language | Rust (PyO3) + Python | Python | TypeScript | Python |
| Package | `pip install iamai` | `pip install nonebot2` | `npm install koishi` | `pip install langchain` |

---

## Documentation

- **[iamai.readthedocs.io](https://iamai.readthedocs.io)** — installation, concepts, quickstart, tutorials, and API reference
- **[examples/](examples/)** — echo, arcade, ReAct, Planner-Executor, Supervisor-Team, group assistant, and more
- **[docs/](docs/)** — Sphinx documentation source

---

## Community & Contributing

- **Issues**: [GitHub Issues](https://github.com/retrofor/iamai/issues)
- **Pull Requests**: fork → feature branch → PR to `main`. Run `ruff check` and `pytest` before submitting.
- **Discussions**: [GitHub Discussions](https://github.com/retrofor/iamai/discussions)

---

## License

[MIT](LICENSE)

---

## Acknowledgments

iamai is inspired by [NoneBot](https://github.com/nonebot/nonebot2) (layered architecture), [Koishi](https://github.com/koishijs/koishi) (adapter-as-plugin design), and [AliceBot](https://github.com/AliceBotProject/alicebot) (simplicity-first approach). Agent patterns are informed by the [ReAct paper](https://arxiv.org/abs/2210.03629) and the broader LLM agent research community.
