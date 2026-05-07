from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from types import SimpleNamespace
from typing import Any

import pytest
from iamai import Runtime


def _make_config(
    tmp_path: Path,
    *,
    plugins: list[str] | None = None,
    adapters: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "runtime": {
            "adapters": adapters or [],
            "plugins": plugins or [],
            "builtin_plugins": False,
            "auto_discover_plugins": False,
            "auto_discover_adapters": False,
        },
        "adapter": {},
        "plugin": {},
        "state": {},
        "__meta__": {"root_dir": str(tmp_path)},
    }


def test_plugin_entry_point_name_can_be_loaded_explicitly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_dir = tmp_path / "pkg"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text(
        dedent("""
            from iamai import Plugin


            class PackagedPlugin(Plugin):
                name = "packaged"
                description = "packaged plugin"
            """),
        encoding="utf-8",
    )
    runtime = Runtime(_make_config(tmp_path, plugins=["packaged"]), base_path=tmp_path)
    runtime.config["runtime"]["python_paths"] = [str(tmp_path)]
    runtime._apply_python_paths()

    monkeypatch.setattr(
        runtime,
        "_plugin_entry_points_by_name",
        lambda: {"packaged": SimpleNamespace(value="pkg:PackagedPlugin")},
    )

    runtime.load_plugins()

    assert runtime.plugins[0].plugin_name == "packaged"
    assert runtime.list_plugins()[0]["ref"] == "pkg:PackagedPlugin"


def test_auto_discover_plugins_loads_entry_points_and_honors_dependencies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_dir = tmp_path / "plugins_pkg"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text(
        dedent("""
            from iamai import Plugin


            class BasePlugin(Plugin):
                name = "base"


            class ChildPlugin(Plugin):
                name = "child"
                requires = ("base",)
            """),
        encoding="utf-8",
    )
    runtime = Runtime(_make_config(tmp_path), base_path=tmp_path)
    runtime.config["runtime"]["python_paths"] = [str(tmp_path)]
    runtime.config["runtime"]["auto_discover_plugins"] = True
    runtime._apply_python_paths()

    monkeypatch.setattr(
        runtime,
        "_plugin_entry_points_by_name",
        lambda: {
            "child": SimpleNamespace(value="plugins_pkg:ChildPlugin"),
            "base": SimpleNamespace(value="plugins_pkg:BasePlugin"),
        },
    )

    runtime.load_plugins()

    assert [plugin.plugin_name for plugin in runtime.plugins] == ["base", "child"]


def test_adapter_entry_point_name_can_be_loaded_explicitly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_dir = tmp_path / "adapter_pkg"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text(
        dedent("""
            from typing import Any

            from iamai import Adapter, Event, Message


            class PackagedAdapter(Adapter):
                name = "packaged_adapter"

                async def start(self) -> None:
                    return None

                async def send_message(
                    self,
                    message: Message,
                    *,
                    event: Event | None = None,
                    target: Any | None = None,
                ) -> Any:
                    return None
            """),
        encoding="utf-8",
    )
    runtime = Runtime(_make_config(tmp_path, adapters=["packaged_adapter"]), base_path=tmp_path)
    runtime.config["runtime"]["python_paths"] = [str(tmp_path)]
    runtime._apply_python_paths()

    monkeypatch.setattr(
        runtime,
        "_adapter_entry_points_by_name",
        lambda: {"packaged_adapter": SimpleNamespace(value="adapter_pkg:PackagedAdapter")},
    )

    runtime.load_adapters()

    assert runtime.adapters[0].name == "packaged_adapter"


def test_auto_discover_adapters_loads_entry_points(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_dir = tmp_path / "auto_adapter_pkg"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text(
        dedent("""
            from typing import Any

            from iamai import Adapter, Event, Message


            class AutoAdapter(Adapter):
                name = "auto_adapter"

                async def start(self) -> None:
                    return None

                async def send_message(
                    self,
                    message: Message,
                    *,
                    event: Event | None = None,
                    target: Any | None = None,
                ) -> Any:
                    return None
            """),
        encoding="utf-8",
    )
    runtime = Runtime(_make_config(tmp_path), base_path=tmp_path)
    runtime.config["runtime"]["python_paths"] = [str(tmp_path)]
    runtime.config["runtime"]["auto_discover_adapters"] = True
    runtime._apply_python_paths()

    monkeypatch.setattr(
        runtime,
        "_adapter_entry_points_by_name",
        lambda: {"auto_adapter": SimpleNamespace(value="auto_adapter_pkg:AutoAdapter")},
    )

    runtime.load_adapters()

    assert runtime.adapters[0].name == "auto_adapter"
