import re

from plugins.iamai_plugin_base import CommandPluginBase

from .config import Config


class Send(CommandPluginBase[None, Config]):
    Config = Config

    def __post_init__(self):
        self.re_pattern = re.compile(r"\s*(?P<message>.*)", flags=re.I)

    async def handle(self) -> None:
        try:
            await self.event.adapter.send(
                self.msg_match.group("message"),
                "private",
                self.config.send_user_id,
            )
        except Exception as e:
            if self.config.send_filed_msg is not None:
                await self.event.reply(
                    self.format_str(self.config.send_filed_msg, repr(e))
                )
        else:
            if self.config.send_success_msg is not None:
                await self.event.reply(self.format_str(self.config.send_success_msg))
