"""Configuration module.

iamai uses `pydantic <https://pydantic-docs.helpmanual.io/>`_ to read configuration.
"""

from typing import Set, Union

from pydantic import BaseModel, ConfigDict, DirectoryPath, Field

__all__ = [
    "ConfigModel",
    "LogConfig",
    "BotConfig",
    "PluginConfig",
    "AdapterConfig",
    "MainConfig",
]


class ConfigModel(BaseModel):
    """iamai configuration model.

    Attributes:
        __config_name__: Configuration name.
    """

    model_config = ConfigDict(extra="allow")

    __config_name__: str = ""


class LogConfig(ConfigModel):
    """iamai log related settings.

    Attributes:
        level: log level.
        verbose_exception: Detailed exception record. When set to ``True``, exception Traceback will be added to the log.
    """

    level: Union[str, int] = "DEBUG"
    verbose_exception: bool = False


class BotConfig(ConfigModel):
    """Bot configuration.

    Attributes:
        plugins: List of plugins to be loaded, which will be loaded by the ``load_plugins()`` method of the ``Bot`` class.
        plugin_dirs: List of plugin directories to be loaded, which will be loaded by the ``load_plugins_from_dirs()`` method of the ``Bot`` class.
        adapters: A list of adapters to be loaded, which will be loaded in turn by the ``load_adapters()`` method of the ``Bot`` class.
        log: iamai log related settings.
    """

    plugins: Set[str] = Field(default_factory=set)
    plugin_dirs: Set[DirectoryPath] = Field(default_factory=set)
    adapters: Set[str] = Field(default_factory=set)
    log: LogConfig = LogConfig()


class PluginConfig(ConfigModel):
    """Plugin configuration."""


class AdapterConfig(ConfigModel):
    """Adapter configuration."""


class MainConfig(ConfigModel):
    """iamai configuration.

    Attributes:
        bot: the main configuration of iamai.
    """

    bot: BotConfig = BotConfig()
    plugin: PluginConfig = PluginConfig()
    adapter: AdapterConfig = AdapterConfig()
