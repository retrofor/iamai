import asyncio
import json
from iamai import Plugin
from iamai.log import logger

class F(Plugin):
    async def handle(self) -> None:

        # 开启端口并接收消息
        server = await asyncio.start_server(self.handle_client, 'localhost', 8888)
        logger.info('Server started on localhost:8888')

        # # 等待直到插件被停止
        # await self.wait()

        # # 关闭服务器
        # server.close()
        # await server.wait_closed()

    async def handle_client(self, reader, writer):
        # 读取客户端消息
        data = await reader.read(99999)
        message = data.decode()

        data_dict = {}
        lines = message.split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                data_dict[key.strip()] = value.strip()

        logger.info(data_dict)

        response = 'Received message: ' + message
        writer.write(response.encode())
        await writer.drain()

        writer.close()

    async def rule(self) -> bool:
        return str(self.event.message) == '1'