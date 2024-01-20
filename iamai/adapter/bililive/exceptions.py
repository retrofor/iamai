"""Bililive 适配器异常。"""
from typing import Optional

from iamai.exceptions import AdapterException


class BililiveException(AdapterException):
    """Bililive 适配器异常基类。"""


class InitError(BililiveException):
    """初始化失败"""
