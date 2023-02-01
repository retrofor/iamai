import re
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
        if self.event.adapter.name != "cqhttp":
            return False
        if self.event.type != "message":
            return False
        if self.config.handle_all_message:
            return self.str_match(self.event.message.get_plain_text())
        elif self.config.handle_friend_message:
            if self.event.message_type == "private":
                return self.str_match(self.event.message.get_plain_text())
        elif self.config.handle_group_message:
            if self.event.message_type == "group":
                if (
                    self.config.accept_group is None
                    or self.event.group_id in self.config.accept_group
                ):
                    return self.str_match(self.event.message.get_plain_text())
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
