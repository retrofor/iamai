# react-runtime

ReAct loop example for iamai.

This example shows:

- a `memory -> tools -> reactor` plugin chain
- `before` and `error` middleware around an agent loop
- LLM-driven tool selection with explicit observations

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
