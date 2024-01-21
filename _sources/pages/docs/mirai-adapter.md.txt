# Mirai Protocol Adapter 

The Mirai Protocol Adapter is an adapter for the [mirai-api-http](https://github.com/project-mirai/mirai-api-http) protocol. You need to install mirai-api-http following the instructions in its documentation.

Please note that this adapter only supports mirai-api-http version 2.3 and above.

This adapter supports both the Websocket Adapter mode and the Reverse Websocket Adapter mode of mirai-api-http.

## Installation

```sh 
pip install iamai-adapter-mirai
```

## Configuring the Protocol Endpoint 

Edit the `setting.yml` configuration file of mirai-api-http:

### Websocket Adapter Mode

```yaml

adapters:
  - ws
enableVerify: true
verifyKey: 1234567890
adapterSettings:
  ws:
    host: localhost
    port: 8080
    reservedSyncId: -1

```

### Reverse Websocket Adapter Mode

```yaml

adapters:
  - reverse-ws
enableVerify: true
verifyKey: 1234567890
singleMode: true
adapterSettings:
  reverse-ws:
    destinations:
    - host: localhost
      port: 8080
      path: /mirai/ws
      protocol: ws
      method: GET
    reservedSyncId: -1

```

## Configuring iamai

Edit the `config.toml` configuration file of iamai.

For more options, please refer to the Mirai configuration.

### Websocket Adapter Mode 

```toml

[bot]
adapters = ["iamai.adapter.mirai"]

[adapter.mirai]
adapter_type = "ws"
verify_key = "1234567890"
qq = "机器人QQ号"

```

### Reverse Websocket Adapter Mode

```toml
[bot]
adapters = ["iamai.adapter.mirai"]

[adapter.mirai]
adapter_type = "reverse-ws"
verify_key = "1234567890"
qq = "机器人QQ号"

```

## Sending Rich Text Messages

Similar to the CQHTTP protocol adapter, the Mirai adapter can easily construct rich text messages.

```python

from iamai import Plugin
from iamai.adapter.mirai.message import MiraiMessageSegment


class Halloiamai(Plugin):
    async def handle(self) -> None:
        msg = MiraiMessageSegment.plain("Hello, iamai!") + \
              MiraiMessageSegment.image(url="https://www.example.org/1.jpg")
        await self.event.reply(msg)

    async def rule(self) -> bool:
        if self.event.adapter.name != "mirai":
            return False
        if self.event.type != "FriendMessage":
            return False
        return self.event.message.get_plain_text().lower() == "hello"

```

For more usage, please refer to [mirai-api-http message segment types](https://docs.mirai.mamoe.net/mirai-api-http/api/MessageType.html) and Mirai messages.

## Calling mirai-api-http API 

You can use the following method to call mirai-api-http API:


```python

from iamai import Plugin


class TestPlugin(Plugin):
    async def handle(self) -> None:
        resp = await self.event.adapter.call_api("friendProfile", target=10001)
        # Equivalent to resp = await self.event.adapter.friendProfile(target=10001)

    async def rule(self) -> bool:
        return self.event.adapter.name == "mirai"

```

For more usage, please refer to [mirai-api-http documentation](https://docs.mirai.mamoe.net/mirai-api-http/adapter/WebsocketAdapter.html) .