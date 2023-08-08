# CQHTTP Protocol Adapter

## Installation

```sh
pip install iamai-adapter-cqhttp
```

## Configuring the Protocol Endpoint

The CQHTTP protocol adapter is an adapter for the OneBot protocol (formerly known as the CKYU platform's CQHTTP protocol). It requires a protocol endpoint that is compatible with the OneBot protocol for communication. Here are some commonly used QQ protocol endpoints that support the OneBot protocol:

- [go-cqhttp](https://github.com/Mrs4s/go-cqhttp)
- [mirai](https://github.com/mamoe/mirai) + [onebot-kotlin](https://github.com/yyuueexxiinngg/onebot-kotlin)
- [oicq](https://github.com/takayama-lily/oicq)

Below is an example using go-cqhttp:

1. Download the release version of go-cqhttp corresponding to your platform: Github Releases
2. Run `go-cqhttp` or `go-cqhttp.exe` to generate the default configuration file.
3. Edit the configuration file `config.yml` and restart the program.

Currently, the CQHTTP adapter supports WebSocket connection and reverse WebSocket connection. The go-cqhttp configuration file should look like this:

```yaml
account:
   uin: BotQQNumber
   password:'BotPassword'

message:
   # Post data format
   post-format: array

# Connection service list, choose only one of the following reverse WS and forward WS

servers:
  # Reverse WS settings
  - ws-reverse:
      # Reverse WS Universal address
      universal: ws://127.0.0.1:8080/cqhttp/ws
      # Reconnection interval in milliseconds
      reconnect-interval: 3000
      middlewares:
        <<: *default # Reference default middleware
  # Forward WS settings
  - ws:
      # Forward WS server listening address
      host: 127.0.0.1
      # Forward WS server listening port
      port: 6700
      middlewares:
        <<: *default # Reference default middleware

```

Other items can remain as default.

## Configuring iamai

If you have installed and configured `go-cqhttp` as mentioned above and are using reverse WebSocket connection, there is no need to configure iamai separately.

If you have other specific requirements, you can edit `config.toml` for configuration, refer to [Basic Configuration](./basic-config.md) and [CQHTTP Configuration](/api/adapter/cqhttp/config.md) 

## Running Tests 

```text
2021-09-01 18:05:29.740 | INFO     | iamai.adapter.cqhttp:handle_cqhttp_event:138 - WebSocket connection from CQHTTP Bot xxxxxx accepted!
```

## Sending Rich Text Messages

When writing plugins, besides sending regular text messages, you can also easily construct and send rich-text messages. Make sure you have read the Built-in Messages section before reading this section.

```python
from iamai import Plugin
from iamai.adapter.cqhttp.message import CQHTTPMessageSegment

class Helloiamai(Plugin):
    async def handle(self) -> None:
        msg = CQHTTPMessageSegment.text("Hello, iamai!") + \
              CQHTTPMessageSegment.image("https://www.example.org/1.jpg")
        await self.event.reply(msg)
    
    async def rule(self) -> bool:
        if self.event.adapter.name != "cqhttp":
              return False
        if self.event.type != "message":
              return False
        return str(self.event.message).lower() == "hello"

```

For more usage methods, please refer to [OneBot Message Segment Types](https://github.com/botuniverse/onebot-11/blob/master/message/segment.md) and [CQHTTP Messages](/api/adapter/cqhttp/message.md) . 

## Calling OneBot API 

You can call OneBot API using following method :

```python
from iamai import Plugin

class TestPlugin(Plugin):
    async def handle(self) -> None:
       resp = await self.event.adapter.call_api("send_like", user_id=10001)
       # Equivalent to resp = await self.event.adapter.send_like(user_id=10001)

    async def rule(self) -> bool:
       return self.event.adapter.name == "cqhttp"

```

For more usage methods, please refer to [OneBot Public API](https://github.com/botuniverse/onebot-11/blob/master/api/public.md) . 
