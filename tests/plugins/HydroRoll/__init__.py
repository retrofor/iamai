"""中间件"""

from iamai import ConfigModel, Plugin
from iamai.log import logger

# HydroRollCore 读取 rules 文件夹内的rules package
logger.info("Loading HydroRollCore...")


class HydroRoll(Plugin):
    """中间件"""
    class Config(ConfigModel):
        __config_name__ = "HydroRoll"

    priority = 0

    async def handle(self) -> None:
        """
        @TODO: HydroRollCore should be able to handle all signals and tokens from Psi.
        @BODY: HydroRollCore actives the rule-packages.
        """

        if self.event.message.get_plain_text() == ".core":
            await self.event.reply("HydroRollCore is running.")
        elif self.event.message.startswith(".test"):
            try:
                from ast import literal_eval
                result = literal_eval(self.event.message.get_plain_text()[5:])
                await self.event.reply(result)
            except Exception as e:
                await self.event.reply(f"{e!r}")

    async def rule(self) -> bool:
        """
        @TODO: Psi should be able to handle all message first.
        @BODY: lexer module will return a list of tokens, parser module will parse the tokens into a tree, and executor module will execute the tokens with a stack with a bool return value.
        """
        logger.info("loading psi...")
        if self.event.type != "message":
            return False
        return self.event.message.get_plain_text().startswith(".")