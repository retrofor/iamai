"""Bot Module

The basic module of iamai, each iamai robot is a ``Bot()`` instance.
"""

import asyncio
import json
import pkgutil
import signal
import sys
import threading
import time
from collections import defaultdict
from contextlib import AsyncExitStack
from itertools import chain
from pathlib import Path
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    overload,
)

from pydantic import ValidationError, create_model

from .adapter import Adapter
from .config import AdapterConfig, ConfigModel, MainConfig, PluginConfig
from .dependencies import solve_dependencies
from .event import Event
from .exceptions import (
    GetEventTimeout,
    LoadModuleError,
    SkipException,
    StopException,
)
from .log import logger
from .plugin import Plugin, PluginLoadType
from .typing import AdapterHook, AdapterT, BotHook, EventHook, EventT
from .utils import (
    ModulePathFinder,
    get_classes_from_module_name,
    is_config_class,
    samefile,
    wrap_get_func,
)

if sys.version_info >= (3, 11):  # pragma: no cover
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib


__all__ = ["Bot"]

HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)


class Bot:
    """iamai ``Bot`` class object, defines the basic functionality  for interacting.

    Read and save configuration ``Config``, load adapters ``Adapter`` and plugins ``Plugin``, then distribute the events.

    Attributes:
        config: Bot configuration.
        should_exit: Whether the bot should enter the ready-to-exit state.
        adapters: List of currently loaded adapters.
        plugins_priority_dict: Plugin priority dictionary.
        plugin_state: Plugin status.
        global_state: Global status.
    """

    config: MainConfig
    should_exit: asyncio.Event  # pyright: ignore[reportUninitializedInstanceVariable]
    adapters: List[Adapter[Any, Any]]
    plugins_priority_dict: Dict[int, List[Type[Plugin[Any, Any, Any]]]]
    plugin_state: Dict[str, Any]
    global_state: Dict[Any, Any]

    _condition: asyncio.Condition  # Condition used to handle get # pyright: ignore[reportUninitializedInstanceVariable]
    _current_event: Optional[Event[Any]]  # Event currently pending

    _restart_flag: bool  # Restart flag
    _module_path_finder: ModulePathFinder  # Module metapath finder for finding plugins
    _raw_config_dict: Dict[str, Any]  # Original configuration dictionary
    _adapter_tasks: Set[
        "asyncio.Task[None]"
    ]  # Adapter task collection, used to hold references to adapter tasks
    _handle_event_tasks: Set[
        "asyncio.Task[None]"
    ]  # Event handling task, used to keep a reference to the adapter task

    # The following properties are not cleared on reboot
    _config_file: Optional[str]  # Configuration file
    _config_dict: Optional[Dict[str, Any]]  # Configuration dictionary
    _hot_reload: bool  # Hot-Reload

    _extend_plugins: List[
        Union[Type[Plugin[Any, Any, Any]], str, Path]
    ]  # A list of plugins loaded programmatically using the ``load_plugins()`` method
    _extend_plugin_dirs: List[
        Path
    ]  # List of plugin paths loaded programmatically using the ``load_plugins_from_dirs()`` method
    _extend_adapters: List[
        Union[Type[Adapter[Any, Any]], str]
    ]  # A list of adapters loaded programmatically using the ``load_adapter()`` method
    _bot_run_hooks: List[BotHook]
    _bot_exit_hooks: List[BotHook]
    _adapter_startup_hooks: List[AdapterHook]
    _adapter_run_hooks: List[AdapterHook]
    _adapter_shutdown_hooks: List[AdapterHook]
    _event_preprocessor_hooks: List[EventHook]
    _event_postprocessor_hooks: List[EventHook]

    def __init__(
        self,
        *,
        config_file: Optional[str] = "config.toml",
        config_dict: Optional[Dict[str, Any]] = None,
        hot_reload: bool = False,
    ) -> None:
        """Initialize iamai, read configuration files, create configurations, load adapters and plug-ins.

        Args:
            config_file: Configuration file, if not specified, the default ``config.toml`` will be used.
                If specified as ``None``, the configuration file will not be loaded.
            config_dict: Configuration dictionary, default is ``None``.
                If a dictionary is specified, the ``config_file`` configuration will be ignored and the configuration file will no longer be read.
            hot_reload: hot reload.
                When enabled, plugin files in ``plugin_dir`` will be automatically checked for updates and automatically reloaded when updated.
        """
        self.config = MainConfig()
        self.plugins_priority_dict = defaultdict(list)
        self.plugin_state = defaultdict(lambda: None)
        self.global_state = {}

        self.adapters = []
        self._current_event = None
        self._restart_flag = False
        self._module_path_finder = ModulePathFinder()
        self._raw_config_dict = {}
        self._adapter_tasks = set()
        self._handle_event_tasks = set()

        self._config_file = config_file
        self._config_dict = config_dict
        self._hot_reload = hot_reload

        self._extend_plugins = []
        self._extend_plugin_dirs = []
        self._extend_adapters = []
        self._bot_run_hooks = []
        self._bot_exit_hooks = []
        self._adapter_startup_hooks = []
        self._adapter_run_hooks = []
        self._adapter_shutdown_hooks = []
        self._event_preprocessor_hooks = []
        self._event_postprocessor_hooks = []

        sys.meta_path.insert(0, self._module_path_finder)

    @property
    def plugins(self) -> List[Type[Plugin[Any, Any, Any]]]:
        """List of currently loaded plugins."""
        return list(chain(*self.plugins_priority_dict.values()))

    def run(self) -> None:
        """Run iamai, monitor and intercept system exit signals, and update robot configuration."""
        self._restart_flag = True
        while self._restart_flag:
            self._restart_flag = False
            asyncio.run(self._run())
            if self._restart_flag:
                self._load_plugins_from_dirs(*self._extend_plugin_dirs)
                self._load_plugins(*self._extend_plugins)
                self._load_adapters(*self._extend_adapters)

    def restart(self) -> None:
        """Exit and rerun iamai."""
        logger.info("Restarting iamai...")
        self._restart_flag = True
        self.should_exit.set()

    async def _run(self) -> None:
        """Run iamai."""
        self.should_exit = asyncio.Event()
        self._condition = asyncio.Condition()

        # Monitor and intercept system exit signals to complete some aftermath work before closing the program
        if threading.current_thread() is threading.main_thread():  # pragma: no cover
            # Signals can only be processed in the main thread
            try:
                loop = asyncio.get_running_loop()
                for sig in HANDLED_SIGNALS:
                    loop.add_signal_handler(sig, self._handle_exit)
            except NotImplementedError:
                # add_signal_handler is only available under Unix, below for Windows
                for sig in HANDLED_SIGNALS:
                    signal.signal(sig, self._handle_exit)

        # Load configuration file
        self._reload_config_dict()

        # Load plugins and adapters
        self._load_plugins_from_dirs(*self.config.bot.plugin_dirs)
        self._load_plugins(*self.config.bot.plugins)
        self._load_adapters(*self.config.bot.adapters)
        self._update_config()

        # Run iamai
        logger.info("Running iamai...")

        hot_reload_task = None
        if self._hot_reload:  # pragma: no cover
            hot_reload_task = asyncio.create_task(self._run_hot_reload())

        for bot_run_hook_func in self._bot_run_hooks:
            await bot_run_hook_func(self)

        try:
            for _adapter in self.adapters:
                for adapter_startup_hook_func in self._adapter_startup_hooks:
                    await adapter_startup_hook_func(_adapter)
                try:
                    await _adapter.startup()
                except Exception as e:
                    self.error_or_exception(f"Startup adapter {_adapter!r} failed:", e)

            for _adapter in self.adapters:
                for adapter_run_hook_func in self._adapter_run_hooks:
                    await adapter_run_hook_func(_adapter)
                _adapter_task = asyncio.create_task(_adapter.safe_run())
                self._adapter_tasks.add(_adapter_task)
                _adapter_task.add_done_callback(self._adapter_tasks.discard)

            await self.should_exit.wait()

            if hot_reload_task is not None:  # pragma: no cover
                await hot_reload_task
        finally:
            for _adapter in self.adapters:
                for adapter_shutdown_hook_func in self._adapter_shutdown_hooks:
                    await adapter_shutdown_hook_func(_adapter)
                await _adapter.shutdown()

            while self._adapter_tasks:
                await asyncio.sleep(0)

            for bot_exit_hook_func in self._bot_exit_hooks:
                await bot_exit_hook_func(self)

            self.adapters.clear()
            self.plugins_priority_dict.clear()
            self._module_path_finder.path.clear()

    def _remove_plugin_by_path(
        self, file: Path
    ) -> List[Type[Plugin[Any, Any, Any]]]:  # pragma: no cover
        """Remove loaded plugins based on path."""
        removed_plugins: List[Type[Plugin[Any, Any, Any]]] = []
        for plugins in self.plugins_priority_dict.values():
            _removed_plugins = list(
                filter(
                    lambda x: x.__plugin_load_type__ != PluginLoadType.CLASS
                    and x.__plugin_file_path__ is not None
                    and samefile(x.__plugin_file_path__, file),
                    plugins,
                )
            )
            removed_plugins.extend(_removed_plugins)
            for plugin_ in _removed_plugins:
                plugins.remove(plugin_)
                logger.info(
                    "Succeeded to remove plugin "
                    f'"{plugin_.__name__}" from file "{file}"'
                )
        return removed_plugins

    async def _run_hot_reload(self) -> None:  # pragma: no cover
        """Hot reload."""
        try:
            from watchfiles import Change, awatch
        except ImportError:
            logger.warning(
                'Hot reload needs to install "watchfiles", try "pip install watchfiles"'
            )
            return

        logger.info("Hot reload is working!")
        async for changes in awatch(
            *(
                x.resolve()
                for x in set(self._extend_plugin_dirs)
                .union(self.config.bot.plugin_dirs)
                .union(
                    {Path(self._config_file)}
                    if self._config_dict is None and self._config_file is not None
                    else set()
                )
            ),
            stop_event=self.should_exit,
        ):
            # Processed in the order of Change.deleted, Change.modified, Change.added
            # To ensure that when renaming occurs, deletions are processed first and then additions are processed
            for change_type, file_ in sorted(changes, key=lambda x: x[0], reverse=True):
                file = Path(file_)
                # Change configuration file
                if (
                    self._config_file is not None
                    and samefile(self._config_file, file)
                    and change_type == change_type.modified
                ):
                    logger.info(f'Reload config file "{self._config_file}"')
                    old_config = self.config
                    self._reload_config_dict()
                    if (
                        self.config.bot != old_config.bot
                        or self.config.adapter != old_config.adapter
                    ):
                        self.restart()
                    continue

                # Change plugin folder
                if change_type == Change.deleted:
                    # Special handling for deletion operations
                    if file.suffix != ".py":
                        file = file / "__init__.py"
                else:
                    if file.is_dir() and (file / "__init__.py").is_file():
                        # When a new directory is added and this directory contains the ``__init__.py`` file
                        # It means that what happens at this time is that a Python package is added, and the ``__init__.py`` file of this package is deemed to be added
                        file = file / "__init__.py"
                    if not (file.is_file() and file.suffix == ".py"):
                        continue

                if change_type == Change.added:
                    logger.info(f"Hot reload: Added file: {file}")
                    self._load_plugins(
                        Path(file), plugin_load_type=PluginLoadType.DIR, reload=True
                    )
                    self._update_config()
                    continue
                if change_type == Change.deleted:
                    logger.info(f"Hot reload: Deleted file: {file}")
                    self._remove_plugin_by_path(file)
                    self._update_config()
                elif change_type == Change.modified:
                    logger.info(f"Hot reload: Modified file: {file}")
                    self._remove_plugin_by_path(file)
                    self._load_plugins(
                        Path(file), plugin_load_type=PluginLoadType.DIR, reload=True
                    )
                    self._update_config()

    def _update_config(self) -> None:
        """Updated config to incorporate Config from Plugin and Adapter."""

        def update_config(
            source: Union[List[Type[Plugin[Any, Any, Any]]], List[Adapter[Any, Any]]],
            name: str,
            base: Type[ConfigModel],
        ) -> Tuple[Type[ConfigModel], ConfigModel]:
            config_update_dict: Dict[str, Any] = {}
            for i in source:
                config_class = getattr(i, "Config", None)
                if is_config_class(config_class):
                    default_value: Any
                    try:
                        default_value = config_class()
                    except ValidationError:
                        default_value = ...
                    config_update_dict[config_class.__config_name__] = (
                        config_class,
                        default_value,
                    )
            config_model = create_model(name, **config_update_dict, __base__=base)
            return config_model, config_model()

        self.config = create_model(
            "Config",
            plugin=update_config(self.plugins, "PluginConfig", PluginConfig),
            adapter=update_config(self.adapters, "AdapterConfig", AdapterConfig),
            __base__=MainConfig,
        )(**self._raw_config_dict)
        # Update the level of logging
        logger.remove()
        logger.add(sys.stderr, level=self.config.bot.log.level)

    def _reload_config_dict(self) -> None:
        """Reload the configuration file."""
        self._raw_config_dict = {}

        if self._config_dict is not None:
            self._raw_config_dict = self._config_dict
        elif self._config_file is not None:
            try:
                with Path(self._config_file).open("rb") as f:
                    if self._config_file.endswith(".json"):
                        self._raw_config_dict = json.load(f)
                    elif self._config_file.endswith(".toml"):
                        self._raw_config_dict = tomllib.load(f)
                    else:
                        self.error_or_exception(
                            "Read config file failed:",
                            OSError("Unable to determine config file type"),
                        )
            except OSError as e:
                self.error_or_exception("Can not open config file:", e)
            except (ValueError, json.JSONDecodeError, tomllib.TOMLDecodeError) as e:
                self.error_or_exception("Read config file failed:", e)

        try:
            self.config = MainConfig(**self._raw_config_dict)
        except ValidationError as e:
            self.config = MainConfig()
            self.error_or_exception("Config dict parse error:", e)
        self._update_config()

    def reload_plugins(self) -> None:
        """Manually reload all plugins."""
        self.plugins_priority_dict.clear()
        self._load_plugins(*self.config.bot.plugins)
        self._load_plugins_from_dirs(*self.config.bot.plugin_dirs)
        self._load_plugins(*self._extend_plugins)
        self._load_plugins_from_dirs(*self._extend_plugin_dirs)
        self._update_config()

    def _handle_exit(self, *_args: Any) -> None:  # pragma: no cover
        """When the robot receives the exit signal, it will handle it according to the situation."""
        logger.info("Stopping iamai...")
        if self.should_exit.is_set():
            logger.warning("Force Exit iamai...")
            sys.exit()
        else:
            self.should_exit.set()

    async def handle_event(
        self,
        current_event: Event[Any],
        *,
        handle_get: bool = True,
        show_log: bool = True,
    ) -> None:
        """Called by the adapter object, distributes events to all plug-ins according to priority, and handles plug-in signals such as ``stop`` and ``skip``.

        This method should not be called manually by the user.

        Args:
            current_event: The currently pending ``Event``.
            handle_get: Whether the current event can be captured by the get method, the default is ``True``.
            show_log: Whether to display in the log, the default is ``True``.
        """
        if show_log:
            logger.info(
                f"Adapter {current_event.adapter.name} received: {current_event!r}"
            )

        if handle_get:
            _handle_event_task = asyncio.create_task(self._handle_event())
            self._handle_event_tasks.add(_handle_event_task)
            _handle_event_task.add_done_callback(self._handle_event_tasks.discard)
            await asyncio.sleep(0)
            async with self._condition:
                self._current_event = current_event
                self._condition.notify_all()
        else:
            _handle_event_task = asyncio.create_task(self._handle_event(current_event))
            self._handle_event_tasks.add(_handle_event_task)
            _handle_event_task.add_done_callback(self._handle_event_tasks.discard)

    async def _handle_event(self, current_event: Optional[Event[Any]] = None) -> None:
        if current_event is None:
            async with self._condition:
                await self._condition.wait()
                assert self._current_event is not None
                current_event = self._current_event
            if current_event.__handled__:
                return

        for _hook_func in self._event_preprocessor_hooks:
            await _hook_func(current_event)

        for plugin_priority in sorted(self.plugins_priority_dict.keys()):
            logger.debug(
                f"Checking for matching plugins with priority {plugin_priority!r}"
            )
            stop = False
            for plugin in self.plugins_priority_dict[plugin_priority]:
                try:
                    async with AsyncExitStack() as stack:
                        _plugin = await solve_dependencies(
                            plugin,
                            use_cache=True,
                            stack=stack,
                            dependency_cache={
                                Bot: self,
                                Event: current_event,
                            },
                        )
                        if _plugin.name not in self.plugin_state:
                            plugin_state = _plugin.__init_state__()
                            if plugin_state is not None:
                                self.plugin_state[_plugin.name] = plugin_state
                        if await _plugin.rule():
                            logger.info(f"Event will be handled by {_plugin!r}")
                            try:
                                await _plugin.handle()
                            finally:
                                if _plugin.block:
                                    stop = True
                except SkipException:
                    # The plug-in requires that it skips itself and continues the current event propagation
                    continue
                except StopException:
                    # Plugin requires stopping current event propagation
                    stop = True
                except Exception as e:
                    self.error_or_exception(f'Exception in plugin "{plugin}":', e)
            if stop:
                break

        for _hook_func in self._event_postprocessor_hooks:
            await _hook_func(current_event)

        logger.info("Event Finished")

    @overload
    async def get(
        self,
        func: Optional[Callable[[Event[Any]], Union[bool, Awaitable[bool]]]] = None,
        *,
        event_type: None = None,
        adapter_type: None = None,
        max_try_times: Optional[int] = None,
        timeout: Optional[Union[int, float]] = None,
    ) -> Event[Any]: ...

    @overload
    async def get(
        self,
        func: Optional[Callable[[EventT], Union[bool, Awaitable[bool]]]] = None,
        *,
        event_type: None = None,
        adapter_type: Type[Adapter[EventT, Any]],
        max_try_times: Optional[int] = None,
        timeout: Optional[Union[int, float]] = None,
    ) -> EventT: ...

    @overload
    async def get(
        self,
        func: Optional[Callable[[EventT], Union[bool, Awaitable[bool]]]] = None,
        *,
        event_type: Type[EventT],
        adapter_type: Optional[Type[AdapterT]] = None,
        max_try_times: Optional[int] = None,
        timeout: Optional[Union[int, float]] = None,
    ) -> EventT: ...

    async def get(
        self,
        func: Optional[Callable[[Any], Union[bool, Awaitable[bool]]]] = None,
        *,
        event_type: Optional[Type[Event[Any]]] = None,
        adapter_type: Optional[Type[Adapter[Any, Any]]] = None,
        max_try_times: Optional[int] = None,
        timeout: Optional[Union[int, float]] = None,
    ) -> Event[Any]:
        """Get events that meet the specified conditions. The coroutine will wait until the adapter receives events that meet the conditions, exceeds the maximum number of events, or times out.

        Args:
            func: Coroutine or function, the function will be automatically packaged as a coroutine for execution.
                Requires an event to be accepted as a parameter and returns a Boolean value. Returns the current event when the coroutine returns ``True``.
                When ``None`` is equivalent to the input coroutine returning true for any event, that is, returning the next event received by the adapter.
            event_type: When specified, only events of the specified type are accepted, taking effect before the func condition. Defaults to ``None``.
            adapter_type: When specified, only events generated by the specified adapter will be accepted, taking effect before the func condition. Defaults to ``None``.
            max_try_times: Maximum number of events.
            timeout: timeout period.

        Returns:
            Returns events that satisfy the condition of ``func``.

        Raises:
            GetEventTimeout: Maximum number of events exceeded or timeout.
        """
        _func = wrap_get_func(func)

        try_times = 0
        start_time = time.time()
        while not self.should_exit.is_set():
            if max_try_times is not None and try_times > max_try_times:
                break
            if timeout is not None and time.time() - start_time > timeout:
                break

            async with self._condition:
                if timeout is None:
                    await self._condition.wait()
                else:
                    try:
                        await asyncio.wait_for(
                            self._condition.wait(),
                            timeout=start_time + timeout - time.time(),
                        )
                    except asyncio.TimeoutError:
                        break

                if (
                    self._current_event is not None
                    and not self._current_event.__handled__
                    and (
                        event_type is None
                        or isinstance(self._current_event, event_type)
                    )
                    and (
                        adapter_type is None
                        or isinstance(self._current_event.adapter, adapter_type)
                    )
                    and await _func(self._current_event)
                ):
                    self._current_event.__handled__ = True
                    return self._current_event

                try_times += 1

        raise GetEventTimeout

    def _load_plugin_class(
        self,
        plugin_class: Type[Plugin[Any, Any, Any]],
        plugin_load_type: PluginLoadType,
        plugin_file_path: Optional[str],
    ) -> None:
        """Load a plugin class"""
        priority = getattr(plugin_class, "priority", None)
        if isinstance(priority, int) and priority >= 0:
            for _plugin in self.plugins:
                if _plugin.__name__ == plugin_class.__name__:
                    logger.warning(
                        f'Already have a same name plugin "{_plugin.__name__}"'
                    )
            plugin_class.__plugin_load_type__ = plugin_load_type
            plugin_class.__plugin_file_path__ = plugin_file_path
            self.plugins_priority_dict[priority].append(plugin_class)
            logger.info(
                f'Succeeded to load plugin "{plugin_class.__name__}" '
                f'from class "{plugin_class!r}"'
            )
        else:
            self.error_or_exception(
                f'Load plugin from class "{plugin_class!r}" failed:',
                LoadModuleError(
                    f'Plugin priority incorrect in the class "{plugin_class!r}"'
                ),
            )

    def _load_plugins_from_module_name(
        self,
        module_name: str,
        *,
        plugin_load_type: PluginLoadType,
        reload: bool = False,
    ) -> None:
        """Load plugins from the given module."""
        try:
            plugin_classes = get_classes_from_module_name(
                module_name, Plugin, reload=reload
            )
        except ImportError as e:
            self.error_or_exception(f'Import module "{module_name}" failed:', e)
        else:
            for plugin_class, module in plugin_classes:
                self._load_plugin_class(
                    plugin_class,  # type: ignore
                    plugin_load_type,
                    module.__file__,
                )

    def _load_plugins(
        self,
        *plugins: Union[Type[Plugin[Any, Any, Any]], str, Path],
        plugin_load_type: Optional[PluginLoadType] = None,
        reload: bool = False,
    ) -> None:
        """Load plugins.

        Args:
            *plugins: plug-in class, plug-in module name or plug-in module file path. Type can be ``Type[Plugin]``, ``str`` or ``pathlib.Path``.
                If it is ``Type[Plugin]``, it will be loaded as a plug-in class.
                If it is of type ``str``, it will be loaded as the plug-in module name, and the format is the same as the Python ``import`` statement.
                    For example: ``path.of.plugin``.
                If it is of type ``pathlib.Path``, it will be loaded as the plug-in module file path.
                    For example: ``pathlib.Path("path/of/plugin")``.
            plugin_load_type: Plug-in loading type, if it is ``None``, it will be automatically determined, otherwise the specified type will be used.
            reload: Whether to reload the module.
        """
        for plugin_ in plugins:
            try:
                if isinstance(plugin_, type) and issubclass(plugin_, Plugin):
                    self._load_plugin_class(
                        plugin_, plugin_load_type or PluginLoadType.CLASS, None
                    )
                elif isinstance(plugin_, str):
                    logger.info(f'Loading plugins from module "{plugin_}"')
                    self._load_plugins_from_module_name(
                        plugin_,
                        plugin_load_type=plugin_load_type or PluginLoadType.NAME,
                        reload=reload,
                    )
                elif isinstance(plugin_, Path):
                    logger.info(f'Loading plugins from path "{plugin_}"')
                    if not plugin_.is_file():
                        raise LoadModuleError(  # noqa: TRY301
                            f'The plugin path "{plugin_}" must be a file'
                        )

                    if plugin_.suffix != ".py":
                        raise LoadModuleError(  # noqa: TRY301
                            f'The path "{plugin_}" must endswith ".py"'
                        )

                    plugin_module_name = None
                    for path in self._module_path_finder.path:
                        try:
                            if plugin_.stem == "__init__":
                                if plugin_.resolve().parent.parent.samefile(Path(path)):
                                    plugin_module_name = plugin_.resolve().parent.name
                                    break
                            elif plugin_.resolve().parent.samefile(Path(path)):
                                plugin_module_name = plugin_.stem
                                break
                        except OSError:
                            continue
                    if plugin_module_name is None:
                        rel_path = plugin_.resolve().relative_to(Path().resolve())
                        if rel_path.stem == "__init__":
                            plugin_module_name = ".".join(rel_path.parts[:-1])
                        else:
                            plugin_module_name = ".".join(
                                rel_path.parts[:-1] + (rel_path.stem,)
                            )

                    self._load_plugins_from_module_name(
                        plugin_module_name,
                        plugin_load_type=plugin_load_type or PluginLoadType.FILE,
                        reload=reload,
                    )
                else:
                    raise TypeError(  # noqa: TRY301
                        f"{plugin_} can not be loaded as plugin"
                    )
            except Exception as e:
                self.error_or_exception(f'Load plugin "{plugin_}" failed:', e)

    def load_plugins(
        self, *plugins: Union[Type[Plugin[Any, Any, Any]], str, Path]
    ) -> None:
        """Load the plugin.

        Args:
            *plugins: ``Plugin`` class, plugin module name or plug-in module file path.
                Type can be ``Type[Plugin]``, ``str`` or ``pathlib.Path``.
                If it is ``Type[Plugin]``, it will be loaded as a plug-in class.
                If it is of type ``str``, it will be loaded as the plug-in module name, and the format is the same as the Python ``import`` statement.
                    For example: ``path.of.plugin``.
                If it is of type ``pathlib.Path``, it will be loaded as the plug-in module file path.
                    For example: ``pathlib.Path("path/of/plugin")``.
        """
        self._extend_plugins.extend(plugins)

        return self._load_plugins(*plugins)

    def _load_plugins_from_dirs(self, *dirs: Path) -> None:
        """Load plug-ins from the directory. Plug-ins in modules starting with ``_`` will not be imported. The path can be a relative path or an absolute path.

        Args:
            *dirs: Module paths that store modules containing plugins.
                For example: ``pathlib.Path("path/of/plugins/")`` .
        """
        dir_list = [str(x.resolve()) for x in dirs]
        logger.info(f'Loading plugins from dirs "{", ".join(map(str, dir_list))}"')
        self._module_path_finder.path.extend(dir_list)
        for module_info in pkgutil.iter_modules(dir_list):
            if not module_info.name.startswith("_"):
                self._load_plugins_from_module_name(
                    module_info.name, plugin_load_type=PluginLoadType.DIR
                )

    def load_plugins_from_dirs(self, *dirs: Path) -> None:
        """Load plug-ins from the directory. Plug-ins in modules starting with ``_`` will not be imported. The path can be a relative path or an absolute path.

        Args:
            *dirs: Module paths that store modules containing plugins.
                For example: ``pathlib.Path("path/of/plugins/")`` .
        """
        self._extend_plugin_dirs.extend(dirs)
        self._load_plugins_from_dirs(*dirs)

    def _load_adapters(self, *adapters: Union[Type[Adapter[Any, Any]], str]) -> None:
        """Load adapter.

        Args:
            *adapters: Adapter class or adapter name, type can be ``Type[Adapter]`` or ``str``.
                If it is of type ``Type[Adapter]``, it will be loaded as an adapter class.
                If it is of type ``str``, it will be loaded as the adapter module name, and the format is the same as the Python ``import`` statement.
                    For example: ``path.of.adapter``.
        """
        for adapter_ in adapters:
            adapter_object: Adapter[Any, Any]
            try:
                if isinstance(adapter_, type) and issubclass(adapter_, Adapter):
                    adapter_object = adapter_(self)
                elif isinstance(adapter_, str):
                    adapter_classes = get_classes_from_module_name(adapter_, Adapter)
                    if not adapter_classes:
                        raise LoadModuleError(  # noqa: TRY301
                            f"Can not find Adapter class in the {adapter_} module"
                        )
                    if len(adapter_classes) > 1:
                        raise LoadModuleError(  # noqa: TRY301
                            f"More then one Adapter class in the {adapter_} module"
                        )
                    adapter_object = adapter_classes[0][0](self)  # type: ignore
                else:
                    raise TypeError(  # noqa: TRY301
                        f"{adapter_} can not be loaded as adapter"
                    )
            except Exception as e:
                self.error_or_exception(f'Load adapter "{adapter_}" failed:', e)
            else:
                self.adapters.append(adapter_object)
                logger.info(
                    f'Succeeded to load adapter "{adapter_object.__class__.__name__}" '
                    f'from "{adapter_}"'
                )

    def load_adapters(self, *adapters: Union[Type[Adapter[Any, Any]], str]) -> None:
        """Load adapter.

        Args:
            *adapters: Adapter class or adapter name, type can be ``Type[Adapter]`` or ``str``.
                If it is of type ``Type[Adapter]``, it will be loaded as an adapter class.
                If it is of type ``str``, it will be loaded as the adapter module name, and the format is the same as the Python ``import`` statement.
                    For example: ``path.of.adapter``.
        """
        self._extend_adapters.extend(adapters)
        self._load_adapters(*adapters)

    @overload
    def get_adapter(self, adapter: str) -> Adapter[Any, Any]: ...

    @overload
    def get_adapter(self, adapter: Type[AdapterT]) -> AdapterT: ...

    def get_adapter(
        self, adapter: Union[str, Type[AdapterT]]
    ) -> Union[Adapter[Any, Any], AdapterT]:
        """Get the loaded adapter by name or adapter class.

        Args:
            adapter: adapter name or adapter class.

        Returns:
            The obtained adapter object.

        Raises:
            LookupError: No adapter object with this name found.
        """
        for _adapter in self.adapters:
            if isinstance(adapter, str):
                if _adapter.name == adapter:
                    return _adapter
            elif isinstance(_adapter, adapter):
                return _adapter
        raise LookupError(f'Can not find adapter named "{adapter}"')

    def get_plugin(self, name: str) -> Type[Plugin[Any, Any, Any]]:
        """Get the loaded plugin class by name.

        Args:
            name: plugin name

        Returns:
            The obtained plug-in class.

        Raises:
            LookupError: The plugin class with this name cannot be found.
        """
        for _plugin in self.plugins:
            if _plugin.__name__ == name:
                return _plugin
        raise LookupError(f'Can not find plugin named "{name}"')

    def error_or_exception(
        self, message: str, exception: Exception
    ) -> None:  # pragma: no cover
        """Output error or exception logs based on the current Bot configuration.

        Args:
            message: message.
            exception: Exception.
        """
        if self.config.bot.log.verbose_exception:
            logger.exception(message)
        else:
            logger.error(f"{message} {exception!r}")

    def bot_run_hook(self, func: BotHook) -> BotHook:
        """Register a function when Bot starts.

        Args:
            func: the registered function.

        Returns:
            The registered function.
        """
        self._bot_run_hooks.append(func)
        return func

    def bot_exit_hook(self, func: BotHook) -> BotHook:
        """Register a function when the Bot exits.

        Args:
            func: the registered function.

        Returns:
            The registered function.
        """
        self._bot_exit_hooks.append(func)
        return func

    def adapter_startup_hook(self, func: AdapterHook) -> AdapterHook:
        """Register a function during adapter initialization.

        Args:
            func: the registered function.

        Returns:
            The registered function.
        """
        self._adapter_startup_hooks.append(func)
        return func

    def adapter_run_hook(self, func: AdapterHook) -> AdapterHook:
        """Register an adapter runtime function.

        Args:
            func: the registered function.

        Returns:
            The registered function.
        """
        self._adapter_run_hooks.append(func)
        return func

    def adapter_shutdown_hook(self, func: AdapterHook) -> AdapterHook:
        """Register a function when the adapter is closed.

        Args:
            func: the registered function.

        Returns:
            The registered function.
        """
        self._adapter_shutdown_hooks.append(func)
        return func

    def event_preprocessor_hook(self, func: EventHook) -> EventHook:
        """Register an event preprocessing function.

        Args:
            func: the registered function.

        Returns:
            The registered function.
        """
        self._event_preprocessor_hooks.append(func)
        return func

    def event_postprocessor_hook(self, func: EventHook) -> EventHook:
        """Register a post-event processing function.

        Args:
            func: the registered function.

        Returns:
            The registered function.
        """
        self._event_postprocessor_hooks.append(func)
        return func
