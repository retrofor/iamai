# supervisor-team-runtime

Supervisor multi-agent example for iamai.

This example shows:

- a `briefing -> workers -> supervisor` dependency chain
- role-specialized workers coordinated by one top-level supervisor
- handoff and review output stored in shared plugin state

## Run

```bash
uv run --package supervisor-team-runtime python -m iamai --config examples/supervisor-team-runtime/config.terminal.toml
```

## Try

- `/roles`
- `/team launch a niche AI newsletter in 14 days`
- `/review`
- `/queue`
