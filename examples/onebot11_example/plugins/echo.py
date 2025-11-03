from iamai import Plugin
from typing import Dict, Any
from iamai.logger import get_logger

logger = get_logger(__name__)
class EchoPlugin(Plugin):
    name = "Echo"
    priority = 10
    
    async def on_startup(self) -> None:
        logger.info(f"{self.name} 插件已启动")
    
    async def on_shutdown(self) -> None:
        logger.info(f"{self.name} 插件已停止")

    async def handle_message(self, data: Dict[str, Any], source: str) -> bool:
        """
        处理消息事件
        
        Args:
            data: 事件数据
            source: 事件来源
            
        Returns:
            True 表示事件已处理，不再传递给其他插件
            False 表示事件继续传递
        """
        message = data.get("message", "")
        user_id = data.get("user_id", "")
        message_type = data.get("message_type", "")
        
        logger.info(f"\n收到 {message_type} 消息")
        logger.info(f"   来自: {user_id}")
        logger.info(f"   内容: {message}")

        # 这里可以调用 API 回复消息
        # 示例: await self.send_message(...)
        
        # 返回 False 让其他插件也能处理这个事件
        return False
    
    async def handle(self, data: Dict[str, Any], source: str) -> bool:
        """
        处理其他类型的事件
        
        这个方法会处理所有没有专门 handler 的事件
        """
        post_type = data.get("post_type", "unknown")
        logger.info(f"\n📬 收到 {post_type} 事件 (来源: {source})")
        return False
