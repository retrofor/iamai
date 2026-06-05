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
  <strong>跨平台聊天机器人框架，内置 AI Agent 支持。Rust 核心，Python 插件。</strong>
</p>

<p align="center">
  <a href="https://github.com/retrofor/iamai/blob/main/README.md">English</a>
</p>

---

## 概览

iamai 是一个基于 Rust 和 Python 的跨平台聊天机器人框架。高性能的消息引擎由 Rust 实现（通过 PyO3 打包），插件系统使用 Python，同时内置了构建 LLM Agent 所需的基础组件。

架构采用三层模式：**Adapter**（平台协议适配）、**Runtime**（插件编排调度）和 **Plugin**（业务逻辑）。适配器将不同平台的协议差异归一化为统一的 `Event`、`Message` 和 `Context` 对象，插件只需编写一次即可跨平台部署。

---

## AI Agent 支持

iamai 在核心包中直接提供了 Agent 基础组件，无需额外安装 SDK 或集成第三方库。

| 组件 | 说明 |
|-----------|-------------|
| `LLMClient` | 异步 OpenAI 兼容客户端，提供 `chat_text()` 和 `chat_json()` 方法。支持通过 TOML 配置或环境变量设置。内置 Mock 模式（`IAMAI_LLM_MOCK=1`），在测试时返回确定性响应，无需实际调用 API。 |
| `ToolRegistry` | 命名工具注册表，支持 `input_schema`、`permission_name`、`requires_approval` 和 `audit_fields`。提供可选的审批回调机制，用于需要人工确认的操作。 |
| `AgentTrace` | 追加式追踪记录，记录每次模型调用、工具调用和观察结果。可序列化为 JSON，为内置 `/trace` 管理命令提供数据支持。 |
| `Guardrail` | Token 级别的输出过滤器，拦截配置的敏感字符串并在匹配时抛出异常。 |
| `LLMConfig` | 统一配置对象，从 TOML 配置文件或 `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL` 环境变量读取。 |

### Agent 模式示例

`examples/` 目录下包含可直接运行的 Agent 项目，展示了不同的编排模式：

**ReAct** — [`examples/react-runtime`](examples/react-runtime)

经典的 think-act-observe 循环模式。LLM 在每轮决定是调用工具还是返回最终答案。包含沙箱化工具（数学计算使用 AST 安全求值，笔记使用关键词搜索）、可配置的轮次上限和追踪查看功能。

```bash
export OPENAI_API_KEY="sk-..."
uv run --package react-runtime python -m iamai --config examples/react-runtime/config.terminal.toml
```

**Planner-Executor** — [`examples/planner-executor-runtime`](examples/planner-executor-runtime)

两阶段流水线：Planner（低温度）产出包含步骤和交付物的结构化计划；Executor（较高温度）逐步执行并生成总结。执行历史会被保存，供后续会话参考。

```bash
uv run --package planner-executor-runtime python -m iamai --config examples/planner-executor-runtime/config.terminal.toml
```

**Supervisor-Team** — [`examples/supervisor-team-runtime`](examples/supervisor-team-runtime)

Supervisor-Worker 模式：Supervisor 分解目标，将子任务分派给不同角色的 Worker（strategist、builder、skeptic），每个 Worker 有固定的 persona 提示词，最后 Supervisor 综合结果。

```bash
uv run --package supervisor-team-runtime python -m iamai --config examples/supervisor-team-runtime/config.terminal.toml
```

> 更多示例见 [`examples/`](examples/)：群聊助手、人生模拟、角色扮演等。

---

## 适配器

适配器负责处理网络通信、鉴权和协议转换。插件只操作归一化后的对象——编写一次，即可在不同平台上运行。

| 适配器 | 协议 | 典型用途 |
|---------|----------|-------------|
| `TerminalAdapter` | stdin/stdout | 本地开发和调试 |
| `OneBot11Adapter` | WS / WS-Reverse / HTTP | QQ、Lagrange、LLOneBot |
| `TelegramAdapter` | Long polling | Telegram 机器人 |
| `WebhookAdapter` | HTTP POST | 钉钉、飞书、企业微信及通用 webhook |
| 自定义 | 任意 | 继承 `Adapter` 并实现 `start()` / `send()` |

---

## 快速开始

### 安装

```bash
pip install iamai
```

### 运行示例

```bash
git clone https://github.com/retrofor/iamai.git && cd iamai
uv sync

# 终端 echo bot（无需 API key）
uv run python -m iamai --config examples/echo-runtime/config.terminal.toml

# ReAct agent（需要 OPENAI_API_KEY）
export OPENAI_API_KEY="sk-..."
uv run --package react-runtime python -m iamai --config examples/react-runtime/config.terminal.toml
```

### 编写插件

```python
from iamai import Plugin, command

class MyPlugin(Plugin):
    @command("hello")
    async def handle(self, ctx):
        await ctx.reply("Hello from iamai!")
```

插件支持 `@command`、`@message_handler`、`@event_handler`，支持中间件（`before` / `around` / `after` / `error`），以及通过类型注解或 `depends()` 实现的依赖注入。

---

## 框架对比

|   | iamai | NoneBot | Koishi | LangChain |
|---|-------|---------|--------|-----------|
| Agent 运行时 | 内置 | — | — | 核心 |
| Bot 框架 | 内置 | 核心 | 核心 | — |
| 插件模型 | 装饰器 + DI | 装饰器 + DI | Hook + Service | — |
| 热重载 | 文件监听自动重载 | — | 插件级 | — |
| 核心语言 | Rust (PyO3) + Python | Python | TypeScript | Python |
| 安装方式 | `pip install iamai` | `pip install nonebot2` | `npm install koishi` | `pip install langchain` |

---

## 文档

- **[iamai.readthedocs.io](https://iamai.readthedocs.io)** — 安装、概念、快速开始、教程和 API 参考
- **[examples/](examples/)** — echo、arcade、ReAct、Planner-Executor、Supervisor-Team、群聊助手等
- **[docs/](docs/)** — Sphinx 文档源文件

---

## 社区与贡献

- **Issue**: [GitHub Issues](https://github.com/retrofor/iamai/issues)
- **Pull Request**: fork → 特性分支 → PR 到 `main`。提交前请运行 `ruff check` 和 `pytest`
- **讨论**: [GitHub Discussions](https://github.com/retrofor/iamai/discussions)

---

## 开源协议

[MIT](LICENSE)

---

## 致谢

iamai 的设计受益于 [NoneBot](https://github.com/nonebot/nonebot2)（分层架构）、[Koishi](https://github.com/koishijs/koishi)（适配器即插件）和 [AliceBot](https://github.com/AliceBotProject/alicebot)（简洁优先）。Agent 模式参考了 [ReAct 论文](https://arxiv.org/abs/2210.03629) 及 LLM Agent 研究社区。
