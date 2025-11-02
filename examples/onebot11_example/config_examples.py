"""
OneBot11 配置示例

演示各种配置方式。
"""

from iamai import Bot
from iamai.middleware.onebot11 import OneBot11MiddlewareConfig


# ============================================================
# 方式1: 最简配置（字典）
# ============================================================
def example1_minimal():
    """最简配置"""
    bot = Bot(
        config={
            "middleware": "onebot11",
            "onebot11_config": {
                "host": "127.0.0.1",
                "port": 3001,
            },
        }
    )
    return bot


# ============================================================
# 方式2: 完整配置（字典）
# ============================================================
def example2_full_dict():
    """完整字典配置"""
    bot = Bot(
        config={
            "middleware": "onebot11",
            "onebot11_config": {
                # 连接配置
                "host": "127.0.0.1",
                "port": 3001,
                "token": "your_access_token",  # 可选
                # 连接类型
                "middleware_connect_type": "websocket",  # 或 'reverse_websocket'
                # 重连配置
                "reconnect_interval": 3,  # 重连间隔（秒）
                "max_reconnect_attempts": 10,  # 最大重连次数
                # 心跳配置
                "heartbeat_interval": 30,  # 心跳间隔（秒）
                "heartbeat_timeout": 10,  # 心跳超时（秒）
                # 其他配置
                "enabled": True,
            },
        }
    )
    return bot


# ============================================================
# 方式3: 使用配置对象（推荐）
# ============================================================
def example3_config_object():
    """使用配置对象（推荐）"""
    # 创建配置对象
    onebot11_config = OneBot11MiddlewareConfig(
        host="127.0.0.1",
        port=3001,
        token="",
        middleware_connect_type="websocket",
        reconnect_interval=3,
        max_reconnect_attempts=10,
        heartbeat_interval=30,
        heartbeat_timeout=10,
        enabled=True,
    )

    # 创建机器人
    bot = Bot(config={"middleware": "onebot11", "onebot11_config": onebot11_config})
    return bot


# ============================================================
# 方式4: 反向 WebSocket
# ============================================================
def example4_reverse_ws():
    """反向 WebSocket 配置"""
    bot = Bot(
        config={
            "middleware": "onebot11",
            "onebot11_config": {
                "host": "0.0.0.0",  # 监听所有接口
                "port": 8080,  # 服务器端口
                "middleware_connect_type": "reverse_websocket",
            },
        }
    )
    return bot


# ============================================================
# 使用示例
# ============================================================
if __name__ == "__main__":
    import asyncio

    # 选择一个示例运行
    print("选择配置示例:")
    print("1. 最简配置")
    print("2. 完整字典配置")
    print("3. 配置对象（推荐）")
    print("4. 反向 WebSocket")

    choice = input("请输入选项 (1-4): ").strip()

    if choice == "1":
        bot = example1_minimal()
    elif choice == "2":
        bot = example2_full_dict()
    elif choice == "3":
        bot = example3_config_object()
    elif choice == "4":
        bot = example4_reverse_ws()
    else:
        print("无效选项")
        exit(1)

    print("\n🚀 启动机器人...")
    print("按 Ctrl+C 停止\n")

    asyncio.run(bot.run())
