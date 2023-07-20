import os
import time
import asyncio
import logging
from typing import Any

import qrcode
import aiohttp
from aiohttp import cookiejar
from qrcode.main import QRCode
from aiohttp.client import ClientSession
from aiohttp.client_exceptions import ClientResponseError

QRCODE_REQUEST_URL = "http://passport.bilibili.com/qrcode/getLoginUrl"
CHECK_LOGIN_RESULT = "http://passport.bilibili.com/qrcode/getLoginInfo"
SEND_URL = "https://api.live.bilibili.com/msg/send"
MUTE_USER_URL = (
    "https://api.live.bilibili.com/xlive/web-ucenter/v1/banned/AddSilentUser"
)
ROOM_SLIENT_URL = "https://api.live.bilibili.com/xlive/web-room/v1/banned/RoomSilent"
ADD_BADWORD_URL = (
    "https://api.live.bilibili.com/xlive/web-ucenter/v1/banned/AddShieldKeyword"
)
DEL_BADWORD_URL = (
    "https://api.live.bilibili.com/xlive/web-ucenter/v1/banned/DelShieldKeyword"
)


user_cookies = cookiejar.CookieJar()

"""
Bilibili Client Operation

"""


async def login(session: ClientSession) -> bool:
    if get_cookies("bili_jct") != None:
        # 無需重複獲取
        logging.info(f"先前已經登入，因此無需再度登入。")
        return True
    try:
        res = await _get(session, QRCODE_REQUEST_URL)

        ts = res["ts"]
        outdated = ts + 180 * 1000  # 180 秒後逾時
        authKey = res["data"]["oauthKey"]

        url = res["data"]["url"]
        qr = qrcode.QRCode()
        logging.info("請掃描下列二維碼進行登入... (或者到目錄下尋找 qrcode.png)")

        qr.add_data(url)
        qr.print_ascii(invert=True)
        qr.make_image().save("qrcode.png")

        while True:
            await asyncio.sleep(5)

            if time.time() > outdated:
                logging.info("已逾時。")
                return False  # 登入失敗

            res = await _post(session, CHECK_LOGIN_RESULT, oauthKey=authKey)

            if res["status"]:
                logging.info("登入成功。")
                return True
            else:
                code = res["data"]
                if code in [-1, -2]:
                    logging.warning(f'登入失敗: {res["message"]}')
                    return False

    except ClientResponseError as e:
        logging.warning(f"請求時出現錯誤: {e}")
        return False
    finally:
        os.remove("qrcode.png")


async def send_danmu(**fields) -> bool:
    token = get_cookies("bili_jct")
    async with ClientSession(cookie_jar=user_cookies) as session:
        try:
            res = await _post(
                session,
                SEND_URL,
                rnd=time.time(),
                csrf=token,
                csrf_token=token,
                **fields,
            )
            return "data" in res
        except Exception as e:
            logging.warning(f"發送彈幕時出現錯誤: {e}")
            return False


def get_cookies(name: str) -> Any:
    for cookie in user_cookies:
        if cookie.key == name:
            return cookie.value
    return None


async def mute_user(tuid: int, roomid: int) -> bool:
    token = get_cookies("bili_jct")
    async with ClientSession(cookie_jar=user_cookies) as session:
        try:
            res = await _post(
                session,
                MUTE_USER_URL,
                csrf=token,
                csrf_token=token,
                visit_id="",
                mobile_app="web",
                tuid=str(tuid),
                room_id=str(roomid),
            )
            return res["code"] == 0
        except Exception as e:
            logging.warning(f"禁言時出現錯誤: {e}")
            return False


async def room_slient(roomid: int, slientType: str, level: int, minute: int) -> bool:
    type_availables = ["off", "medal", "member", "level"]
    if slientType not in type_availables:
        logging.warning(f"未知的禁言類型: {slientType} ({type_availables})")
        return False

    minute_available = [0, 30, 60]
    if minute not in minute_available:
        logging.warning(f"未知的静音时间: {minute} ({minute_available})")
        return False

    token = get_cookies("bili_jct")
    async with ClientSession(cookie_jar=user_cookies) as session:
        try:
            res = await _post(
                session,
                ROOM_SLIENT_URL,
                csrf=token,
                csrf_token=token,
                visit_id="",
                room_id=str(roomid),
                type=str(slientType),
                minute=str(minute),
                level=str(level),
            )
            return res["code"] == 0
        except Exception as e:
            logging.warning(f"房間靜音時出現錯誤: {e}")
            return False


async def add_badword(roomid: int, keyword: str) -> bool:
    token = get_cookies("bili_jct")
    async with ClientSession(cookie_jar=user_cookies) as session:
        try:
            res = await _post(
                session,
                ADD_BADWORD_URL,
                csrf=token,
                csrf_token=token,
                visit_id="",
                room_id=str(roomid),
                keyword=keyword,
            )
            return res["code"] == 0
        except Exception as e:
            logging.warning(f"添加屏蔽字時出現錯誤: {e}")
            return False


async def remove_badword(roomid: int, keyword: str) -> bool:
    token = get_cookies("bili_jct")
    async with ClientSession(cookie_jar=user_cookies) as session:
        try:
            res = await _post(
                session,
                DEL_BADWORD_URL,
                csrf=token,
                csrf_token=token,
                visit_id="",
                room_id=str(roomid),
                keyword=keyword,
            )
            return res["code"] == 0
        except Exception as e:
            logging.warning(f"删除屏蔽字時出現錯誤: {e}")
            return False


def logout():
    user_cookies.clear()


"""
Http Request

"""


async def _get(session: ClientSession, url: str):
    async with session.get(url) as resp:
        resp.raise_for_status()
        data = await resp.json()
        logging.debug(data)
        if "code" in data and data["code"] != 0:
            raise Exception(data["message"] if "message" in data else data["code"])
        return data


async def _post(session: ClientSession, url: str, **data):
    form = aiohttp.FormData()
    for k, v in data.items():
        form.add_field(k, v)
    logging.debug(f"正在发送 POST 请求: {url}, 内容: {data}")
    async with session.post(url, data=form) as resp:
        resp.raise_for_status()
        data = await resp.json()
        logging.debug(data)
        if "code" in data and data["code"] != 0:
            raise Exception(data["message"] if "message" in data else data["code"])
        return data


if __name__ == "__main__":
    session = ClientSession(cookies={"a": 1, "b": 2})
    for c in session.cookie_jar:
        print(c.key, c.value)
