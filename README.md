<p align="center">
  <img src="docs/_static/brand/iamai-logo-wide.svg" alt="iamai" width="640">
</p>

<p align="center">
  <a href="https://pypi.org/project/iamai/"><img src="https://img.shields.io/pypi/v/iamai?color=blue" alt="PyPI"></a>
  <a href="https://pypi.org/project/iamai/"><img src="https://img.shields.io/pypi/pyversions/iamai" alt="Python"></a>
  <a href="https://github.com/retrofor/iamai/blob/main/Cargo.toml"><img src="https://img.shields.io/badge/rust-edition%202024-orange" alt="Rust"></a>
  <a href="https://github.com/retrofor/iamai/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
  <a href="https://github.com/retrofor/iamai/actions/workflows/check.yml"><img src="https://github.com/retrofor/iamai/actions/workflows/check.yml/badge.svg" alt="CI"></a>
  <a href="https://iamai.readthedocs.io/"><img src="https://readthedocs.org/projects/iamai/badge/?version=latest" alt="Docs"></a>
</p>

<p align="center">
  <strong>Rust + Python 跨平台聊天机器人框架。写插件，接平台，一步到位。</strong>
</p>

---

**iamai** 是一个面向插件开发和多平台接入的聊天机器人运行时框架。它用 **Rust** 构建高性能的消息链和协议归一化层，用 **Python** 提供灵活的插件系统和运行时编排，通过 PyO3 打包成一个 Python 包，`pip install` 即可使用。

> 设计上借鉴了 NoneBot 的分层架构、Koishi 的适配器插件化理念，同时保持了轻量、直接、易上手的开发体验。

---

## ✨ 为什么选择 iamai

|   | iamai | NoneBot | Koishi |
|---|-------|---------|--------|
| 语言 | Python + Rust 核心 | Python | TypeScript |
| 插件模型 | 装饰器 + 依赖注入 | 装饰器 + 依赖注入 | 钩子 + 服务 |
| 适配器 | Terminal / OneBot11 / Webhook / 自定义 | OneBot11 / Telegram / 等 | 丰富的官方适配器 |
| 热重载 | ✅ 文件监听自动重载 | ❌ | ✅ |
| Agent 运行时 | ✅ 内置 LLMClient / ToolRegistry / Guardrail | ❌ | ❌ |
| 持久化状态 | ✅ SQLite / JSON | ❌ | ✅ |
| 性能核心 | Rust (PyO3) | Pure Python | Node.js |

**核心卖点：**

- **多平台，一套代码** — 终端调通了，切到 OneBot11 或 Webhook 只改配置文件，插件代码不动。
- **Python 写业务，Rust 跑引擎** — 消息链解析、协议归一化、配置合并这些脏活在 Rust 层完成，插件只关心 `Event`、`Message`、`Context`。
- **Agent 开箱即用** — 内置 `LLMClient`、`ToolRegistry`、`AgentTrace`、`Guardrail`，ReAct / Planner-Executor / Supervisor 等模式都有可运行的示例。
- **热重载 & 依赖注入** — 改插件代码自动重载，中间件和 handler 通过类型注解自动注入依赖，开发体验流畅。

---

## 🚀 快速开始

```bash
# 安装
pip install iamai

# 从示例模板初始化项目
git clone https://github.com/retrofor/iamai.git && cd iamai
uv sync
uv run python -m iamai --config examples/echo-runtime/config.terminal.toml
```

终端输入任意文字，bot 会原样回复。一个最小插件长这样：

```python
# plugin_echo.py
from iamai import Plugin, command

class Echo(Plugin):
    @command("echo")
    async def handle(self, ctx):
        await ctx.reply(f"你说: {ctx.message}")
```

切到 OneBot11 只需换配置文件：

```bash
uv run python -m iamai --config examples/echo-runtime/config.onebot11-ws-reverse.toml
```

---

## 🧩 适配器生态

| 适配器 | 协议 | 适用场景 |
|--------|------|----------|
| `TerminalAdapter` | stdin/stdout | 本地开发调试 |
| `OneBot11Adapter` | WS / WS-Reverse / HTTP | QQ、Lagrange、LLOneBot 等 |
| `WebhookAdapter` | HTTP POST | 通用 webhook（钉钉、飞书、企业微信……） |
| 自定义适配器 | 任意 | 继承 `Adapter` 基类，实现 `start()` / `send()` |

> 适配器负责网络、鉴权、协议转换和重连；插件只操作统一的 `Event` / `Message` / `Context`，与具体平台无关。

---

## 🏗️ 架构概览

```text
┌──────────────────────────────────────────────┐
│                 Python Plugins                │
│  @command / @message_handler / @event_handler │
│         Middleware / Dependency Injection      │
├──────────────────────────────────────────────┤
│              Runtime & Adapter Layer           │
│   Plugin loader · Hot reload · State · Config │
│   TerminalAdapter · OneBot11 · Webhook · …   │
├──────────────────────────────────────────────┤
│             Rust Core (_core)                 │
│   MessageChain · Event normalization          │
│   Config deep-merge · Protocol serialization  │
└──────────────────────────────────────────────┘
```

---

## 📚 文档 & 示例

- **文档站**: [iamai.readthedocs.io](https://iamai.readthedocs.io) — 安装 → 概念 → 快速开始 → 教程 → 指南 → API 参考
- **本地构建**: `uv sync --group docs && uv run sphinx-build -b html docs docs/_build/html`

| 示例 | 说明 |
|------|------|
| [`echo-runtime`](examples/echo-runtime) | 最小样板，一键接入终端 / OneBot11 / Webhook |
| [`arcade-runtime`](examples/arcade-runtime) | 多插件协作、middleware、排行榜 |
| [`react-runtime`](examples/react-runtime) | ReAct agent loop，工具调用与错误收敛 |
| [`planner-executor-runtime`](examples/planner-executor-runtime) | Planner / Executor 多 agent 协作 |
| [`supervisor-team-runtime`](examples/supervisor-team-runtime) | Supervisor + specialists 多角色模式 |
| [更多...](examples/) | 群聊助手、人生模拟、角色扮演等 |

---

## 🤝 社区 & 贡献

欢迎提交 Issue、PR，或把你的插件/适配器发布到社区生态。

- **Bug 报告 & 功能请求**: [GitHub Issues](https://github.com/retrofor/iamai/issues)
- **代码贡献**: Fork → Feature Branch → PR 到 `main`，确保 `ruff check` 和 `pytest` 通过
- **文档贡献**: 文档源在 `docs/`，使用 Sphinx + RST，欢迎完善教程和翻译

---

## 📄 开源协议

[MIT](LICENSE)

---

## 🙏 致谢

iamai 的设计深受以下项目启发：

- [NoneBot](https://github.com/nonebot/nonebot2) — Python 聊天机器人框架
- [Koishi](https://github.com/koishijs/koishi) — TypeScript 跨平台机器人框架
- [AliceBot](https://github.com/AliceBotProject/alicebot) — 轻量 Python 机器人框架

---

---

<p align="center">
  <img src="docs/_static/brand/iamai-logo-wide.svg" alt="iamai" width="640">
</p>

<p align="center">
  <a href="https://pypi.org/project/iamai/"><img src="https://img.shields.io/pypi/v/iamai?color=blue" alt="PyPI"></a>
  <a href="https://pypi.org/project/iamai/"><img src="https://img.shields.io/pypi/pyversions/iamai" alt="Python"></a>
  <a href="https://github.com/retrofor/iamai/blob/main/Cargo.toml"><img src="https://img.shields.io/badge/rust-edition%202024-orange" alt="Rust"></a>
  <a href="https://github.com/retrofor/iamai/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
  <a href="https://github.com/retrofor/iamai/actions/workflows/check.yml"><img src="https://github.com/retrofor/iamai/actions/workflows/check.yml/badge.svg" alt="CI"></a>
  <a href="https://iamai.readthedocs.io/"><img src="https://readthedocs.org/projects/iamai/badge/?version=latest" alt="Docs"></a>
</p>

<p align="center">
  <strong>A Rust + Python cross-platform chatbot framework — write plugins, connect platforms, done.</strong>
</p>

---

**iamai** is a plugin-oriented chatbot runtime framework. Its high-performance message chain and protocol normalization layer are built in **Rust**, while the flexible plugin system and runtime orchestration are in **Python**. The whole thing ships as a single Python package via PyO3 — `pip install` and go.

> Inspired by NoneBot's layered architecture and Koishi's adapter-as-plugin philosophy, with a focus on keeping things lightweight and developer-friendly.

---

## ✨ Why iamai

|   | iamai | NoneBot | Koishi |
|---|-------|---------|--------|
| Language | Python + Rust core | Python | TypeScript |
| Plugin model | Decorator + DI | Decorator + DI | Hook + Service |
| Adapters | Terminal / OneBot11 / Webhook / custom | OneBot11 / Telegram / etc. | Rich official adapters |
| Hot reload | ✅ File-watch auto reload | ❌ | ✅ |
| Agent runtime | ✅ Built-in LLMClient / ToolRegistry / Guardrail | ❌ | ❌ |
| Persistent state | ✅ SQLite / JSON | ❌ | ✅ |
| Performance core | Rust (PyO3) | Pure Python | Node.js |

---

## 🚀 Quick Start

```bash
pip install iamai

# Clone and run the echo example
git clone https://github.com/retrofor/iamai.git && cd iamai
uv sync
uv run python -m iamai --config examples/echo-runtime/config.terminal.toml
```

Type anything and the bot replies back. A minimal plugin:

```python
from iamai import Plugin, command

class Echo(Plugin):
    @command("echo")
    async def handle(self, ctx):
        await ctx.reply(f"You said: {ctx.message}")
```

---

## 🧩 Adapters

| Adapter | Protocol | Use case |
|---------|----------|----------|
| `TerminalAdapter` | stdin/stdout | Local dev & debug |
| `OneBot11Adapter` | WS / WS-Reverse / HTTP | QQ, Lagrange, LLOneBot |
| `WebhookAdapter` | HTTP POST | DingTalk, Feishu, WeCom, etc. |
| Custom adapter | Any | Extend `Adapter` base class |

> Adapters handle networking, auth, protocol translation, and reconnection. Plugins only deal with unified `Event` / `Message` / `Context` objects — platform-agnostic.

---

## 📚 Docs & Community

- **Documentation**: [iamai.readthedocs.io](https://iamai.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/retrofor/iamai/issues)
- **License**: [MIT](LICENSE)

---


## 🙏 Acknowledgments

Inspired by [NoneBot](https://github.com/nonebot/nonebot2), [Koishi](https://github.com/koishijs/koishi), and [AliceBot](https://github.com/AliceBotProject/alicebot).
