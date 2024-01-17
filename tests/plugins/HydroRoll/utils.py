import re
import time
import random
from abc import ABC, abstractmethod
from typing import Type, Union, Generic, TypeVar
from iamai import Plugin
from iamai.typing import T_State
from iamai.adapter.cqhttp.event import GroupMessageEvent, PrivateMessageEvent

from .config import BasePluginConfig, RegexPluginConfig, CommandPluginConfig

T_Config = TypeVar("T_Config", bound=BasePluginConfig)
T_RegexPluginConfig = TypeVar("T_RegexPluginConfig", bound=RegexPluginConfig)
T_CommandPluginConfig = TypeVar("T_CommandPluginConfig", bound=CommandPluginConfig)


class BasePlugin(
    Plugin[Union[PrivateMessageEvent, GroupMessageEvent], T_State, T_Config],
    ABC,
    Generic[T_State, T_Config],
):
    Config: Type[T_Config] = BasePluginConfig

    def format_str(self, format_str: str, message_str: str = "") -> str:
        return format_str.format(
            message=message_str,
            user_name=self.event.sender.nickname,
            user_id=self.event.sender.user_id,
        )

    async def rule(self) -> bool:
        is_bot_off = False

        if self.event.adapter.name != "cqhttp":
            return False
        if self.event.type != "message":
            return False
        match_str = self.event.message.get_plain_text()
        if is_bot_off:
            if self.event.message.startswith(f"[CQ:at,qq={self.event.self_id}]"):
                match_str = re.sub(
                    rf"^\[CQ:at,qq={self.event.self_id}\]", "", match_str
                )
            elif self.event.message.startswith(f"[CQ:at,qq={self.event.self_tiny_id}]"):
                match_str = re.sub(
                    rf"^\[CQ:at,qq={self.event.self_tiny_id}\]", "", match_str
                )
            else:
                return False
        if self.config.handle_all_message:
            return self.str_match(match_str)
        elif self.config.handle_friend_message:
            if self.event.message_type == "private":
                return self.str_match(match_str)
        elif self.config.handle_group_message:
            if self.event.message_type == "group":
                if (
                    self.config.accept_group is None
                    or self.event.group_id in self.config.accept_group
                ):
                    return self.str_match(match_str)
        elif self.config.handle_group_message:
            if self.event.message_type == "guild":
                return self.str_match(match_str)
        return False

    @abstractmethod
    def str_match(self, msg_str: str) -> bool:
        raise NotImplemented


class RegexPluginBase(BasePlugin[T_State, T_RegexPluginConfig], ABC):
    msg_match: re.Match
    re_pattern: re.Pattern
    Config: Type[T_RegexPluginConfig] = RegexPluginConfig

    def str_match(self, msg_str: str) -> bool:
        msg_str = msg_str.strip()
        self.msg_match = self.re_pattern.fullmatch(msg_str)
        return bool(self.msg_match)


class CommandPluginBase(RegexPluginBase[T_State, T_CommandPluginConfig], ABC):
    command_match: re.Match
    command_re_pattern: re.Pattern
    Config: Type[T_CommandPluginConfig] = CommandPluginConfig

    def str_match(self, msg_str: str) -> bool:
        if not hasattr(self, "command_re_pattern"):
            self.command_re_pattern = re.compile(
                f'({"|".join(self.config.command_prefix)})'
                f'({"|".join(self.config.command)})'
                r"\s*(?P<command_args>.*)",
                flags=re.I if self.config.ignore_case else 0,
            )
        msg_str = msg_str.strip()
        self.command_match = self.command_re_pattern.fullmatch(msg_str)
        if not self.command_match:
            return False
        self.msg_match = self.re_pattern.fullmatch(
            self.command_match.group("command_args")
        )
        return bool(self.msg_match)


class PseudoRandomGenerator:
    """线性同余法随机数生成器"""

    def __init__(self, seed):
        self.seed = seed

    def generate(self):
        while True:
            self.seed = (self.seed * 1103515245 + 12345) % (2**31)
            yield self.seed


class HydroDice:
    """水系掷骰组件

    一些 API 相关的工具函数

    """

    def __init__(self, seed):
        self.generator = PseudoRandomGenerator(seed)

    def roll_dice(
        self,
        _counts: int | str,
        _sides: int | str,
        is_reversed: bool = False,
        streamline: bool = False,
        threshold: int | str = 5,
    ) -> str:
        """普通掷骰
        Args:
            _counts (int | str): 掷骰个数.
            _sides (int | str): 每个骰子的面数.
            is_reversed (bool, optional): 倒序输出. Defaults to False.
            streamline (bool, optional): 忽略过程. Defaults to False.
            threshold (int | str, optional): streamline 的阈值. Defaults to 5.

        Returns:
            str: 表达式结果.
        """
        rolls = []
        for _ in range(int(_counts)):
            roll = next(self.generator.generate()) % _sides + 1
            rolls.append(roll)
        total = sum(rolls)

        if streamline:
            return str(total)
        else:
            if len(rolls) > int(threshold):
                return str(total)
            rolls_str = " + ".join(str(r) for r in rolls)
            result_str = (
                f"{total} = {rolls_str}" if is_reversed else f"{rolls_str} = {total}"
            )
            return result_str
