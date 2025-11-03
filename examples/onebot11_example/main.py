"""
OneBot11 完整使用示例

演示如何使用 iamai 框架快速搭建 OneBot11 机器人。
"""

import asyncio
from iamai import Bot
from iamai.middleware.onebot11 import OneBot11MiddlewareConfig


async def main():
    config = {
        "middleware": "onebot11",
        "onebot11_config": {
            "host": "127.0.0.1",
            "port": 3001,
            "token": "",
            "middleware_connect_type": "websocket",
            "reconnect_interval": 3,
            "max_reconnect_attempts": 10,
            "heartbeat_interval": 30,
            "heartbeat_timeout": 10,
        },
    }
    bot = Bot(config=config)
    try:
        await bot.run()
    except KeyboardInterrupt:
        ...
    except Exception as e:
        print(f"{e}")
        import traceback

        traceback.print_exc()
    finally:
        ...


if __name__ == "__main__":
    # 运行机器人
    asyncio.run(main())
