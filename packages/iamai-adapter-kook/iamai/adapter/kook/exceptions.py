"""Kook 适配器异常。"""
from typing import Optional

from iamai.exceptions import AdapterException


class KookException(AdapterException):
    """Kook 异常基类。"""


class NetworkError(KookException):
    """网络异常。"""


class ActionFailed(KookException):
    """API 请求成功响应，但响应表示 API 操作失败。"""

    def __init__(self, resp):
        """
        Args:
            resp: 返回的响应。
        """
        self.resp = resp


class ApiNotAvailable(ActionFailed):
    """API 请求返回 404，表示当前请求的 API 不可用或不存在。"""


class ApiTimeout(KookException):
    """API 请求响应超时。"""


class UnauthorizedException(KookException):
    pass


class RateLimitException(KookException):
    pass


class UnsupportedMessageType(KookException):
    """
    :说明:

      在发送不支持的消息类型时抛出，开黑啦 Bot 不支持发送音频消息。
    """

    def __init__(self, message: str = ""):
        super().__init__()
        self.message = message

    def __repr__(self) -> str:
        return self.message


class UnsupportedMessageOperation(KookException):
    """
    :说明:

      在调用不支持的 Message 或 MessageSegment 操作时抛出，例如对图片类型的 MessageSegment 使用加运算。
    """

    def __init__(self, message: str = ""):
        super().__init__()
        self.message = message

    def __repr__(self) -> str:
        return self.message


class ReconnectError(KookException):
    """
    :说明:

      服务端通知客户端, 代表该连接已失效, 请重新连接。客户端收到后应该主动断开当前连接。
    """


class TokenError(KookException):
    """
    :说明:

      服务端通知客户端, 代表该连接已失效, 请重新连接。客户端收到后应该主动断开当前连接。
    """

    def __init__(self, msg: Optional[str] = None):
        super().__init__()
        self.msg = msg

    def __repr__(self):
        return f"<TokenError message={self.msg}>"

    def __str__(self):
        return self.__repr__()
