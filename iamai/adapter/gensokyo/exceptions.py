"""GSK 适配器异常。"""
from typing import Any, ClassVar, Dict

from iamai.exceptions import AdapterException

__all__ = [
    "GSKException",
    "NetworkError",
    "ActionFailed",
    "ApiNotAvailable",
    "ApiTimeout",
]


class GSKException(AdapterException):
    """GSK 异常基类。"""


class NetworkError(GSKException):
    """网络异常。"""


class ActionFailed(GSKException):
    """API 请求成功响应，但响应表示 API 操作失败。"""

    def __init__(self, resp: Dict[str, Any]) -> None:
        """初始化。

        Args:
            resp: 返回的响应。
        """
        self.resp = resp


class ApiNotAvailable(ActionFailed):
    """API 请求返回 404，表示当前请求的 API 不可用或不存在。"""

    ERROR_CODE: ClassVar[int] = 1404


class ApiTimeout(GSKException):
    """API 请求响应超时。"""
