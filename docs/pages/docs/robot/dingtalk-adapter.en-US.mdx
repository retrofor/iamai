# DingTalk Protocol Adapter 

## Installation

```sh
pip install iamai-adapter-dingtalk
```

## Configuring the Protocol Endpoint

The DingTalk protocol adapter is an adapter for the DingTalk enterprise robot protocol. DingTalk's enterprise robot uses the outgoing (callback) mechanism. After a user mentions the robot, DingTalk will POST the message content to the developer's message receiving address.

For specific configurations, refer to the relevant documentation on the DingTalk Open Platform:

- [Robot Overiew](https://open.dingtalk.com/document/group/robot-overview)
- [Enterprise Internal Development of Robots](https://open.dingtalk.com/document/group/enterprise-created-chatbot)

During testing,  you may not have your own public domain name or IP. DingTalk provides an intranet penetration tool: [Intranet Penetration Tool](https://open.dingtalk.com/document/resourcedownload/http-intranet-penetration) . 

## Configuring iamai

You need to edit `config.toml` to configure the DingTalk adapter. Refer to [Basic Configuration](./basic-config.md) and [DingTalk Configuration](/api/adapter/dingtalk/config.md) . 

## Sending Rich Text Messages

When writing plugins, besides sending regular text messages, you can also easily construct and send rich-text messages. Make sure you have read the Built-in Messages section before reading this section.

The special thing is that due to the uniqueness of DingTalk's rich-text messages, the message class of the DingTalk adapter `DingTalkMessage` is not a subclass of `Message`, but a subclass of `MessageSegment`. You cannot build messages by simply adding common message fields. Instead, you need to manually write Markdown text.

```python

from iamai import Plugin
from iamai.adapter.digntalk.message import DingTalkMessage

class Halloiamai(Plugin):
    async def handle(self) -> None:
        await self.event.reply(DingTalkMessage.markdown("# hello\n\nHello, iamai!"))

    async def rule(self) -> bool:
        if self.event.adapter.name != "dingtalk":
            return False
        return str(self.event.message).strip().lower() == "hello"


```

For more usage methods, please refer to [Message Types and Data Formats](https://open.dingtalk.com/document/group/message-types-and-data-format) and [CQHTTP Messages](/api/adapter/dingtalk/message.md) . 

