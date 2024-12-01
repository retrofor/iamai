from iamai.mapper import Mapper
from typing import Dict, Any
import json
import websockets

class WSMapper(Mapper):
    """WebSocket 链接器，用于通过 WebSocket 连接接收和发送 JSON 数据。"""

    def __init__(self, engine):
        self.engine = engine
        
    async def start(self, host: str, port: int) -> None:
        """启动 WebSocket 服务器。"""
        server = await websockets.serve(self.handler, host, port)
        print(f"WebSocket server started at ws://{host}:{port}")
        await server.wait_closed()

    async def handler(self, websocket, path=""):
        """处理 WebSocket 连接。"""
        async for message in websocket:
            data = json.loads(message)
            print(f"Received data: {data}")
            # 这里可以将数据传递给规则引擎进行处理
            self.engine.run(data)
            await self.send(websocket, {"status": "received"})

    async def send(self, websocket, data: Dict[str, Any]) -> None:
        """发送 JSON 数据。"""
        await websocket.send(json.dumps(data))
        print(f"Sent data: {data}")

    async def receive(self, websocket) -> Dict[str, Any]:
        """接收 JSON 数据。"""
        data = await websocket.recv()
        print(f"Received data: {data}")
        return json.loads(data)