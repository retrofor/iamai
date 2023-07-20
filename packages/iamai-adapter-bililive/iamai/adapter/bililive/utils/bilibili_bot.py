import logging
from typing import List

from aiohttp import ClientSession

from utils.plugin import BotPlugin, DanmakuMessage, DanmakuPosition, SuperChatMessage
from utils.bilibili_api import (
    mute_user,
    send_danmu,
    add_badword,
    room_slient,
    user_cookies,
    remove_badword,
)

from ..api.blivedm import BLiveClient


class BiliLiveBot(BLiveClient):
    BOT_PLUGINS: List[BotPlugin] = []

    def __init__(
        self,
        room_id,
        uid=0,
        session: ClientSession = None,
        heartbeat_interval=30,
        ssl=True,
        loop=None,
    ):
        super().__init__(
            room_id,
            session=session,
            heartbeat_interval=heartbeat_interval,
            ssl=ssl,
            loop=loop,
        )
        self.botid = uid
        if session is None:
            self._session._cookie_jar = user_cookies

        for bot_plugin in self.BOT_PLUGINS:
            bot_plugin.botid = uid
            bot_plugin.send_message = self.send_message
            bot_plugin.add_badword = self.add_badword
            bot_plugin.remove_badword = self.remove_badword
            bot_plugin.mute_user = self.mute_user
            bot_plugin.room_slient_on = self.room_slient_on
            bot_plugin.room_slient_off = self.room_slient_off

    """
    -> bool: 返回操作成功與否

    """

    async def send_message(
        self,
        danmaku: str,
        fontsize: int = 25,
        color: int = 0xFFFFFF,
        pos: DanmakuPosition = DanmakuPosition.NORMAL,
    ) -> bool:
        # don't know what the hell is bubble
        return await send_danmu(
            msg=danmaku,
            fontsize=fontsize,
            color=color,
            pos=pos,
            roomid=self.room_id,
            bubble=0,
        )

    async def mute_user(self, uid: int) -> bool:
        return await mute_user(uid, self.room_id)

    # "level" | "medal" | "member" | "off"
    async def room_slient_on(
        self, slientType: str = "off", minute: int = 0, level: int = 1
    ) -> bool:
        return await room_slient(self.room_id, slientType, level, minute)

    async def room_slient_off(self) -> bool:
        return await room_slient(self.room_id, "off", 1, 0)

    async def add_badword(self, badword: str) -> bool:
        return await add_badword(self.room_id, badword)

    async def remove_badword(self, badword: str) -> bool:
        return await remove_badword(self.room_id, badword)

    """
    執行插件所有處理

    """

    async def on_command_received(self, cmd, data):
        if self.is_bot_itself(cmd, data):
            return
        logging.debug(f"從房間 {self.room_id} 收到指令: {cmd}")
        for bot_plugin in self.BOT_PLUGINS:
            try:
                await bot_plugin.on_command_received(cmd, data)
            except Exception as e:
                logging.warning(
                    f"执行插件 {get_type_name(bot_plugin)} 时出现错误({get_type_name(e)}): {e}"
                )

    async def _on_receive_popularity(self, popularity: int):
        logging.debug(f"從房間 {self.room_id} 收到人氣值: {popularity}")
        for bot_plugin in self.BOT_PLUGINS:
            try:
                await bot_plugin.on_receive_popularity(popularity)
            except Exception as e:
                logging.warning(
                    f"执行插件 {get_type_name(bot_plugin)} 时出现错误({get_type_name(e)}): {e}"
                )

    # 其餘的自己過濾
    def is_bot_itself(self, cmd, data) -> bool:
        if cmd == "DANMU_MSG":
            danmu = DanmakuMessage.from_command(data["info"])
            return danmu.uid == self.botid
        elif cmd == "SUPER_CHAT_MESSAGE":
            sc = SuperChatMessage.from_command(data["data"])
            return sc.uid == self.botid
        elif cmd == "INTERACT_WORD":
            uid = data["data"]["uid"]
            return uid == self.botid
        else:
            return False


def get_type_name(ins: any) -> str:
    return type(ins).__name__
