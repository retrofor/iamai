from __future__ import annotations

from pathlib import Path
from typing import Any

from iamai import Plugin, Runtime, command, message_handler


def _make_runtime(tmp_path: Path) -> Runtime:
    return Runtime(
        {
            "runtime": {"adapters": [], "plugins": [], "builtin_plugins": False},
            "adapter": {},
            "plugin": {},
            "state": {},
            "__meta__": {"root_dir": str(tmp_path)},
        },
        base_path=tmp_path,
    )


class AlphaPlugin(Plugin):
    name = "alpha"

    @command("alpha", priority=10, block=True)
    async def alpha_command(self) -> None:
        return None


class ObserverPlugin(Plugin):
    name = "observer"
    seen_handlers: list[str]
    seen_plugins: list[str]

    def __init__(self, runtime: Runtime) -> None:
        super().__init__(runtime)
        self.seen_handlers = []
        self.seen_plugins = []

    @message_handler(startswith=("inspect",), priority=20)
    async def inspect_message(self) -> None:
        return None

    async def startup(self) -> None:
        self.seen_handlers = [
            f"{handler.plugin.plugin_name}.{handler.spec.func_name}"
            for handler in self.runtime.iter_handlers()
        ]
        self.seen_plugins = [plugin["name"] for plugin in self.runtime.list_plugins()]


def test_plugins_can_inspect_loaded_plugins_and_all_bound_handlers(
    tmp_path: Path,
) -> None:
    runtime = _make_runtime(tmp_path)
    plugins = [AlphaPlugin(runtime), ObserverPlugin(runtime)]
    for index, plugin in enumerate(plugins):
        plugin.load_index = index
        plugin.plugin_ref = plugin.__class__.__module__ + ":" + plugin.__class__.__name__
    runtime._set_plugins(plugins, [])

    observer = runtime.get_plugin("observer")
    assert isinstance(observer, ObserverPlugin)

    handlers = runtime.iter_handlers()
    assert [handler.plugin.plugin_name for handler in handlers] == ["alpha", "observer"]
    assert [handler.spec.func_name for handler in handlers] == [
        "alpha_command",
        "inspect_message",
    ]

    import asyncio

    asyncio.run(observer.startup())

    assert observer.seen_handlers == ["alpha.alpha_command", "observer.inspect_message"]
    assert observer.seen_plugins == ["alpha", "observer"]


def test_list_handlers_returns_json_friendly_handler_metadata(tmp_path: Path) -> None:
    runtime = _make_runtime(tmp_path)
    plugin = AlphaPlugin(runtime)
    plugin.load_index = 0
    runtime._set_plugins([plugin], [])

    payload: list[dict[str, Any]] = runtime.list_handlers()

    assert payload == [
        {
            "plugin": "alpha",
            "name": "alpha_command",
            "kind": "command",
            "commands": ["alpha"],
            "prefixes": [],
            "adapters": [],
            "event_types": ["message"],
            "detail_types": [],
            "startswith": [],
            "contains": [],
            "regex": None,
            "priority": 10,
            "block": True,
            "rule": False,
            "permission": False,
            "callback": f"{AlphaPlugin.alpha_command.__module__}.AlphaPlugin.alpha_command",
        }
    ]
    assert runtime.health()["handlers"] == 1
