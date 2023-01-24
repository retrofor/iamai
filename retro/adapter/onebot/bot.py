import threading
import time
import websockets
import json
import asyncio
import uuid
import traceback
import obj
import re


class reg:
    reg_list = {
        'apps': [
            # {'re': '(.*)', 'func': <function func at 0x0000000000000000>}
        ],
        'notice': [
            # {'func': <function func at 0x0000000000000000>}
        ],
        'noticeApps': [
            # {'type': 'poke', 'func': <function func at 0x0000000000000000>}
        ],
        'request': [
            # {'func': <function func at 0x0000000000000000>}
        ],
        'requestApps': [
            # {'type': 'poke', 'func': <function func at 0x0000000000000000>}
        ],
        'msgApp': [
            # {'func': <function func at 0x0000000000000000>}
        ]
    }

    def register(self, func_tri):
        def wapper(func):
            def _wapper(*args, **kwargs):
                return func(*args, **kwargs)  # 实际上不会被调用，运行不到这一步

            self.reg_list['apps'].append({'re': func_tri, 'func': func})
            return _wapper

        return wapper

    def registerNotice(self, func):
        def wapper(*args, **kwargs):
            return func(*args, **kwargs)  # 实际上不会被调用，运行不到这一步

        self.reg_list['notice'].append({'func': func})
        return wapper

    def registerNoticeApp(self, notice_type):
        def wapper(func):
            def _wapper(*args, **kwargs):
                return func(*args, **kwargs)  # 实际上不会被调用，运行不到这一步

            self.reg_list['noticeApps'].append({'type': notice_type, 'func': func})
            return _wapper

        return wapper

    def registerRequest(self, func):
        def wapper(*args, **kwargs):
            return func(*args, **kwargs)  # 实际上不会被调用，运行不到这一步

        self.reg_list['request'].append({'func': func})
        return wapper

    def registerRequestApp(self, notice_type):
        def wapper(func):
            def _wapper(*args, **kwargs):
                return func(*args, **kwargs)  # 实际上不会被调用，运行不到这一步

            self.reg_list['requestApps'].append({'type': notice_type, 'func': func})
            return _wapper

        return wapper


class Bot:
    ws_url = 'ws://127.0.0.1:6700'
    bot = {
        'id': 10001,
        'name': 'Bot',
    }
    msg = {}
    logger = obj.logger()
    revc_api = {}
    group_list = {}
    friend_list = {}

    def __init__(self, ws_url):
        self.recv_api = {}
        self.reg = reg()
        self.ws_url = ws_url

    def run(self):
        self._run()

    def _run(self):
        try:
            self.loop = asyncio.get_event_loop()
            t = self.loop.create_task(self._runWebsocket())
            self.loop.run_until_complete(t)
            # self.loop.run_forever()
        except KeyboardInterrupt as kb:
            self.logger.info('Shutting Down!')
            self.logger.__del__()

    def stop(self):
        self.loop.stop()

    async def _runWebsocket(self):
        while True:
            async with websockets.connect(self.ws_url) as self.ws:
                threading.Thread(target=self._Bot_init).start()
                while True:
                    try:
                        res = await self.ws.recv()
                        threading.Thread(target=self._jsonParse, args=(res,)).start()  # 多线程防止堵塞
                    except (Exception, BaseException) as e:
                        print(traceback.format_exc())
                        time.sleep(5)

    async def _sendWebsocket(self, data):
        await self.ws.send(data)

    def _Bot_init(self):
        def get_group_list():  # get_group_list
            id = f'{uuid.uuid1()}'
            data = {'action': 'get_group_list', 'params': {}, 'echo': id}
            ret = self._send_data(data, id)
            gl = ret['data']
            for i in gl:
                gi = obj.group_info(
                    id=i['group_id'],
                    name=i['group_name'],
                    create_time=i['group_create_time'],
                    level=i['group_level'],
                    member_count=i['member_count'],
                    max_member_count=i['max_member_count']
                )
                self.group_list[i['group_id']] = gi
            self.logger.info(f'获取到群列表，共 {len(self.group_list)} 个。')

        def get_friend_list():
            id = f'{uuid.uuid1()}'
            data = {'action': 'get_friend_list', 'params': {}, 'echo': id}
            ret = self._send_data(data, id)
            fl = ret['data']
            for i in fl:
                fi = obj.friend_info(
                    id=i['user_id'],
                    name=i['nickname'],
                    remark=i['remark']
                )
                self.friend_list[i['user_id']] = fi
            self.logger.info(f'获取到好友列表，共 {len(self.friend_list)} 个。')

        def get_gocq_ver():
            id = f'{uuid.uuid1()}'
  
