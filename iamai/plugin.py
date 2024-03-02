"""iamai 插件。

所有 iamai 插件的基类。所有用户编写的插件必须继承自 `Plugin` 类。
"""

import inspect
from abc import ABC, abstractmethod
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    NoReturn,
    Optional,
    Tuple,
    Type,
    cast,
    final,
)
from typing_extensions import Annotated, get_args, get_origin

from .config import ConfigModel
from .dependencies import Depends
from .event import Event
from .exceptions import SkipException, StopException
from .typing import ConfigT, EventT, StateT
from .utils import is_config_class

if TYPE_CHECKING:
    from .bot import Bot

__all__ = ["Plugin", "PluginLoadType"]


class PluginLoadType(Enum):
    """Plugins loaded types."""

    DIR = "dir"
    NAME = "name"
    FILE = "file"
    CLASS = "class"


class Plugin(ABC, Generic[EventT, StateT, ConfigT]):
    """Base class for all iamai plugins.

    Attributes:
        event: The event currently being processed by this plugin.
        priority: The priority of the plugin. The smaller the number, the higher the priority. The default is 0.
        block: Whether to prevent the propagation of events after the plug-in is executed. ``True`` means blocking.
        __plugin_load_type__: Plugin load type, automatically set by iamai, reflects how this plugin is loaded.
        __plugin_file_path__: ``None`` when the plugin loading type is ``PluginLoadType.CLASS``,
            Otherwise, the location of the Python module in which the plugin is defined.
    """

    priority: ClassVar[int] = 0
    block: ClassVar[bool] = False

    # Cannot use ClassVar because PEP 526 does not allow it
    Config: Type[ConfigT]

    __plugin_load_type__: ClassVar[PluginLoadType]
    __plugin_file_path__: ClassVar[Optional[str]]

    if TYPE_CHECKING:
        event: EventT
    else:
        event = Depends(Event)

    def __init_state__(self) -> Optional[StateT]:
        """Initialize plugin state."""

    def __init_subclass__(
        cls,
        config: Optional[Type[ConfigT]] = None,
        init_state: Optional[StateT] = None,
        **_kwargs: Any,
    ) -> None:
        """Initialize subclasses.

        Args:
            config: Configuration class.
            init_state: initial state.
        """
        super().__init_subclass__()

        orig_bases: Tuple[type, ...] = getattr(cls, "__orig_bases__", ())
        for orig_base in orig_bases:
            origin_class = get_origin(orig_base)
            if inspect.isclass(origin_class) and issubclass(origin_class, Plugin):
                try:
                    _event_t, state_t, config_t = cast(
                        Tuple[EventT, StateT, ConfigT], get_args(orig_base)
                    )
                except ValueError:  # pragma: no cover
                    continue
                if (
                    config is None
                    and inspect.isclass(config_t)
                    and issubclass(config_t, ConfigModel)
                ):
                    config = config_t  # pyright: ignore
                if (
                    init_state is None
                    and get_origin(state_t) is Annotated
                    and hasattr(state_t, "__metadata__")
                ):
                    init_state = state_t.__metadata__[0]  # pyright: ignore

        if not hasattr(cls, "Config") and config is not None:
            cls.Config = config
        if cls.__init_state__ is Plugin.__init_state__ and init_state is not None:
            cls.__init_state__ = lambda _: init_state  # type: ignore

    @final
    @property
    def name(self) -> str:
        """plugin class name."""
        return self.__class__.__name__

    @final
    @property
    def bot(self) -> "Bot":
        """bot object."""
        return self.event.adapter.bot  # pylint: disable=no-member

    @final
    @property
    def config(self) -> ConfigT:
        """plugin configuration."""
        default: Any = None
        config_class = getattr(self, "Config", None)
        if is_config_class(config_class):
            return getattr(
                self.bot.config.plugin,
                config_class.__config_name__,
                default,
            )
        return default

    @final
    def stop(self) -> NoReturn:
        """Stop propagation of current events."""
        raise StopException

    @final
    def skip(self) -> NoReturn:
        """Skips itself and continues propagation of the current event."""
        raise SkipException

    @property
    def state(self) -> StateT:
        """plugin status."""
        return self.bot.plugin_state[self.name]

    @state.setter
    @final
    def state(self, value: StateT) -> None:
        self.bot.plugin_state[self.name] = value

    @abstractmethod
    async def handle(self) -> None:
        """Method to handle events. iamai will call this method when the ``rule()`` method returns ``True``. Each plugin must implement this method."""
        raise NotImplementedError

    @abstractmethod
    async def rule(self) -> bool:
        """Method to match the event. When the event is processed, this method will be called in sequence according to the priority of the plugin. When this method returns ``True``, the event will be handed over to this plugin for processing. Each plugin must implement this method.

        .. note::
            It is not recommended to implement event processing directly in this method. Please leave the specific processing of events to the ``handle()`` method.
        """
        raise NotImplementedError
