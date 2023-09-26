import asyncio
from aiohttp import web
from iamai import Plugin
from iamai.log import logger
from .config import _format_event

server = None

class F(Plugin):
    async def handle(self) -> None:
        global server

        if str(self.event.message) == 'service on':
            # 开启端口并接收消息
            app = web.Application()
            app.router.add_post('/', self.handle_request)
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, 'localhost', 8888)

            try:
                await site.start()
                logger.info('Server started on localhost:8888')
                await self.event.reply("Server started on localhost:8888")
            except OSError:
                logger.error('Failed to start server. Port is already in use.')
                await self.event.reply("Failed to start server. Port is already in use.")
        elif str(self.event.message) == 'service off':
            if server is not None:
                # 关闭服务器
                server.close()
                await server.wait_closed()
                await self.event.reply("Server Off.")
            else:
                await self.event.reply("Server is not running.")

    async def handle_request(self, request):
        # 读取请求体内容
        data = await request.json()
        logger.info(f'Received JSON body: {data}')

        event_type = request.headers.get('X-GitHub-Event')
        if event_type in ['commit_comment', 'create', 'delete', 'fork', 'issue_comment', 'issues', 'pull_request', 'push', 'release', 'watch']:
            await self.event.adapter.call_api('send_group_msg', group_id=126211793, message=_format_event(event_type=event_type, data=data))

        # 构造响应
        response = {'message': 'Received request'}
        return web.json_response(response)

    async def rule(self) -> bool:
        return str(self.event.message) in ["service on", "service off"]
