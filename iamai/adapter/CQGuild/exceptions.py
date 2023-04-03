"""CQGuild 适配器异常。"""
from iamai.exceptions import AdapterException


class CQGuildException(AdapterException):
    """CQGuild 异常基类。"""


class NetworkError(CQGuildException):
    """网络异常。"""


class ActionFailed(CQGuildException):
    """API 请求成功响应，但响应表示 API 操作失败。"""

    def __init__(self, resp):
        """
        Args:
            resp: 返回的响应。
        """
        self.resp = resp


class ApiNotAvailable(ActionFailed):
    """API 请求返回 404，表示当前请求的 API 不可用或不存在。"""


class ApiTimeout(CQGuildException):
    """API 请求响应超时。"""
