"""
漂流瓶示例 - 机器人启动脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from iamai import Bot
from iamai.rule import rule
from iamai.typing import RuleContext

# 基础规则
@rule(name="help", condition="event.fields.get('content', '').startswith('help')")
async def help_rule(ctx: RuleContext):
    """帮助命令"""
    help_text = """
🤖 可用命令:
- help: 显示此帮助信息
- ping: 测试机器人响应
- bottle <消息>: 发送漂流瓶
- bottle_stats: 查看漂流瓶统计
- stats: 显示机器人统计信息
"""
    console_middleware = ctx.bot.middlewares.get('console')
    if console_middleware:
        await console_middleware.send_message(
            help_text.strip(),
            ctx.event.get_field('channel_id', 'console_channel')
        )

@rule(name="ping", condition="event.fields.get('content', '').startswith('ping')")
async def ping_rule(ctx: RuleContext):
    """Ping命令"""
    console_middleware = ctx.bot.middlewares.get('console')
    if console_middleware:
        await console_middleware.send_message(
            "🏓 Pong!",
            ctx.event.get_field('channel_id', 'console_channel')
        )

@rule(name="stats", condition="event.fields.get('content', '').startswith('stats')")
async def stats_rule(ctx: RuleContext):
    """统计命令"""
    stats = ctx.bot.get_stats()
    stats_text = f"""📊 机器人统计:
- 运行时间: {stats['uptime']:.1f}秒
- 处理事件: {stats['events_processed']}个
- 执行规则: {stats['rules_executed']}次
- 加载插件: {stats['plugins']}个
- 活跃中间件: {stats['middlewares']}个"""
    
    console_middleware = ctx.bot.middlewares.get('console')
    if console_middleware:
        await console_middleware.send_message(
            stats_text,
            ctx.event.get_field('channel_id', 'console_channel')
        )

async def main():
    """主函数"""
    # 创建机器人实例
    bot = Bot(config="./config.toml")
    
    # 添加基础规则
    bot.add_rule(help_rule)
    bot.add_rule(ping_rule)
    bot.add_rule(stats_rule)
    
    # 启动机器人
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
