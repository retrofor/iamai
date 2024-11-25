from iamai import Plugin
from iamai.log import logger, error_or_exception


class Commander(Plugin):
    async def handle(self) -> None:
        if self.event.message == "/reload":
            logger.info("正在重载插件")
            await self.bot.reload_plugins()
            await self.event.reply("插件已重载")
        elif self.event.message == "/restart":
            logger.info("正在重启 Bot")
            await self.bot.restart()
            await self.event.reply("Bot 已重启")

    async def rule(self) -> bool:
        error_or_exception(f"Commander: {self.event.message}", None, True)
        return str(self.event.message) in ["/reload", "/restart", "/res"]
