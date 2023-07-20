import json
import asyncio
import logging

from genericpath import exists
from aiohttp.client import ClientSession

from utils.bilibili_bot import BiliLiveBot
from utils.plugins_loader import load_plugins
from utils.file_loader import make_folder, load_default_config
from utils.bilibili_api import login, get_cookies, user_cookies


async def start_bot(room: int):
    cookies = {}
    # 有上次的 session
    session_exist = exists(SESSION_DATA_PATH)
    if session_exist:
        with open(SESSION_DATA_PATH) as f:
            cookies = json.load(f)
    # 加到 cookies
    user_cookies.update_cookies(cookies)
    async with ClientSession(cookie_jar=user_cookies) as session:
        # 嘗試登入
        success = await login(session)
        # 成功登入
        if success:
            uid = get_cookies("DedeUserID")
            jct = get_cookies("bili_jct")

            if uid == None or jct == None:
                logging.error(f"获取 cookies 失败")
                return
            if not session_exist:
                for cookie in user_cookies:
                    cookies[cookie.key] = cookie.value

                logging.debug(f"已储存 cookies: {cookies}")
                with open(SESSION_DATA_PATH, mode="w") as f:
                    json.dump(cookies, f)

            bot = BiliLiveBot(
                room_id=room, uid=int(uid), session=session, loop=session._loop
            )
            await bot.init_room()
            logging.info(f"機器人已啟動。")
            await bot.start()
            # while True:
            #    await asyncio.sleep(60)
            await bot.close()
            logging.info(f"機器人已關閉。")
        else:
            exit()


if __name__ == "__main__":
    make_folder("data")
    make_folder("config")
    make_folder("plugins")

    data = load_default_config()

    logging.basicConfig(level=logging.INFO if not data["debug"] else logging.DEBUG)

    room = data["roomid"]

    BiliLiveBot.BOT_PLUGINS = load_plugins()
    asyncio.run(start_bot(room))
