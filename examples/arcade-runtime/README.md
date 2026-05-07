# arcade-runtime

一个偏游戏化的 iamai 示例，展示：

- `plugin_dirs` 自动发现
- 插件依赖与加载顺序
- `before / after / error` middleware
- builtin 管理插件 `/reload` `/plugins` `/adapters`

## 启动

```bash
uv run --package arcade-runtime python -m iamai --config examples/arcade-runtime/config.terminal.toml
```

## 试试这些命令

- `/plugins`
- `/adapters`
- `/spin`
- `/wallet`
- `/roll d20`
- `/quest`
- `/leaderboard`
- `/boom`
