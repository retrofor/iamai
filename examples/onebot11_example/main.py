"""
OneBot11 完整使用示例

演示如何使用 iamai 框架快速搭建 OneBot11 机器人。
"""
import asyncio
from iamai import Bot
from iamai.middleware.onebot11 import OneBot11MiddlewareConfig


async def main():
    """主函数"""
    print("=" * 60)
    print("iamai OneBot11 Bot 示例")
    print("=" * 60)
    print()
    
    # 配置机器人
    print("📝 配置机器人...")
    config = {
        'middleware': 'onebot11',
        'onebot11_config': {
            'host': '127.0.0.1',
            'port': 3001,
            'token': '',
            'middleware_connect_type': 'websocket',
            'reconnect_interval': 3,
            'max_reconnect_attempts': 10,
            'heartbeat_interval': 30,
            'heartbeat_timeout': 10,
        }
    }
    
    print(f"  • 中间件: OneBot11")
    print(f"  • 连接地址: ws://{config['onebot11_config']['host']}:{config['onebot11_config']['port']}")
    print(f"  • 连接类型: WebSocket")
    print()
    
    # 创建机器人实例
    print("🤖 创建 Bot 实例...")
    bot = Bot(config=config)
    print(f"  • Bot 已创建")
    print(f"  • 已加载中间件数量: {len(bot.middlewares)}")
    print()
    
    # 运行机器人
    print("🚀 启动机器人...")
    print("  • 按 Ctrl+C 停止")
    print()
    
    try:
        await bot.run()
    except KeyboardInterrupt:
        print("\n⏹️  收到停止信号")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n👋 机器人已停止")


if __name__ == "__main__":
    # 运行机器人
    asyncio.run(main())
