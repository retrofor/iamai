# story-runtime

一个偏叙事生成的 iamai 示例，展示：

- `requires / optional_requires / load_before`
- `before / after / error` middleware
- `message_handler` 与状态记忆

## 启动

```bash
uv run --package story-runtime python -m iamai --config examples/story-runtime/config.terminal.toml
```

## 试试这些命令

- `/plugins`
- `/cast 机械鲸:船长`
- `/where 月光码头`
- `/scene 雨夜追逐`
- `/twist`
- 输入 `继续`
- `/recap`
- `/panic`
