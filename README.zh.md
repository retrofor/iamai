<p align="center">
  <img src="https://raw.githubusercontent.com/retrofor/iamai/dev/docs/_static/brand/iamai-logo.svg" alt="iamai gateway mark" width="120">
</p>

<h1 align="center">iamai</h1>

<p align="center">
  <strong>连接平台协议与业务逻辑的消息运行时。</strong>
</p>

<p align="center">
  只做一次事件归一化，让类型明确的异步 Python 插件、可选 Agent workflow<br>
  和 Rust 消息处理能力运行在每一个 Adapter 之后。
</p>

<p align="center">
  <a href="https://github.com/retrofor/iamai"><img src="https://img.shields.io/github/stars/retrofor/iamai?logo=github&label=Stars" alt="GitHub stars"></a>
  <a href="https://pypi.org/project/iamai/"><img src="https://img.shields.io/pypi/v/iamai?color=e8462f&label=PyPI" alt="PyPI version"></a>
  <a href="https://pypi.org/project/iamai/"><img src="https://img.shields.io/badge/Python_3.11+-17212b?logo=python&logoColor=white" alt="Python 3.11 or newer"></a>
  <a href="https://github.com/retrofor/iamai/actions/workflows/check.yml"><img src="https://github.com/retrofor/iamai/actions/workflows/check.yml/badge.svg?branch=dev" alt="CI status"></a>
  <a href="https://github.com/retrofor/iamai/blob/dev/LICENSE"><img src="https://img.shields.io/badge/license-MIT-159b7a" alt="MIT license"></a>
</p>

<p align="center">
  <a href="https://github.com/retrofor/iamai/blob/dev/docs/quickstart.rst">快速开始</a> ·
  <a href="https://github.com/retrofor/iamai/tree/dev/docs/tutorials">渐进式教程</a> ·
  <a href="https://github.com/retrofor/iamai/tree/dev/examples">示例</a> ·
  <a href="https://github.com/retrofor/iamai/blob/dev/docs/reference/extensions.rst">扩展合同</a> ·
  <a href="https://github.com/retrofor/iamai/releases/tag/v1.0.0">v1.0.0</a>
</p>

<p align="center">
  <a href="https://github.com/retrofor/iamai/blob/dev/README.md">English</a> · <b>中文</b>
</p>

---

## 为什么是 iamai

聊天平台的 payload、传输、鉴权和回复 API 各不相同，业务逻辑不应该因此重复实现。

iamai 在平台与业务之间放置一个小而明确的运行时：

| 边界 | iamai 稳定下来的内容 |
|---|---|
| **平台边缘** | Adapter 把 Terminal、OneBot、Telegram 和 Webhook 流量归一化为 `Event` 与 `Message`。 |
| **业务代码** | Plugin 只使用 `Context`、命令、规则、权限、依赖注入、中间件、状态和会话。 |
| **运行时生命周期** | 扩展发现、启动、关闭、重载、回滚、配置与可观测性都有明确合同。 |
| **Agent 执行** | 可选的模型调用、工具、审批、trace 和 guardrail 复用同一套权限与审计边界。 |

iamai 是运行时，不是大而全的机器人控制台。它不强制使用 LLM，不隐藏网络边界，也不要求
业务代码绑定某个平台 SDK。经常变化的行为留在 Python；选定的消息与归一化路径由 Rust 加速。

> **稳定合同：** `v1.0.0` 是当前 1.x 兼容线。第三方扩展应声明 `iamai>=1,<2`，并在发布前
> 运行公开 conformance helpers。

## 跑通一条真实消息链路

在自己的项目中安装稳定版：

```bash
python -m pip install "iamai>=1,<2"
```

要验证完整的 Adapter → Runtime → Plugin → 回复链路，可以运行仓库持续维护的终端示例：

```bash
git clone --depth 1 https://github.com/retrofor/iamai.git
cd iamai
uv sync --locked --all-packages --group dev

# 启动前先检查配置、扩展发现和插件 Schema。
uv run --package echo-runtime iamai \
  --config examples/echo-runtime/config.terminal.toml config-check

# 启动本地 TerminalAdapter Runtime。
uv run --package echo-runtime iamai \
  --config examples/echo-runtime/config.terminal.toml
```

出现提示符后输入：

```text
/echo hello iamai
```

示例会通过接收事件的同一个 Adapter 回复消息。[快速开始](https://github.com/retrofor/iamai/blob/dev/docs/quickstart.rst)
进一步解释配置与链路中的对象。

业务代码仍然只是普通的异步 Python：

```python
from iamai import Context, Plugin, command


class HelloPlugin(Plugin):
    name = "hello"

    @command("hello")
    async def hello(self, ctx: Context) -> None:
        await ctx.reply("Hello from iamai.")
```

## 一个 Runtime，边界必须清楚

```text
Terminal · OneBot · Telegram · Webhook · 你的协议
                         │
                         ▼
                      Adapter
              payload → Event + Message
                         │
                         ▼
          Rule · Permission · DI · Middleware
                       Runtime
                         │
                         ▼
                 Plugin 或 Agent workflow
                         │
                         └──── Context.reply() ────► Adapter ────► 平台
```

| 分层 | 负责内容 | 源码 |
|---|---|---|
| **Adapter** | 网络、信任、协议转换、重连和出站 API | [`python/iamai/adapters`](https://github.com/retrofor/iamai/tree/dev/python/iamai/adapters) |
| **Runtime** | 配置、扩展发现、生命周期、分发、DI、中间件、状态、会话与重载 | [`python/iamai`](https://github.com/retrofor/iamai/tree/dev/python/iamai) |
| **Plugin** | 命令、事件 handler、规则、权限和产品行为 | [`examples`](https://github.com/retrofor/iamai/tree/dev/examples) |
| **Rust core** | 消息链操作、OneBot 归一化和 JSON 数据辅助能力 | [`src`](https://github.com/retrofor/iamai/tree/dev/src) |

[架构指南](https://github.com/retrofor/iamai/blob/dev/docs/guides/architecture.rst)详细定义准入、分发、重载、
失效和关闭语义。

## 1.0 已经包含什么

| 能力面 | 已提供的能力 |
|---|---|
| **消息接入** | `TerminalAdapter`、OneBot 11 HTTP/WebSocket/反向 WebSocket、Telegram long polling、支持可选验签的通用 Webhook 和自定义 Adapter |
| **应用模型** | 命令、消息/事件 handler、可组合 `Rule` 与 `Permission`、依赖注入、中间件和事件作用域 `Context` |
| **有状态工作流** | 内存、JSON、SQLite 状态后端，以及按 Adapter、频道、用户隔离的 Session waiter |
| **运维能力** | 严格配置校验、版本化 JSON Schema、健康/指标视图、审计事件、管理命令和事务式热重载 |
| **Agent 组件** | OpenAI 兼容调用、`ToolRegistry`、审批钩子、追加式 `AgentTrace` 和输出 guardrail；全部可选 |
| **公开合同** | 版本化序列化、确定性扩展发现、生命周期规则、弃用政策、迁移指南和 conformance helpers |

## 从一个可运行形态开始

仓库中的示例都是完整 workspace package，不是脱离上下文的代码片段。

| 示例 | 适合从这里开始的场景 |
|---|---|
| [`echo-runtime`](https://github.com/retrofor/iamai/tree/dev/examples/echo-runtime) | 最小的终端、OneBot 与 Webhook Runtime |
| [`state-runtime`](https://github.com/retrofor/iamai/tree/dev/examples/state-runtime) | 状态后端和会话型交互 |
| [`group-assistant-runtime`](https://github.com/retrofor/iamai/tree/dev/examples/group-assistant-runtime) | 权限、群组工作流和工具路由 |
| [`react-runtime`](https://github.com/retrofor/iamai/tree/dev/examples/react-runtime) | ReAct 工具、记忆与 trace 查看 |
| [`planner-executor-runtime`](https://github.com/retrofor/iamai/tree/dev/examples/planner-executor-runtime) | 结构化规划与分阶段执行 |
| [`supervisor-team-runtime`](https://github.com/retrofor/iamai/tree/dev/examples/supervisor-team-runtime) | Supervisor 协调不同职责的 Worker |

Agent 组件不会替代 Runtime 模型。它们是带明确依赖与安全边界的 Plugin 构建块，详见
[Agent Runtime 指南](https://github.com/retrofor/iamai/blob/dev/docs/guides/agent-runtime.rst)。

## 不 fork 核心也能扩展

第三方包可以发布 `iamai.plugins` 和 `iamai.adapters` Python entry point。遇到重复、保留、非法或
不兼容的扩展时，iamai 会拒绝启动，而不是含糊地挑选其中一个；扩展作者还可以复用 Adapter/Plugin
conformance helpers。

- [扩展打包与发现](https://github.com/retrofor/iamai/blob/dev/docs/reference/extensions.rst)
- [序列化合同](https://github.com/retrofor/iamai/blob/dev/docs/reference/serialization-contract.rst)
- [生命周期合同](https://github.com/retrofor/iamai/blob/dev/docs/reference/public-api-lifecycle.rst)
- [公共 API conformance matrix](https://github.com/retrofor/iamai/blob/dev/docs/reference/public-api-conformance.rst)
- [0.3 → 1.0 迁移指南](https://github.com/retrofor/iamai/blob/dev/docs/guides/migration-0.3-to-1.0.rst)

## 找到正确入口

| 如果你想…… | 从这里开始 |
|---|---|
| 跑通第一条本地消息 | [快速开始](https://github.com/retrofor/iamai/blob/dev/docs/quickstart.rst) |
| 从头到尾完成一个功能 | [渐进式教程](https://github.com/retrofor/iamai/tree/dev/docs/tutorials) |
| 设计 Plugin、Adapter、状态或运维能力 | [开发指南](https://github.com/retrofor/iamai/tree/dev/docs/guides) |
| 查看公开 Python 类与函数 | [API 参考源码](https://github.com/retrofor/iamai/tree/dev/docs/api) |
| 发布或发现扩展 | [社区商店](https://github.com/retrofor/iamai/blob/dev/docs/community/store.rst) |
| 对比 iamai 与平台型、Agent 型框架 | [生态对比](https://github.com/retrofor/iamai/blob/dev/docs/guides/ecosystem-comparison.rst) |

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

Pull Request 请提交到 `dev`。公开行为变化必须同时增加测试和对应合同文档。当前工作见
[Issues](https://github.com/retrofor/iamai/issues)，设计讨论见
[Discussions](https://github.com/retrofor/iamai/discussions)。

## 开源协议与致谢

[MIT](https://github.com/retrofor/iamai/blob/dev/LICENSE) © iamai contributors。

iamai 从 [NoneBot](https://github.com/nonebot/nonebot2)、[Koishi](https://github.com/koishijs/koishi)
和 [AliceBot](https://github.com/AliceBotProject/alicebot) 的实践中吸取经验。Agent 示例参考了
[ReAct 论文](https://arxiv.org/abs/2210.03629)及更广泛的 Agent Runtime 社区。
