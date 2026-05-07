# group-assistant-runtime

Group assistant example for iamai.

This example shows:

- passive room memory via `message_handler`
- functional group helpers for digest, TODO extraction, and contextual replies
- an explicit AI assistant loop for group chat, without pretending to be human

## Run

```bash
uv run --package group-assistant-runtime python -m iamai --config examples/group-assistant-runtime/config.terminal.toml
```

## Try

- send a few plain messages
- `/recent`
- `/digest`
- `/todo`
- `/mood`
- `ai summarize what just happened`
