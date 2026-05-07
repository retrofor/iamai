# planner-executor-runtime

Planner / Executor agent loop example for iamai.

This example shows:

- plugin dependencies via `requires` and `load_after`
- shared runtime state through middleware
- a two-stage LLM workflow: planning first, execution second

## Run

```bash
uv run --package planner-executor-runtime python -m iamai --config examples/planner-executor-runtime/config.terminal.toml
```

## Try

- `/plugins`
- `/plan ship a tiny launch checklist for an indie game`
- `/execute design a three-step weekend study plan for Rust`
- `/last`
- `/runs`
