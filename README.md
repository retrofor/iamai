<p align="center">
  <img src="docs/_static/brand/iamai-logo-wide.svg" alt="iamai" width="720">
</p>

<p align="center">
  <strong>面向插件开发和多平台接入的 Rust + Python 消息运行时。</strong>
</p>

# iamai

iamai 是一个 `Rust + Python` 双层跨平台消息运行时：

- Python 负责插件生态、配置装配、运行编排。
- Rust 负责消息链、协议归一化、配置深度合并等底层能力。
- 使用 `PyO3 + maturin` 打包成一个 Python 包。
- 以 `uv` 作为项目与示例的统一管理器。

## 设计目标

- 保留 NoneBot 的 `Runtime / Adapter / Plugin` 分层。
- 借鉴 Koishi 的高扩展性与适配器插件化思路。
- 保持 AliceBot / iamai 这种轻量、直接、容易写插件的体验。
- 插件只写 Python，底层数据结构和协议归一化交给 Rust。

## 当前能力

- `TerminalAdapter`：本地终端交互适配器。
- `OneBot11Adapter`：支持 `ws`、`ws-reverse`、`http` 三种模式。
- `WebhookAdapter`：通用 HTTP webhook 适配器。
- Python 插件系统：
  - `@command(...)`
  - `@message_handler(...)`
  - `@event_handler(...)`
- 中间件与依赖注入：
  - `@middleware(phase="before" | "around" | "after" | "error")`
  - `depends(...) / Depends(...)`
- 插件依赖与加载顺序：
  - `requires`
  - `optional_requires`
  - `load_after`
  - `load_before`
- 插件热重载：
  - 手动 `runtime.reload_plugins()`
  - 基于文件变更轮询的自动热重载
- 内置管理插件：
  - `/reload`
  - `/reload-config`
  - `/plugins`
  - `/plugin <name>`
  - `/plugin-config <name>`
  - `/adapters`
  - `/health`
  - `/sessions`
  - `/trace last`
- 配置文件使用 TOML。
- 示例项目位于：
  - [examples/echo-runtime](examples/echo-runtime)
  - [examples/arcade-runtime](examples/arcade-runtime)
  - [examples/story-runtime](examples/story-runtime)
  - [examples/planner-executor-runtime](examples/planner-executor-runtime)
  - [examples/react-runtime](examples/react-runtime)
  - [examples/supervisor-team-runtime](examples/supervisor-team-runtime)
  - [examples/life-sim-runtime](examples/life-sim-runtime)
  - [examples/group-assistant-runtime](examples/group-assistant-runtime)
  - [examples/persona-rp-runtime](examples/persona-rp-runtime)

## 项目结构

```text
.
├── Cargo.toml
├── pyproject.toml
├── src/lib.rs
├── python/iamai
│   ├── adapters
│   ├── runtime.py
│   ├── plugin.py
│   ├── context.py
│   └── ...
├── docs
└── examples/echo-runtime
```

## 开发

根项目：

```bash
uv sync
uv run python -m iamai --config examples/echo-runtime/config.terminal.toml
```

示例项目也作为根 workspace member 启动，不需要进入子目录单独 ``uv sync``：

```bash
uv run --package echo-runtime python -m iamai --config examples/echo-runtime/config.terminal.toml
```

文档：

```bash
uv sync --group docs
uv run sphinx-build -b html docs docs/_build/html
```

质量检查：

```bash
uv run ruff check .
uv run pytest
bash scripts/check_example_configs.sh
```

## 架构概览

```text
Python plugins
    ↓
Middleware / Dependency Injection / Context / Runtime / Adapter lifecycle
    ↓
Rust core (_core)
    - message chain
    - OneBot11 event normalization
    - JSON config deep merge
```

## 生态调研

见 [docs/ecosystem-and-architecture.md](docs/ecosystem-and-architecture.md)。

## 新增运行时能力

- 插件热重载：
  - 在配置里开启 `[runtime.hot_reload]`
  - 修改插件文件后框架会自动重载
  - 设置 `config = true` 后，修改当前 TOML 配置文件也会触发配置与插件重载
- CLI 配置检查：
  - `python -m iamai --config config.toml config-check`
  - `python -m iamai --config config.toml config-schema [plugin]`
  - `config-check` 会打印高风险配置告警，但不会阻止本地开发态配置通过
- 插件依赖图：
  - 加载前会做依赖解析与拓扑排序
  - 缺失依赖和循环依赖会在启动时直接报错
- 依赖注入：
  - handler / middleware 参数可以直接声明 `ctx`、`runtime`、`event`、`adapter`、`plugin`
  - 也可以用 `depends(...)` 注入派生值
- 多轮会话：
  - handler 可用 `await ctx.wait_for_message(timeout=60)` 等待同会话下一条消息
  - 管理命令 `/sessions` 可查看等待中的会话
- 事件中间件分层：
  - `before` 适合预处理和上下文注入
  - `around` 适合包裹 handler
  - `after` 适合成功后的收尾
  - `error` 适合统一错误处理，可返回 `True` 表示抑制异常
- HTTP/Webhook：
  - OneBot11 可用 HTTP webhook 收事件、HTTP API 发动作
  - 通用 `WebhookAdapter` 可接任意外部系统 POST 事件
- Agent runtime：
  - 内置 `LLMClient / ToolRegistry / AgentTrace / Guardrail`
  - examples 里的 ReAct 工具调用已迁移到框架级 `ToolRegistry`
- 持久化状态：
  - 插件可声明 `state_scope = "persistent"`
  - 配置 `[state] backend = "json"` 后会把插件 state 写入 JSON 文件
  - 配置 `[state] backend = "sqlite"` 后会把插件 state 写入 SQLite
- Sphinx 文档：
  - 使用 `readthedocs.io + Furo + rst`
  - API 参考通过 autodoc / autosummary 自动生成
  - 提供模块指南与渐进式教程

## 生产建议

- `WebhookAdapter` 暴露到公网时，至少同时配置 `access_token` 和 `signature_secret`。
- 除非上游系统无法配合，否则不要开启 `allow_query_token`。
- 保持 `allow_event_reply_url = false`；如果必须开启，配合 `reply_url_allowlist` 使用。
- 管理命令只给 `runtime.superusers`，并保持 `reload_requires_superuser = true`、`introspection_requires_superuser = true`。
- `runtime.allow_external_paths = true` 只建议用于示例或多项目共享代码目录。

## 工程质量门禁

- `ruff`：静态检查
- `pytest`：运行时安全与行为回归
- `config-check`：示例配置与插件装配校验
- `sphinx-build`：文档与 API 参考可构建性校验

## 示例

- `echo-runtime`：最小可运行样板，覆盖终端、OneBot11、Webhook 配置模板。
- `arcade-runtime`：多插件依赖、before/after/error middleware、leaderboard 和错误恢复。
- `story-runtime`：叙事型状态机示例，展示 `load_before`、`optional_requires` 和 message handler。
- `planner-executor-runtime`：Planner / Executor agent loop，展示跨插件计划与执行协作。
- `react-runtime`：ReAct loop，展示工具调用、observation trace 和错误收敛。
- `supervisor-team-runtime`：Supervisor + specialist workers，多角色协作与总结。
- `life-sim-runtime`：人生模拟器，展示长期状态、场景生成和结构化选项。
- `group-assistant-runtime`：群聊助手，展示房间记忆、总结、TODO 提取和显式 AI 回复。
- `persona-rp-runtime`：显式 AI 角色扮演，展示 persona 切换和群聊式对话风格。

LLM examples 默认读取 ``examples/_shared/.env``，各示例只在插件配置里保留 temperature 和 token 限制。
需要临时覆盖时，可以在 shell 里设置：

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="xxx"
# Optional:
# export OPENAI_BASE_URL="https://your-compatible-endpoint/v1"
```
