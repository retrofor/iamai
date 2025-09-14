"""
漂流瓶插件
"""
import random
from iamai.plugin import BasePlugin
from iamai.rule import rule
from iamai.typing import RuleContext

class BottlePlugin(BasePlugin):
    """漂流瓶插件"""
    
    def __init__(self, bot, config=None):
        super().__init__(bot, config)
        self.bottles = []
        self.max_bottles = self.get_config('max_bottles', 100)
    
    @rule(name="bottle_send", condition="event.fields.get('content', '').startswith('bottle')")
    async def send_bottle(self, ctx: RuleContext):
        """发送漂流瓶"""
        content = ctx.event.get_field('content', '')
        if content.startswith('bottle '):
            message = content[7:].strip()
            if message:
                # 添加到漂流瓶池
                bottle = {
                    'message': message,
                    'sender_id': ctx.event.get_field('user_id', 'unknown'),
                    'timestamp': ctx.event.timestamp
                }
                self.bottles.append(bottle)
                
                # 保持漂流瓶数量限制
                if len(self.bottles) > self.max_bottles:
                    self.bottles.pop(0)
                
                console_middleware = ctx.bot.middlewares.get('console')
                if console_middleware:
                    await console_middleware.send_message(
                        f"🌊 漂流瓶已投入大海: {message[:20]}{'...' if len(message) > 20 else ''}",
                        ctx.event.get_field('channel_id', 'console_channel')
                    )
    
    @rule(name="bottle_receive", condition="event.type == 'message'")
    async def receive_bottle(self, ctx: RuleContext):
        """随机接收漂流瓶"""
        if self.bottles and random.random() < 0.1:  # 10%概率收到漂流瓶
            bottle = random.choice(self.bottles)
            console_middleware = ctx.bot.middlewares.get('console')
            if console_middleware:
                await console_middleware.send_message(
                    f"🌊 收到漂流瓶: {bottle['message']}",
                    ctx.event.get_field('channel_id', 'console_channel')
                )
    
    @rule(name="bottle_stats", condition="event.fields.get('content', '').startswith('bottle_stats')")
    async def bottle_stats(self, ctx: RuleContext):
        """漂流瓶统计"""
        stats_text = f"🌊 漂流瓶统计: 池中共有 {len(self.bottles)} 个漂流瓶"
        console_middleware = ctx.bot.middlewares.get('console')
        if console_middleware:
            await console_middleware.send_message(
                stats_text,
                ctx.event.get_field('channel_id', 'console_channel')
            )
