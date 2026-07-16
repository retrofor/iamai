<p align="center">
  <img src="https://raw.githubusercontent.com/retrofor/iamai/92336af67d4af6e288caa845b88bf2d26a17a9b2/docs/_static/brand/iamai-logo.svg" alt="iamai runtime mark" width="128">
</p>

<h1 align="center">iamai</h1>

<p align="center">
  <em>面向跨平台消息、插件与可审计 AI Agent 的轻量 Python + Rust 运行时。</em>
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
  <a href="https://github.com/retrofor/iamai/blob/dev/README.md">English</a> · <b>中文</b>
</p>

---

## iamai 是什么

**iamai** 是一个面向聊天机器人、事件驱动应用和轻量 AI Agent 的开源运行时。它把平台协议留在系统边缘，让业务逻辑保持为普通的异步 Python 插件。

Adapter 将终端、WebSocket、HTTP、Telegram 和 OneBot payload 归一化为稳定的 `Event`、`Message` 与 `Context` 对象。Runtime 负责扩展发现、生命周期、事件分发、规则、权限、依赖注入、中间件、状态、会话和可观测性。部分消息与归一化能力通过 PyO3 运行在 Rust 扩展中。

iamai 的定位是运行时，而不是大而全的 Agent 平台。你可以使用内置 Agent 组件，也可以替换它们，或者完全不接入 LLM。

---

## 工作原理

```text
外部平台
  -> Adapter 校验并归一化 payload
  -> Runtime 匹配 handler，并执行 Rule + Permission + DI
  -> Plugin 在事件作用域的 Context 中运行
  -> Context.reply() 把回复委托回 Adapter
```

| 分层 | 职责 | 源码 |
|---|---|---|
| **Adapter** | 网络、鉴权、验签、协议转换和出站 API | [`python/iamai/adapters`](https://github.com/retrofor/iamai/tree/dev/python/iamai/adapters) |
| **Runtime** | 配置、扩展发现、生命周期、分发、DI、中间件、状态、会话和热重载 | [`python/iamai`](https://github.com/retrofor/iamai/tree/dev/python/iamai) |
| **Plugin** | 命令、消息/事件 handler、规则、权限和业务行为 | [`examples`](https://github.com/retrofor/iamai/tree/dev/examples) |
| **Rust core** | 消息链操作、OneBot 归一化和 JSON 合并辅助函数 | [`src`](https://github.com/retrofor/iamai/tree/dev/src) |

完整的准入、中间件、热重载和关闭语义见[架构指南](https://github.com/retrofor/iamai/blob/dev/docs/guides/architecture.rst)。

---

## 功能

- **协议无关的插件**：只依赖 `Event`、`Message` 和 `Context`，不把平台 payload 写进业务逻辑。
- **明确的扩展模型**：通过导入路径或标准 Python entry point 加载插件和适配器。
- **结构化分发**：命令、消息 handler、事件 handler、可组合规则、权限、DI 和中间件。
- **有状态工作流**：内存、JSON、SQLite 状态后端，以及事件作用域的 Session waiter。
- **运维入口**：配置校验、版本化 JSON Schema、健康与指标视图、审计事件和管理命令。
- **可靠开发循环**：插件/配置热重载；替换失败时回滚到旧运行状态。
- **Agent 基础组件**：OpenAI 兼容模型调用、工具元数据、审批钩子、trace 和输出 guardrail。
- **稳定合同**：版本化的序列化、生命周期、配置、弃用和扩展 conformance 规则。

---

## 快速开始

### 安装最新稳定版

```bash
python -m pip install iamai
```

`dev` 分支可能领先于 PyPI 最新稳定版。要使用当前源码运行仓库示例：

```bash
git clone https://github.com/retrofor/iamai.git
cd iamai
uv sync --locked --all-packages --group dev

# 启动前先校验完整 Runtime 配置。
uv run --package echo-runtime iamai \
  --config examples/echo-runtime/config.terminal.toml config-check

# 启动本地 TerminalAdapter 示例。
uv run --package echo-runtime iamai \
  --config examples/echo-runtime/config.terminal.toml
```

出现提示符后输入：

```text
/echo hello iamai
```

### 编写插件

```python
from iamai import Context, Plugin, command


class HelloPlugin(Plugin):
    name = "hello"

    @command("hello")
    async def hello(self, ctx: Context) -> None:
        await ctx.reply("Hello from iamai.")
```

把插件导入路径加入 `[runtime].plugins`，执行 `config-check`，再重新启动 Runtime。[快速开始](https://github.com/retrofor/iamai/blob/dev/docs/quickstart.rst)会从配置校验一直走到第一次回复。

---

## 适配器

| 适配器 | 传输方式 | 典型用途 |
|---|---|---|
| `TerminalAdapter` | stdin / stdout | 本地开发和确定性测试 |
| `OneBot11Adapter` | HTTP、WebSocket、反向 WebSocket | QQ 生态，例如 Lagrange 和 LLOneBot |
| `TelegramAdapter` | Long polling | Telegram 机器人 |
| `WebhookAdapter` | HTTP POST（可选签名校验） | 通用 webhook 和服务集成 |
| 自定义 Adapter | 任意协议 | 继承 `Adapter`，实现 `start()` 和 `send_message()`；需要资源清理时再重写 `close()` |

Adapter 拥有网络和信任边界。[适配器指南](https://github.com/retrofor/iamai/blob/dev/docs/guides/adapters.rst)介绍鉴权、payload 归一化、出站调用和生产约束。

---

## Agent 基础组件

iamai 提供一组小型、可组合的 Agent 组件。它们是可选能力，不会改变核心 Runtime 模型。

| 组件 | 用途 |
|---|---|
| `LLMClient` | 异步 OpenAI 兼容文本/JSON 调用；真实请求需要可选的 `openai` 包 |
| `ToolRegistry` | 带输入 schema、权限名、审批要求和审计字段的命名工具 |
| `AgentTrace` | 可序列化为 JSON 的追加式模型/工具/观察记录 |
| `Guardrail` | 大小写归一后的输出子字符串检查 |
| `LLMConfig` | 通过 TOML/环境变量配置 endpoint、模型、凭据、temperature、token 上限和超时 |

仓库提供了可运行的 Agent 模式：

| 模式 | 展示内容 | 示例 |
|---|---|---|
| ReAct | 工具选择、观察、记忆和 trace 查看 | [`react-runtime`](https://github.com/retrofor/iamai/tree/dev/examples/react-runtime) |
| Planner-Executor | 结构化规划与分阶段执行 | [`planner-executor-runtime`](https://github.com/retrofor/iamai/tree/dev/examples/planner-executor-runtime) |
| Supervisor-Team | Supervisor 协调不同职责的 Worker | [`supervisor-team-runtime`](https://github.com/retrofor/iamai/tree/dev/examples/supervisor-team-runtime) |
| Skill Chat | 会话 Runtime 中的工具/技能路由 | [`skill-chat-runtime`](https://github.com/retrofor/iamai/tree/dev/examples/skill-chat-runtime) |

依赖和安全边界见 [Agent Runtime 指南](https://github.com/retrofor/iamai/blob/dev/docs/guides/agent-runtime.rst)。

---

## 扩展与合同

第三方包可以发布 `iamai.plugins` 和 `iamai.adapters` entry point。Runtime 为独立分发的扩展提供确定性的发现错误、版本化配置 Schema、secret 标记和 conformance helpers。

1.x 兼容边界有明确文档，而不是依赖隐式约定：

- [扩展打包与发现](https://github.com/retrofor/iamai/blob/dev/docs/reference/extensions.rst)
- [序列化合同](https://github.com/retrofor/iamai/blob/dev/docs/reference/serialization-contract.rst)
- [生命周期合同](https://github.com/retrofor/iamai/blob/dev/docs/reference/public-api-lifecycle.rst)
- [公共 API conformance matrix](https://github.com/retrofor/iamai/blob/dev/docs/reference/public-api-conformance.rst)
- [0.3 到 1.0 迁移指南](https://github.com/retrofor/iamai/blob/dev/docs/guides/migration-0.3-to-1.0.rst)

---

## 示例与文档

| 资源 | 适合从这里开始的场景 |
|---|---|
| [快速开始](https://github.com/retrofor/iamai/blob/dev/docs/quickstart.rst) | 校验配置并运行终端示例 |
| [渐进式教程](https://github.com/retrofor/iamai/tree/dev/docs/tutorials) | 从零逐步构建 Runtime |
| [开发指南](https://github.com/retrofor/iamai/tree/dev/docs/guides) | 设计插件、适配器、状态、运维和 Agent |
| [API 参考](https://github.com/retrofor/iamai/tree/dev/docs/api) | 查看公开 Python 类与函数 |
| [`examples/`](https://github.com/retrofor/iamai/tree/dev/examples) | 运行完整本地项目和 Agent 模式 |
| [生态对比](https://github.com/retrofor/iamai/blob/dev/docs/guides/ecosystem-comparison.rst) | 理解 iamai 的定位及其刻意不替代的领域 |

---

## 开发

```bash
uv sync --locked --all-packages --group dev --group docs
uv run ruff check .
uv run python -m mypy
uv run pytest
cargo test --no-default-features
bash scripts/check_example_configs.sh
uv run sphinx-build -W --keep-going -b html docs docs/_build/html
```

Pull Request 请提交到 `dev`。修改公开边界时，请同时增加行为测试并更新相应合同文档。当前工作见 [GitHub Issues](https://github.com/retrofor/iamai/issues)，设计讨论见 [GitHub Discussions](https://github.com/retrofor/iamai/discussions)。

---

## 开源协议

[MIT](https://github.com/retrofor/iamai/blob/dev/LICENSE) © iamai contributors

## 致谢

iamai 从 [NoneBot](https://github.com/nonebot/nonebot2)、[Koishi](https://github.com/koishijs/koishi) 和 [AliceBot](https://github.com/AliceBotProject/alicebot) 的实践中吸取经验。Agent 示例参考了 [ReAct 论文](https://arxiv.org/abs/2210.03629)及更广泛的 Agent Runtime 社区。
