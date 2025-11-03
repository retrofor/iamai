"""
使用配置文件运行 Bot 的简单示例
"""
import asyncio
import toml
from pathlib import Path
from iamai import Bot


async def main():
    """主函数"""
    # 加载配置
    config_file = Path(__file__).parent / "config.toml"
    config = toml.load(config_file)
    bot = Bot(config=config)
    
    try:
        await bot.run()
    except KeyboardInterrupt:
        ...
    finally:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
