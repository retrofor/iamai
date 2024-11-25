import re
import json
import base64
import secrets

from iamai import Plugin
from iamai.log import logger
from iamai.adapter.cqhttp.message import CQHTTPMessageSegment as ms

from .config import match_github_links
from .lib.opengraph import get_opengraph_image, indentify_message_tag


class Github(Plugin):
    async def handle(self) -> None:
        message_text = self.event.message.get_plain_text()

        # 匹配 GitHub 链接
        match = match_github_links(message_text)
        if not match:
            logger.warning("No valid GitHub link found in the message.")
            return

        # 解析匹配到的链接信息
        groups = match.groupdict()
        # message = {"id": self.event.message_id}
        # message = message | groups

        logger.info(f"message: {groups}")

        tag = indentify_message_tag(groups)

        if not tag:
            logger.warning("No valid tag found in the message.")
            return

        logger.info(f"Tag: {tag}")
        # 获取 OpenGraph 图片（示例代码）
        image = await get_opengraph_image(tag, secrets.token_urlsafe(16))
        if image:
            logger.info("Image fetched successfully!")

            # 将图片转换为 Base64 编码
            encoded_image = base64.b64encode(image).decode("utf-8")

            # 构造 CQHTTP 的图片消息格式
            cq_message = ms.image(file=f"base64://{encoded_image}")

            # 发送图片消息
            await self.event.reply(cq_message)

    async def rule(self) -> bool:
        # 判断是否为 GitHub 相关消息
        # return "github.com" in self.event.message.get_plain_text()
        return self.event.type == "message"
