import re

from plugins.iamai_plugin_base import CommandPluginBase

from .config import Config


class Echo(CommandPluginBase[None, Config]):
    Config = Config

    def __post_init__(self):
        self.re_pattern = re.compile(r"(?P<echo_str>.*)", flags=re.I)

    async def handle(self) -> None:
        await self.event.reply(
            self.format_str(self.config.message_str, self.msg_match.group("echo_str"))
        )
