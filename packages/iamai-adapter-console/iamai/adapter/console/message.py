import re

from iamai.message import MessageSegment


class ConsoleMessage(MessageSegment[None]):
    """Console 适配器消息。"""

    @property
    def _message_class(self) -> None:
        return None

    def is_text(self) -> bool:
        return self.type == "text"


def escape_tag(s: str) -> str:
    """用于记录带颜色日志时转义 `<tag>` 类型特殊标签

    参考: [loguru color 标签](https://loguru.readthedocs.io/en/stable/api/logger.html#color)

    参数:
        s: 需要转义的字符串
    """
    return re.sub(r"</?((?:[fb]g\s)?[^<>\s]*)>", r"\\\g<0>", s)
