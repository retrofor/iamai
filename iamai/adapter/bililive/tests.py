import time

from bilibili_api import Danmaku, Credential, sync
from bilibili_api.live import LiveRoom, LiveDanmaku

# 自己直播间号
ROOMID = 21752074
# 凭证 根据回复弹幕的账号填写
credential = Credential(
    sessdata="b62ece97%2C1705379969%2Ccdd22*71",
    bili_jct="a6e051b71890306f61b94771eb7281ab",
)
# 监听直播间弹幕
monitor = LiveDanmaku(ROOMID, credential=credential)
# 用来发送弹幕
sender = LiveRoom(ROOMID, credential=credential)


@monitor.on("DANMU_MSG")
async def recv(event):
    # 发送者UID
    print(event)
    uid = event["data"]["info"][2][0]
    # 排除自己发送的弹幕
    # if uid == UID:
    #     return
    # 弹幕文本
    msg = event["data"]["info"][1]
    if str(msg).startswith("1"):
        # 发送弹幕
        await sender.send_danmaku(Danmaku(str(time.time())))


# 启动监听
sync(monitor.connect())
