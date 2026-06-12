# skill-chat-runtime

A minimal skill-routing chatbot example for `iamai`.

It demonstrates:

- message routing
- tool calls
- trace recording
- skill search and promotion
- LLM fallback replies

## Start

```powershell
cd D:\jiandian\iamai
uv run --package skill-chat-runtime python -m iamai --config examples/skill-chat-runtime/config.terminal.toml
```

The terminal prompt is `skill> `.

## How it works

1. User input is routed to an existing skill first.
2. If no skill matches, heuristic rules are checked.
3. If nothing matches, the router calls `llm_reply`.
4. `llm_reply` traces are automatically promoted after 3 consecutive successes.

The example also keeps a persistent trace buffer, so you can inspect the last runs and manually promote them later.

## Chatting

You can type natural language directly:

- `画图软件哪个最好`
- `帮我推荐一个适合 UI 设计的工具`
- `我想要一个更适合新手的绘图软件`

The bot will:

- try to reuse an existing skill
- otherwise use the LLM fallback

If you want to force the command form, use:

- `/chat <message>`

## Commands

### Chat and routing

- `/chat <message>` - route a message explicitly
- `/route <message>` - show the route decision for a message

### Skill management

- `/skills` - list recent skills
- `/skills <query>` - search skills
- `/skill <skill_id>` - inspect a skill
- `/skill <skill_id> replay` - replay the source trace
- `/skill promote [title]` - promote the latest successful trace

### Trace inspection

- `/trace` - show the latest trace
- `/traces` - show recent traces
- `/successes` - show recent successful traces
- `/failures` - show recent failed traces

### Runtime management

- `/plugins` - list loaded plugins
- `/adapters` - list adapters
- `/reload` - reload plugins

## LLM config

This example reads its own `.env` file at:

- `examples/skill-chat-runtime/.env`

Required variables:

```env
OPENAI_API_KEY=...
OPENAI_BASE_URL=...
OPENAI_MODEL=...
```

For DeepSeek compatibility, the current local `.env` uses:

- `OPENAI_BASE_URL=https://api.deepseek.com`
- `OPENAI_MODEL=deepseek-v4-pro`

## Files

- `src/skill_chat_runtime/plugins/router.py` - routing and fallback
- `src/skill_chat_runtime/plugins/tools.py` - tool registry and `llm_reply`
- `src/skill_chat_runtime/plugins/skills.py` - skill storage and promotion
- `src/skill_chat_runtime/plugins/memory.py` - notes and trace buffers
