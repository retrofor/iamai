"""Console适配器。

"""
from asyncio import Condition

from iamai.event import Event
from iamai.adapter import Adapter

from .config import Config
from .event import ConsoleEvent

__all__ = ["ConsoleAdapter"]


class ConsoleAdapter(Adapter[ConsoleEvent, Config]):
    """Console适配器。"""

    name: str = "console"
    _msg: str = ""
    _cond: Condition
    Config = Config

    async def startup(self):
        self._cond = Condition()

    async def run(self):
        while not self.bot.should_exit.is_set():
            async with self._cond:
                await self._cond.wait()
                await self.handle_event(
                    ConsoleEvent(adapter=self, type="message", message=self._msg)
                )

    async def send(self, msg: str):
        """此方法发送的消息会直接使此适配器产生一个事件。"""
        async with self._cond:
            self._msg = msg
            self._cond.notify()
