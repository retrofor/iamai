from __future__ import annotations

import asyncio
import importlib
from pathlib import Path
from textwrap import dedent
from typing import Any

import iamai
import pytest
from iamai import Adapter, Event, Message, Plugin, Runtime

import iamai.runtime as runtime_module


_UNSET = object()


class _FakeEntryPoints(list["_FakeEntryPoint"]):
    def select(self, **params: str) -> "_FakeEntryPoints":
        return _FakeEntryPoints(
            entry_point
            for entry_point in self
            if all(getattr(entry_point, key) == value for key, value in params.items())
        )


class _FakeEntryPoint:
    def __init__(
        self,
        name: str,
        value: str,
        *,
        group: str,
        distribution: str,
        version: str = "1.0.0",
        loaded: object = _UNSET,
        error: Exception | None = None,
    ) -> None:
        self.name = name
        self.value = value
        self.group = group
        self.dist = type(
            "FakeDistribution",
            (),
            {"metadata": {"Name": distribution}, "version": version},
        )()
        self._loaded = loaded
        self._error = error

    def load(self) -> object:
        if self._error is not None:
            raise self._error
        if self._loaded is not _UNSET:
            return self._loaded
        module_name, attr_name = self.value.split(":", 1)
        return getattr(importlib.import_module(module_name), attr_name)


class _AlphaPlugin(Plugin):
    name = "alpha"


class _BetaPlugin(Plugin):
    name = "beta"


class _ZetaPlugin(Plugin):
    name = "zeta"


class _MismatchedPlugin(Plugin):
    name = "actual_plugin"


class _DuplicatePlugin(Plugin):
    name = "duplicate"


class _ReservedManagementPlugin(Plugin):
    name = "management"


class _AdapterFixture(Adapter):
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


class _AlphaAdapter(_AdapterFixture):
    name = "alpha_adapter"


class _BetaAdapter(_AdapterFixture):
    name = "beta_adapter"


class _ZetaAdapter(_AdapterFixture):
    name = "zeta_adapter"


class _MismatchedAdapter(_AdapterFixture):
    name = "actual_adapter"


class _ReservedTerminalAdapter(_AdapterFixture):
    name = "terminal"


def _install_entry_points(
    monkeypatch: pytest.MonkeyPatch,
    *entry_points: _FakeEntryPoint,
) -> None:
    monkeypatch.setattr(
        runtime_module.metadata,
        "entry_points",
        lambda: _FakeEntryPoints(entry_points),
    )


def _assert_discovery_error(
    error: Exception,
    *,
    code: str,
    group: str,
    entry_point: str,
    distributions: tuple[str, ...],
    reason: str,
) -> None:
    error_type = getattr(iamai, "ExtensionDiscoveryError", None)
    assert error_type is not None, "iamai.ExtensionDiscoveryError must be public"
    assert isinstance(error, error_type)
    expected_distributions = tuple(sorted(distributions))
    assert error.code == code
    assert error.group == group
    assert error.entry_point == entry_point
    assert error.distributions == expected_distributions
    assert error.reason == reason
    assert str(error) == (
        f"extension discovery failed: code={code}; group={group}; "
        f"entry_point={entry_point}; distribution={','.join(expected_distributions)}; "
        f"reason={reason}"
    )


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
        lambda: {
            "packaged": _FakeEntryPoint(
                "packaged",
                "pkg:PackagedPlugin",
                group="iamai.plugins",
                distribution="packaged-plugin",
            )
        },
    )

    runtime.load_plugins()

    assert runtime.plugins[0].plugin_name == "packaged"
    assert runtime.list_plugins()[0]["ref"] == "pkg:PackagedPlugin"


def test_dotted_plugin_entry_point_survives_hot_reload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_dir = tmp_path / "nested_pkg"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text(
        dedent("""
            from iamai import Plugin


            class Holder:
                class NestedPlugin(Plugin):
                    name = "nested"
            """),
        encoding="utf-8",
    )
    runtime = Runtime(_make_config(tmp_path, plugins=["nested"]), base_path=tmp_path)
    runtime.config["runtime"]["python_paths"] = [str(tmp_path)]
    runtime._apply_python_paths()
    nested_module = importlib.import_module("nested_pkg")

    monkeypatch.setattr(
        runtime,
        "_plugin_entry_points_by_name",
        lambda: {
            "nested": _FakeEntryPoint(
                "nested",
                "nested_pkg:Holder.NestedPlugin [feature]",
                group="iamai.plugins",
                distribution="nested-plugin",
                loaded=nested_module.Holder.NestedPlugin,
            )
        },
    )

    runtime.load_plugins()
    first_type = type(runtime.plugins[0])
    asyncio.run(runtime.reload_plugins())

    assert runtime.plugins[0].plugin_name == "nested"
    assert type(runtime.plugins[0]) is not first_type


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
            "child": _FakeEntryPoint(
                "child",
                "plugins_pkg:ChildPlugin",
                group="iamai.plugins",
                distribution="child-plugin",
            ),
            "base": _FakeEntryPoint(
                "base",
                "plugins_pkg:BasePlugin",
                group="iamai.plugins",
                distribution="base-plugin",
            ),
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
        lambda: {
            "packaged_adapter": _FakeEntryPoint(
                "packaged_adapter",
                "adapter_pkg:PackagedAdapter",
                group="iamai.adapters",
                distribution="packaged-adapter",
            )
        },
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
        lambda: {
            "auto_adapter": _FakeEntryPoint(
                "auto_adapter",
                "auto_adapter_pkg:AutoAdapter",
                group="iamai.adapters",
                distribution="auto-adapter",
            )
        },
    )

    runtime.load_adapters()

    assert runtime.adapters[0].name == "auto_adapter"


def test_duplicate_entry_points_report_every_distribution_in_sorted_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_entry_points(
        monkeypatch,
        _FakeEntryPoint(
            "duplicate",
            f"{__name__}:_DuplicatePlugin",
            group="iamai.plugins",
            distribution="zeta-extension",
            version="2.0.0",
            loaded=_DuplicatePlugin,
        ),
        _FakeEntryPoint(
            "duplicate",
            f"{__name__}:_DuplicatePlugin",
            group="iamai.plugins",
            distribution="alpha-extension",
            version="3.0.0",
            loaded=_DuplicatePlugin,
        ),
    )
    runtime = Runtime(_make_config(tmp_path), base_path=tmp_path)
    runtime.config["runtime"]["auto_discover_plugins"] = True

    with pytest.raises(Exception) as exc_info:
        runtime.load_plugins()

    _assert_discovery_error(
        exc_info.value,
        code="duplicate_entry_point",
        group="iamai.plugins",
        entry_point="duplicate",
        distributions=("zeta-extension==2.0.0", "alpha-extension==3.0.0"),
        reason="multiple installed distributions publish the same entry point",
    )


def test_plugin_entry_point_cannot_shadow_builtin_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_entry_points(
        monkeypatch,
        _FakeEntryPoint(
            "management",
            f"{__name__}:_ReservedManagementPlugin",
            group="iamai.plugins",
            distribution="third-party-management",
            loaded=_ReservedManagementPlugin,
        ),
    )
    runtime = Runtime(_make_config(tmp_path), base_path=tmp_path)
    runtime.config["runtime"]["auto_discover_plugins"] = True

    with pytest.raises(Exception) as exc_info:
        runtime.load_plugins()

    _assert_discovery_error(
        exc_info.value,
        code="reserved_entry_point",
        group="iamai.plugins",
        entry_point="management",
        distributions=("third-party-management==1.0.0",),
        reason="entry point name is reserved by a built-in extension",
    )


def test_adapter_entry_point_cannot_shadow_builtin_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_entry_points(
        monkeypatch,
        _FakeEntryPoint(
            "terminal",
            f"{__name__}:_ReservedTerminalAdapter",
            group="iamai.adapters",
            distribution="third-party-terminal",
            loaded=_ReservedTerminalAdapter,
        ),
    )
    runtime = Runtime(_make_config(tmp_path), base_path=tmp_path)
    runtime.config["runtime"]["auto_discover_adapters"] = True

    with pytest.raises(Exception) as exc_info:
        runtime.load_adapters()

    _assert_discovery_error(
        exc_info.value,
        code="reserved_entry_point",
        group="iamai.adapters",
        entry_point="terminal",
        distributions=("third-party-terminal==1.0.0",),
        reason="entry point name is reserved by a built-in extension",
    )


def test_plugin_entry_point_rejects_non_plugin_object(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_entry_points(
        monkeypatch,
        _FakeEntryPoint(
            "wrong_plugin",
            "builtins:object",
            group="iamai.plugins",
            distribution="wrong-plugin",
            loaded=object(),
        ),
    )
    runtime = Runtime(_make_config(tmp_path, plugins=["wrong_plugin"]), base_path=tmp_path)

    with pytest.raises(Exception) as exc_info:
        runtime.load_plugins()

    _assert_discovery_error(
        exc_info.value,
        code="invalid_object",
        group="iamai.plugins",
        entry_point="wrong_plugin",
        distributions=("wrong-plugin==1.0.0",),
        reason="loaded object is not a Plugin subclass",
    )


def test_adapter_entry_point_rejects_non_adapter_object(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_entry_points(
        monkeypatch,
        _FakeEntryPoint(
            "wrong_adapter",
            "builtins:object",
            group="iamai.adapters",
            distribution="wrong-adapter",
            loaded=object(),
        ),
    )
    runtime = Runtime(_make_config(tmp_path, adapters=["wrong_adapter"]), base_path=tmp_path)

    with pytest.raises(Exception) as exc_info:
        runtime.load_adapters()

    _assert_discovery_error(
        exc_info.value,
        code="invalid_object",
        group="iamai.adapters",
        entry_point="wrong_adapter",
        distributions=("wrong-adapter==1.0.0",),
        reason="loaded object is not an Adapter subclass",
    )


def test_plugin_entry_point_name_must_match_plugin_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_entry_points(
        monkeypatch,
        _FakeEntryPoint(
            "declared_plugin",
            f"{__name__}:_MismatchedPlugin",
            group="iamai.plugins",
            distribution="mismatched-plugin",
            loaded=_MismatchedPlugin,
        ),
    )
    runtime = Runtime(_make_config(tmp_path, plugins=["declared_plugin"]), base_path=tmp_path)

    with pytest.raises(Exception) as exc_info:
        runtime.load_plugins()

    _assert_discovery_error(
        exc_info.value,
        code="name_mismatch",
        group="iamai.plugins",
        entry_point="declared_plugin",
        distributions=("mismatched-plugin==1.0.0",),
        reason="loaded Plugin.name is 'actual_plugin'",
    )


def test_adapter_entry_point_name_must_match_adapter_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_entry_points(
        monkeypatch,
        _FakeEntryPoint(
            "declared_adapter",
            f"{__name__}:_MismatchedAdapter",
            group="iamai.adapters",
            distribution="mismatched-adapter",
            loaded=_MismatchedAdapter,
        ),
    )
    runtime = Runtime(_make_config(tmp_path, adapters=["declared_adapter"]), base_path=tmp_path)

    with pytest.raises(Exception) as exc_info:
        runtime.load_adapters()

    _assert_discovery_error(
        exc_info.value,
        code="name_mismatch",
        group="iamai.adapters",
        entry_point="declared_adapter",
        distributions=("mismatched-adapter==1.0.0",),
        reason="loaded Adapter.name is 'actual_adapter'",
    )


def test_entry_point_load_failure_preserves_original_cause(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    load_error = ImportError("missing optional dependency")
    _install_entry_points(
        monkeypatch,
        _FakeEntryPoint(
            "broken",
            "iamai.plugins.management:ManagementPlugin",
            group="iamai.plugins",
            distribution="broken-plugin",
            loaded=_ReservedManagementPlugin,
            error=load_error,
        ),
    )
    runtime = Runtime(_make_config(tmp_path, plugins=["broken"]), base_path=tmp_path)

    with pytest.raises(Exception) as exc_info:
        runtime.load_plugins()

    _assert_discovery_error(
        exc_info.value,
        code="load_failed",
        group="iamai.plugins",
        entry_point="broken",
        distributions=("broken-plugin==1.0.0",),
        reason="entry point load raised ImportError: missing optional dependency",
    )
    assert exc_info.value.__cause__ is load_error


def test_auto_discovery_order_is_deterministic_across_groups(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_entry_points(
        monkeypatch,
        _FakeEntryPoint(
            "zeta_adapter",
            f"{__name__}:_ZetaAdapter",
            group="iamai.adapters",
            distribution="zeta-adapter",
            loaded=_ZetaAdapter,
        ),
        _FakeEntryPoint(
            "zeta",
            f"{__name__}:_ZetaPlugin",
            group="iamai.plugins",
            distribution="zeta-plugin",
            loaded=_ZetaPlugin,
        ),
        _FakeEntryPoint(
            "alpha_adapter",
            f"{__name__}:_AlphaAdapter",
            group="iamai.adapters",
            distribution="alpha-adapter",
            loaded=_AlphaAdapter,
        ),
        _FakeEntryPoint(
            "alpha",
            f"{__name__}:_AlphaPlugin",
            group="iamai.plugins",
            distribution="alpha-plugin",
            loaded=_AlphaPlugin,
        ),
    )
    runtime = Runtime(_make_config(tmp_path), base_path=tmp_path)
    runtime.config["runtime"]["auto_discover_plugins"] = True
    runtime.config["runtime"]["auto_discover_adapters"] = True

    runtime.load_plugins()
    runtime.load_adapters()

    assert [plugin.plugin_name for plugin in runtime.plugins] == ["alpha", "zeta"]
    assert [adapter.name for adapter in runtime.adapters] == [
        "alpha_adapter",
        "zeta_adapter",
    ]


def test_auto_discovery_appends_sorted_entries_without_reordering_explicit_references(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_entry_points(
        monkeypatch,
        _FakeEntryPoint(
            "alpha",
            f"{__name__}:_AlphaPlugin",
            group="iamai.plugins",
            distribution="alpha-plugin",
            loaded=_AlphaPlugin,
        ),
        _FakeEntryPoint(
            "zeta",
            f"{__name__}:_ZetaPlugin",
            group="iamai.plugins",
            distribution="zeta-plugin",
            loaded=_ZetaPlugin,
        ),
        _FakeEntryPoint(
            "beta",
            f"{__name__}:_BetaPlugin",
            group="iamai.plugins",
            distribution="beta-plugin",
            loaded=_BetaPlugin,
        ),
        _FakeEntryPoint(
            "alpha_adapter",
            f"{__name__}:_AlphaAdapter",
            group="iamai.adapters",
            distribution="alpha-adapter",
            loaded=_AlphaAdapter,
        ),
        _FakeEntryPoint(
            "zeta_adapter",
            f"{__name__}:_ZetaAdapter",
            group="iamai.adapters",
            distribution="zeta-adapter",
            loaded=_ZetaAdapter,
        ),
        _FakeEntryPoint(
            "beta_adapter",
            f"{__name__}:_BetaAdapter",
            group="iamai.adapters",
            distribution="beta-adapter",
            loaded=_BetaAdapter,
        ),
    )
    runtime = Runtime(
        _make_config(
            tmp_path,
            plugins=["zeta", "beta"],
            adapters=["zeta_adapter", "beta_adapter"],
        ),
        base_path=tmp_path,
    )
    runtime.config["runtime"]["auto_discover_plugins"] = True
    runtime.config["runtime"]["auto_discover_adapters"] = True

    runtime.load_plugins()
    runtime.load_adapters()

    assert [plugin.plugin_name for plugin in runtime.plugins] == [
        "zeta",
        "beta",
        "alpha",
    ]
    assert [adapter.name for adapter in runtime.adapters] == [
        "zeta_adapter",
        "beta_adapter",
        "alpha_adapter",
    ]


def test_explicit_loading_ignores_unrequested_broken_entry_points(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_entry_points(
        monkeypatch,
        _FakeEntryPoint(
            "alpha",
            f"{__name__}:_AlphaPlugin",
            group="iamai.plugins",
            distribution="alpha-plugin",
            loaded=_AlphaPlugin,
        ),
        _FakeEntryPoint(
            "broken_plugin",
            "broken_plugin:BrokenPlugin",
            group="iamai.plugins",
            distribution="broken-plugin",
            error=ImportError("unrequested plugin dependency is missing"),
        ),
        _FakeEntryPoint(
            "alpha_adapter",
            f"{__name__}:_AlphaAdapter",
            group="iamai.adapters",
            distribution="alpha-adapter",
            loaded=_AlphaAdapter,
        ),
        _FakeEntryPoint(
            "broken_adapter",
            "broken_adapter:BrokenAdapter",
            group="iamai.adapters",
            distribution="broken-adapter",
            error=ImportError("unrequested adapter dependency is missing"),
        ),
    )
    runtime = Runtime(
        _make_config(tmp_path, plugins=["alpha"], adapters=["alpha_adapter"]),
        base_path=tmp_path,
    )

    runtime.load_plugins()
    runtime.load_adapters()

    assert [plugin.plugin_name for plugin in runtime.plugins] == ["alpha"]
    assert [adapter.name for adapter in runtime.adapters] == ["alpha_adapter"]


def test_auto_discovery_reports_first_error_in_entry_point_name_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_entry_points(
        monkeypatch,
        _FakeEntryPoint(
            "zeta_broken",
            "zeta_broken:BrokenPlugin",
            group="iamai.plugins",
            distribution="zeta-broken-plugin",
            error=ImportError("zeta dependency is missing"),
        ),
        _FakeEntryPoint(
            "alpha_broken",
            "alpha_broken:BrokenPlugin",
            group="iamai.plugins",
            distribution="alpha-broken-plugin",
            error=ImportError("alpha dependency is missing"),
        ),
    )
    runtime = Runtime(_make_config(tmp_path), base_path=tmp_path)
    runtime.config["runtime"]["auto_discover_plugins"] = True

    with pytest.raises(Exception) as exc_info:
        runtime.load_plugins()

    _assert_discovery_error(
        exc_info.value,
        code="load_failed",
        group="iamai.plugins",
        entry_point="alpha_broken",
        distributions=("alpha-broken-plugin==1.0.0",),
        reason="entry point load raised ImportError: alpha dependency is missing",
    )
