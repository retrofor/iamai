import asyncio
from my_rust_module import Engine, run_engine
import json
import websockets

# 定义规则处理函数
def greeting_action(context):
    print(f"Greeting action executed: {context.get('message')}")

# 定义条件
def greeting_condition(context):
    return context.get("type") == "greeting"

# 启动引擎
if __name__ == "__main__":
    # 创建规则引擎并添加规则
    engine = Engine()
    engine.add_rule('GreetingRule', greeting_condition, greeting_action)

    # 创建 WebSocket 服务器并运行
    host = "localhost"
    port = 8765
    engine.run(host, port)

    # 异步启动
    asyncio.run(run_engine(host, port))
