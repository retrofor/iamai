"""
最小化测试脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

try:
    # 直接导入核心模块
    from iamai.bot import Bot
    from iamai.event import Event
    from iamai.message import MessageBuilder
    from iamai.rule import rule
    from iamai.typing import RuleContext
    
    # 简单的测试规则
    @rule(name="test_help")
    async def test_help(ctx: RuleContext):
        """测试帮助命令"""
        content = ctx.event.get_field('content', '')
        if content.startswith('help'):
            print("🤖 测试机器人正在运行!")
    
    @rule(name="test_ping")
    async def test_ping(ctx: RuleContext):
        """测试ping命令"""
        content = ctx.event.get_field('content', '')
        if content.startswith('ping'):
            print("🏓 Pong!")
    
    async def main():
        """主函数"""
        print("启动测试机器人...")
        
        # 创建机器人实例（使用默认配置）
        bot = Bot()
        
        # 添加规则
        bot.add_rule(test_help)
        bot.add_rule(test_ping)
        
        print("机器人已启动，输入 'help' 或 'ping' 测试")
        print("输入 'quit' 退出")
        
        # 简单的控制台循环
        while True:
            try:
                user_input = input("> ").strip()
                if user_input.lower() == 'quit':
                    break
                
                # 创建测试事件
                message = MessageBuilder.create_console_message(
                    content=user_input,
                    user_id="test_user",
                    channel_id="test_channel"
                )
                
                event = message.to_event()
                
                # 处理事件
                await bot.process_event(event)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"错误: {e}")
        
        print("测试完成")
    
    if __name__ == "__main__":
        asyncio.run(main())

except ImportError as e:
    print(f"导入错误: {e}")
    import traceback
    traceback.print_exc()
    print("请确保已安装所需的依赖包")
