from enum import IntEnum
from abc import abstractmethod

from utils.file_loader import load_config as load_plugin_config


def load_config(yml: str, default: dict = {}) -> any:
    return load_plugin_config(yml, default)


class DanmakuPosition(IntEnum):
    TOP = (5,)
    BOTTOM = (4,)
    NORMAL = 1


class BotPlugin:
    def __init__(self) -> None:
        self.botid = -1

    """
    收到指令时
    """

    @abstractmethod
    async def on_command_received(self, cmd, data):
        pass

    """
    收到人气时
    """

    @abstractmethod
    async def on_receive_popularity(self, popularity: int):
        pass

    """
    发送弹幕
    """

    async def send_message(
        self,
        danmaku: str,
        fontsize: int = 25,
        color: int = 0xFFFFFF,
        pos: DanmakuPosition = DanmakuPosition.NORMAL,
    ) -> bool:
        pass

    """
    以下所有操作全部需要房管权限

    """

    """
    禁言用户
    """

    async def mute_user(self, uid: int) -> bool:
        pass

    """
    全局禁言
    """

    # "level" | "medal" | "member"
    async def room_slient_on(self, slientType: str, minute: int, level: int) -> bool:
        pass

    """
    全局禁言关闭
    """

    async def room_slient_off(self) -> bool:
        pass

    """
    新增屏蔽字
    """

    async def add_badword(self, badword: str) -> bool:
        pass

    """
    删除屏蔽字
    """

    async def remove_badword(self, badword: str) -> bool:
        pass


"""
WS數據物件化  (from xfgryujk)
"""


class DanmakuMessage:
    def __init__(
        self,
        mode,
        font_size,
        color,
        timestamp,
        rnd,
        uid_crc32,
        msg_type,
        bubble,
        msg,
        uid,
        uname,
        admin,
        vip,
        svip,
        urank,
        mobile_verify,
        uname_color,
        medal_level,
        medal_name,
        runame,
        room_id,
        mcolor,
        special_medal,
        user_level,
        ulevel_color,
        ulevel_rank,
        old_title,
        title,
        privilege_type,
    ):
        """
        :param mode: 弹幕显示模式（滚动、顶部、底部）
        :param font_size: 字体尺寸
        :param color: 颜色
        :param timestamp: 时间戳
        :param rnd: 随机数
        :param uid_crc32: 用户ID文本的CRC32
        :param msg_type: 是否礼物弹幕（节奏风暴）
        :param bubble: 右侧评论栏气泡

        :param msg: 弹幕内容

        :param uid: 用户ID
        :param uname: 用户名
        :param admin: 是否房管
        :param vip: 是否月费老爷
        :param svip: 是否年费老爷
        :param urank: 用户身份，用来判断是否正式会员，猜测非正式会员为5000，正式会员为10000
        :param mobile_verify: 是否绑定手机
        :param uname_color: 用户名颜色

        :param medal_level: 勋章等级
        :param medal_name: 勋章名
        :param runame: 勋章房间主播名
        :param room_id: 勋章房间ID
        :param mcolor: 勋章颜色
        :param special_medal: 特殊勋章

        :param user_level: 用户等级
        :param ulevel_color: 用户等级颜色
        :param ulevel_rank: 用户等级排名，>50000时为'>50000'

        :param old_title: 旧头衔
        :param title: 头衔

        :param privilege_type: 舰队类型，0非舰队，1总督，2提督，3舰长
        """
        self.mode = mode
        self.font_size = font_size
        self.color = color
        self.timestamp = timestamp
        self.rnd = rnd
        self.uid_crc32 = uid_crc32
        self.msg_type = msg_type
        self.bubble = bubble

        self.msg = msg

        self.uid = uid
        self.uname = uname
        self.admin = admin
        self.vip = vip
        self.svip = svip
        self.urank = urank
        self.mobile_verify = mobile_verify
        self.uname_color = uname_color

        self.medal_level = medal_level
        self.medal_name = medal_name
        self.runame = runame
        self.room_id = room_id
        self.mcolor = mcolor
        self.special_medal = special_medal

        self.user_level = user_level
        self.ulevel_color = ulevel_color
        self.ulevel_rank = ulevel_rank

        self.old_title = old_title
        self.title = title

        self.privilege_type = privilege_type

    @classmethod
    def from_command(cls, info: dict):
        return cls(
            info[0][1],
            info[0][2],
            info[0][3],
            info[0][4],
            info[0][5],
            info[0][7],
            info[0][9],
            info[0][10],
            info[1],
            *info[2][:8],
            *(info[3][:6] or (0, "", "", 0, 0, 0)),
            info[4][0],
            info[4][2],
            info[4][3],
            *info[5][:2],
            info[7],
        )


class GiftMessage:
    def __init__(
        self,
        gift_name,
        num,
        uname,
        face,
        guard_level,
        uid,
        timestamp,
        gift_id,
        gift_type,
        action,
        price,
        rnd,
        coin_type,
        total_coin,
    ):
        """
        :param gift_name: 礼物名
        :param num: 礼物数量
        :param uname: 用户名
        :param face: 用户头像URL
        :param guard_level: 舰队等级，0非舰队，1总督，2提督，3舰长
        :param uid: 用户ID
        :param timestamp: 时间戳
        :param gift_id: 礼物ID
        :param gift_type: 礼物类型（未知）
        :param action: 目前遇到的有'喂食'、'赠送'
        :param price: 礼物单价瓜子数
        :param rnd: 随机数
        :param coin_type: 瓜子类型，'silver'或'gold'
        :param total_coin: 总瓜子数
        """
        self.gift_name = gift_name
        self.num = num
        self.uname = uname
        self.face = face
        self.guard_level = guard_level
        self.uid = uid
        self.timestamp = timestamp
        self.gift_id = gift_id
        self.gift_type = gift_type
        self.action = action
        self.price = price
        self.rnd = rnd
        self.coin_type = coin_type
        self.total_coin = total_coin

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            data["giftName"],
            data["num"],
            data["uname"],
            data["face"],
            data["guard_level"],
            data["uid"],
            data["timestamp"],
            data["giftId"],
            data["giftType"],
            data["action"],
            data["price"],
            data["rnd"],
            data["coin_type"],
            data["total_coin"],
        )


class GuardBuyMessage:
    def __init__(
        self,
        uid,
        username,
        guard_level,
        num,
        price,
        gift_id,
        gift_name,
        start_time,
        end_time,
    ):
        """
        :param uid: 用户ID
        :param username: 用户名
        :param guard_level: 舰队等级，0非舰队，1总督，2提督，3舰长
        :param num: 数量
        :param price: 单价金瓜子数
        :param gift_id: 礼物ID
        :param gift_name: 礼物名
        :param start_time: 开始时间戳？
        :param end_time: 结束时间戳？
        """
        self.uid = uid
        self.username = username
        self.guard_level = guard_level
        self.num = num
        self.price = price
        self.gift_id = gift_id
        self.gift_name = gift_name
        self.start_time = start_time
        self.end_time = end_time

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            data["uid"],
            data["username"],
            data["guard_level"],
            data["num"],
            data["price"],
            data["gift_id"],
            data["gift_name"],
            data["start_time"],
            data["end_time"],
        )


class SuperChatMessage:
    def __init__(
        self,
        price,
        message,
        message_jpn,
        start_time,
        end_time,
        time,
        id_,
        gift_id,
        gift_name,
        uid,
        uname,
        face,
        guard_level,
        user_level,
        background_bottom_color,
        background_color,
        background_icon,
        background_image,
        background_price_color,
    ):
        """
        :param price: 价格（人民币）
        :param message: 消息
        :param message_jpn: 消息日文翻译（目前只出现在SUPER_CHAT_MESSAGE_JPN）
        :param start_time: 开始时间戳
        :param end_time: 结束时间戳
        :param time: 剩余时间
        :param id_: str，消息ID，删除时用
        :param gift_id: 礼物ID
        :param gift_name: 礼物名
        :param uid: 用户ID
        :param uname: 用户名
        :param face: 用户头像URL
        :param guard_level: 舰队等级，0非舰队，1总督，2提督，3舰长
        :param user_level: 用户等级
        :param background_bottom_color: 底部背景色
        :param background_color: 背景色
        :param background_icon: 背景图标
        :param background_image: 背景图
        :param background_price_color: 背景价格颜色
        """
        self.price = price
        self.message = message
        self.message_jpn = message_jpn
        self.start_time = start_time
        self.end_time = end_time
        self.time = time
        self.id = id_
        self.gift_id = gift_id
        self.gift_name = gift_name
        self.uid = uid
        self.uname = uname
        self.face = face
        self.guard_level = guard_level
        self.user_level = user_level
        self.background_bottom_color = background_bottom_color
        self.background_color = background_color
        self.background_icon = background_icon
        self.background_image = background_image
        self.background_price_color = background_price_color

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            data["price"],
            data["message"],
            data["message_trans"],
            data["start_time"],
            data["end_time"],
            data["time"],
            data["id"],
            data["gift"]["gift_id"],
            data["gift"]["gift_name"],
            data["uid"],
            data["user_info"]["uname"],
            data["user_info"]["face"],
            data["user_info"]["guard_level"],
            data["user_info"]["user_level"],
            data["background_bottom_color"],
            data["background_color"],
            data["background_icon"],
            data["background_image"],
            data["background_price_color"],
        )


class SuperChatDeleteMessage:
    def __init__(self, ids):
        """
        :param ids: 消息ID数组
        """
        self.ids = ids

    @classmethod
    def from_command(cls, data: dict):
        return cls(data["ids"])
