# echo-runtime

## 启动

终端模式：

```bash
uv run --package echo-runtime python -m iamai --config examples/echo-runtime/config.terminal.toml
```

OneBot11 正向 websocket：

```bash
uv run --package echo-runtime python -m iamai --config examples/echo-runtime/config.onebot11.ws.toml
```

OneBot11 反向 websocket：

```bash
uv run --package echo-runtime python -m iamai --config examples/echo-runtime/config.onebot11.ws_reverse.toml
```

OneBot11 HTTP webhook + HTTP API：

```bash
uv run --package echo-runtime python -m iamai --config examples/echo-runtime/config.onebot11.http.toml
```

通用 webhook：

```bash
uv run --package echo-runtime python -m iamai --config examples/echo-runtime/config.webhook.toml
```

## 内置命令

- `/ping`
- `/echo <text>`
- `/whoami`
- `/state`
- `/reload`
- `/plugins`
- `/adapters`
- 直接发送 `hi` 或 `你好` 可触发问候

## Webhook 调试

通用 webhook 适配器会监听 `http://127.0.0.1:8090/events`。可以这样发一个事件：

```bash
curl -X POST http://127.0.0.1:8090/events \
  -H 'content-type: application/json' \
  -d '{"text":"hi","user_id":"tester","channel_id":"demo"}'
```
