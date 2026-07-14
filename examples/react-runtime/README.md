# react-runtime

ReAct loop example for iamai.

This example shows:

- a `memory -> tools -> reactor` plugin chain
- `before` and `error` middleware around an agent loop
- LLM-driven tool selection with explicit observations
- optional plain-message chat mode for group adapters
- a local `SOUL.md` persona prompt loaded by the reactor

## Run

```bash
uv run --package react-runtime python -m iamai --config examples/react-runtime/config.terminal.toml
```

## Try

- `/ask should I spend a free evening learning SQL or shipping a small script?`
- `/ask help me compare 17*23 with rolling 3d6`
- `/remember I prefer short answers`
- `/notes`
- `/react-trace`

Set `chat_mode = true` under `[plugin.reactor]` to let non-command messages enter the
ReAct loop. The OneBot example enables this mode and suppresses replies when the model
returns `{"silent": true}`.

`SOUL.md` is appended to the system prompt when present. Keep persona-specific behavior
there and keep tool contracts in the plugin source.
