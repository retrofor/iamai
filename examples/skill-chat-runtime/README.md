# skill-chat-runtime

基于技能路由（skill routing）的最小聊天机器人示例，展示 iamai 框架的**消息路由、工具调用、执行追踪和技能学习**能力。

## 概述

通过 4 个插件实现一个带"学习能力"的聊天机器人——用户聊得越多，它越"懂"该怎么路由消息：

- 每条消息经过「路由」决定该用哪个工具处理
- 执行过程记录为「追踪记录（trace）」
- 成功的追踪记录自动提炼为「技能清单（skill manifest）」
- 后续消息优先匹配历史技能，形成自我优化循环

**展示的 iamai 特性：**

- `message_handler` 自由文本匹配（无需命令前缀）
- `command` 命令系统
- `plugin_dirs` 自动发现
- 插件依赖与加载顺序（`requires`、`load_after`）
- 多阶段 Middleware（`before`、`error`）
- 跨插件协作（通过 `runtime.get_plugin()`）
- `ToolRegistry` 工具注册与调用
- Pydantic 配置模型

## 快速开始

```bash
# Windows（在 iamai 根目录）
.venv\Scripts\Activate.ps1
cd examples\skill-chat-runtime
python run.py
```

```bash
# Linux / macOS
source .venv/bin/activate
cd examples/skill-chat-runtime
python run.py
```

启动后看到 `skill>` 提示符即可输入。

## 核心概念

### 一条消息的完整流程

```
用户输入: "帮我算一下 17 * 23 + 5"
    │
    ▼
┌──────────┐
│  router  │  _route() 路由决策
│          │  ① 技能匹配：搜索 skill 库，找最佳匹配
│          │  ② 启发式：匹配不到就按关键词规则
│          │  ③ 兜底：都不行就走 echo
└────┬─────┘
     │ 决定: tool=math, skill=skill.math.quick
     ▼
┌──────────┐
│  tools   │  run_tool("math", "17 * 23 + 5")
│          │  → AST 解析 → 安全求值 → "396"
└────┬─────┘
     │
     ▼
┌──────────┐
│  memory  │  append_trace(trace)
│          │  记录完整追踪：输入、工具、结果、路由原因...
└────┬─────┘
     │
     ▼
┌──────────┐
│  skills  │  ingest_trace(trace)  ← 自动提炼技能
│          │  更新 skill.math.quick 的 success_count +1
│          │  若 success_count >= 4 → 升级为 "promoted"
└──────────┘
```

### 技能生命周期

```
draft ──(成功≥2次)──▶ verified ──(成功≥4次)──▶ promoted
  │                                                │
  └────────────────(失败≥3次 & 失败率≥60%)──────────▶ deprecated（不再参与匹配）
```

## 命令列表

### 消息交互

| 输入 | 说明 | 示例 |
|------|------|------|
| 自由文本 | 自动路由到合适的工具 | `hello`、`17*23+5`、`remember 我喜欢蓝色` |
| `/chat` | 显式命令模式聊天 | `/chat what time is it` |
| `/route` | 查看路由决策详情（调试用） | `/route 算一下 1+2` |

### 技能管理

| 命令 | 说明 | 示例 |
|------|------|------|
| `/skills` | 列出最近技能 | `/skills` |
| `/skills <关键词>` | 搜索匹配的技能 | `/skills math` |
| `/skill <id>` | 查看指定技能详情 | `/skill skill.math.quick` |
| `/skill <id> replay` | 回放技能的源追踪记录 | `/skill skill.math.quick replay` |
| `/skill promote [标题]` | 手动将最新追踪提升为技能 | `/skill promote quick math` |

### 追踪诊断

| 命令 | 说明 | 示例 |
|------|------|------|
| `/trace` | 查看最近一条追踪记录 | `/trace` |
| `/traces` | 列出最近 6 条追踪 | `/traces` |
| `/successes` | 列出最近成功追踪 | `/successes` |
| `/failures` | 列出最近失败追踪 | `/failures` |

### 内置管理（来自框架）

| 命令 | 说明 |
|------|------|
| `/plugins` | 列出已加载插件 |
| `/adapters` | 列出适配器 |
| `/reload` | 热重载插件 |

## 目录结构

```
examples/skill-chat-runtime/
├── run.py                           # 入口脚本
├── pyproject.toml                   # 项目配置
├── config.terminal.toml             # 终端模式配置
└── src/
    └── skill_chat_runtime/
        ├── __init__.py
        ├── skilllib.py              # 共享数据模型与工具函数
        └── plugins/
            ├── __init__.py
            ├── memory.py             # 追踪记录与笔记存储
            ├── skills.py             # 技能清单管理与搜索
            ├── tools.py              # 原子工具注册与调用
            └── router.py             # 消息路由与调度
```

## 插件详解

### 插件依赖关系

```
┌─────────┐
│ memory  │ ◄── 存储追踪记录、笔记、错误信息
└────┬────┘
     │ requires
┌────▼────┐
│ skills  │ ◄── 管理技能清单，搜索与评分
└────┬────┘
     │ requires
┌────▼────┐
│ tools   │ ◄── 注册 5 个原子工具（echo/math/remember/recall/search_skill）
└────┬────┘
     │ requires + load_after
┌────▼────┐
│ router  │ ◄── 接收消息 → 路由决策 → 调用工具 → 记录追踪 → 提炼技能
└─────────┘
```

加载顺序：`memory → skills → tools → router`

### MemoryPlugin — 追踪与笔记

**功能**：存储执行追踪记录（trace）和用户笔记（notes）。

**Middleware**：

| 阶段 | 方法 | 功能 |
|------|------|------|
| `before` | `ensure_buffers` | 确保 `notes`、`traces`、`last_error` 字段存在 |
| `error` | `explain_agent_error` | 捕获异常，仅对 router 插件做友好提示 |

**关键方法**：

- `append_trace(trace)` — 存储追踪记录，超过 `trace_limit` 自动裁剪
- `last_trace()` — 获取最近一条追踪记录

### SkillsPlugin — 技能清单

**功能**：管理技能清单的增删改查，提供搜索与评分。

**技能状态流转**：`draft → verified → promoted`（升级）/ `deprecated`（降级）

**关键方法**：

- `search(query)` — 按词元重叠评分搜索技能
- `best_match(query)` — 返回最佳匹配技能
- `ingest_trace(trace)` — 从追踪记录更新或创建技能（自动提升）
- `promote_latest_trace()` — 手动将最新追踪提升为技能

### ToolsPlugin — 工具集

**功能**：注册 5 个原子工具，通过 `ToolRegistry` 统一调用。

| 工具名 | 功能 | 示例 |
|--------|------|------|
| `echo` | 回显输入文本 | `heard: hello` |
| `math` | 安全求值算术表达式（AST 解析） | `17*23+5 → 396` |
| `remember` | 存储笔记 | `stored note: 我喜欢蓝色` |
| `recall` | 按关键词搜索笔记 | 返回匹配结果 |
| `search_skill` | 搜索技能清单 | 返回匹配的技能列表 |

### RouterPlugin — 路由调度

**功能**：接收所有消息，决定用哪个工具处理，记录追踪，触发技能学习。

**路由优先级**：
1. **技能匹配** — 用 `skills.best_match()` 找最佳技能，分数 ≥ `skill_threshold` 则命中
2. **启发式规则** — 按内置关键词规则匹配（纯数字表达式→math，含"remember"→remember...）
3. **兜底** — 都不匹配就走 `echo`

**消息入口**：
- `free_chat`（`@message_handler`）处理不以 `/` 开头的自由文本
- `/chat` 命令显式调用
- `/route` 命令调试模式（跳过自动技能提炼）

### skilllib.py — 共享数据模型

| 类/函数 | 用途 |
|---------|------|
| `RouteDecision` | 路由决策结果（来源、工具名、技能ID、分数） |
| `TraceRecord` | 单次执行追踪（输入、工具、结果、路径、状态） |
| `SkillManifest` | 技能定义（触发器、示例、步骤、生命周期、评分） |
| `score_skill(query, manifest)` | 基于词元重叠的加权评分算法 |
| `build_skill_manifest(trace)` | 从追踪记录构建新技能 |
| `tokenize(text)` | 分词并去除停用词 |
| `default_seed_skills()` | 返回 5 个内置种子技能 |

## 评分算法

`score_skill()` 对查询词元和技能清单各字段进行加权匹配：

| 匹配字段 | 权重 | 说明 |
|----------|:----:|------|
| `title` 命中 | ×3.0 | 标题匹配最重要 |
| `triggers` 命中 | ×2.5 | 触发词匹配 |
| `tags` 命中 | ×2.0 | 标签匹配 |
| `summary` 命中 | ×1.5 | 摘要匹配 |
| `examples` 命中 | ×1.0 | 示例匹配 |
| `tool_name` 命中 | +2.0 | 工具名直接命中加分 |
| `lifecycle=promoted` | +3.0 | 已推广技能加分 |
| `lifecycle=verified` | +2.0 | 已验证技能加分 |
| `lifecycle=deprecated` | ×0.3 | 已弃用技能大幅降权 |
| 成功率 | ×4.0 | 成功率越高分越高 |
| 复用次数 | ×0.25 | 重用越多分越高（上限10次） |

## 配置说明

关键配置项（完整配置见 `config.terminal.toml`）：

```toml
[runtime]
command_prefixes = ["/"]
adapters = ["terminal"]
plugin_dirs = ["src/skill_chat_runtime/plugins"]   # 插件自动发现
python_paths = ["src"]                              # 源码路径
superusers = ["skill-user"]

[plugin.memory]
note_limit = 12           # 最多保留笔记数
trace_limit = 8           # 最多保留追踪数

[plugin.skills]
skill_limit = 20          # 最多保留技能数
auto_promote = true       # 是否自动提炼技能
search_limit = 5          # 搜索返回结果数

[plugin.router]
skill_threshold = 0.45    # 技能匹配最低分数阈值
```
