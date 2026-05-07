# life-sim-runtime

Life simulator example for iamai.

This example shows:

- stateful storytelling across multiple turns
- `before` and `error` middleware for long-lived game state
- LLM-generated yearly scenes with structured choices

## Run

```bash
uv run --package life-sim-runtime python -m iamai --config examples/life-sim-runtime/config.terminal.toml
```

## Try

- `/newlife cyberpunk`
- `/status`
- `/next`
- `/choose 2`
- `/history`
