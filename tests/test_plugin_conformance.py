from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from iamai import (
    Adapter,
    Context,
    Event,
    Message,
    Plugin,
    Runtime,
    allow_all,
    deny_all,
    message_handler,
)
from iamai.plugin import BoundHandler
from iamai.testing.plugins import (
    PluginConformanceError,
    assert_plugin_config,
    assert_plugin_dependencies,
    assert_plugin_handler,
    assert_plugin_lifecycle,
    assert_plugin_metadata,
    assert_plugin_permission,
    assert_plugin_startup_failure_cleanup,
)
from iamai.validation import PluginConfigValidationError
from pydantic import BaseModel, ConfigDict, Field


def _make_runtime(tmp_path: Path) -> Runtime:
    return Runtime(
        {
            "runtime": {"adapters": [], "builtin_plugins": False},
            "adapter": {},
            "plugin": {},
            "state": {},
            "__meta__": {"root_dir": str(tmp_path)},
        },
        base_path=tmp_path,
    )


class FixtureAdapter(Adapter):
    name = "test"

    async def start(self) -> None:
        return None

    async def send_message(
        self,
        message: Message,
        *,
        event: Event | None = None,
        target: Any | None = None,
    ) -> Any:
        return message.plain_text()


class PydanticConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    greeting: str = "hello"
    retries: int = Field(default=1, ge=1)


@dataclass
class DataclassConfig:
    label: str
    enabled: bool = True


class ConformingPlugin(Plugin):
    name = "conforming"
    description = "Plugin conformance fixture."
    priority = 25
    config_model = PydanticConfig
    requires = ("database",)
    optional_requires = ("metrics",)
    load_after = ("bootstrap",)
    load_before = ("reporting",)
    state_scope = "persistent"

    @message_handler(permission=allow_all())
    async def allowed(self, ctx: Context) -> None:
        return None

    @message_handler(permission=deny_all())
    async def denied(self, ctx: Context) -> None:
        return None


class DataclassConfigPlugin(Plugin):
    name = "dataclass-config"
    config_model = DataclassConfig


def _context(
    plugin: Plugin,
    handler: BoundHandler,
) -> Context:
    runtime = plugin.runtime
    return Context(
        runtime=runtime,
        adapter=FixtureAdapter(runtime),
        plugin=plugin,
        event=Event(
            id="evt-1",
            adapter="test",
            platform="test",
            type="message",
            channel_id="room",
            user_id="alice",
            message=Message("hello"),
        ),
        handler=handler,
    )


def test_metadata_and_dependency_helpers_accept_public_contract() -> None:
    assert_plugin_metadata(ConformingPlugin)
    assert_plugin_dependencies(ConformingPlugin)


def test_metadata_helper_rejects_invalid_state_scope() -> None:
    class InvalidMetadataPlugin(Plugin):
        state_scope = "process"

    with pytest.raises(PluginConformanceError, match="state_scope"):
        assert_plugin_metadata(InvalidMetadataPlugin)


@pytest.mark.parametrize("name", ["", " leading", "trailing "])
def test_metadata_helper_rejects_invalid_explicit_name(name: str) -> None:
    invalid_plugin = type("InvalidNamePlugin", (Plugin,), {"name": name})

    with pytest.raises(PluginConformanceError, match="non-empty trimmed string"):
        assert_plugin_metadata(invalid_plugin)


def test_metadata_helper_allows_none_name_fallback() -> None:
    class ImplicitNamePlugin(Plugin):
        name = None

    assert_plugin_metadata(ImplicitNamePlugin)


def test_dependency_helper_rejects_conflicting_ordering() -> None:
    class ConflictingPlugin(Plugin):
        name = "conflicting"
        load_after = ("storage",)
        load_before = ("storage",)

    with pytest.raises(PluginConformanceError, match="both before and after"):
        assert_plugin_dependencies(ConflictingPlugin)


def test_config_helper_supports_pydantic_and_dataclass_models() -> None:
    pydantic_data, pydantic_obj = assert_plugin_config(
        ConformingPlugin,
        {"greeting": "hi", "retries": 3},
    )
    dataclass_data, dataclass_obj = assert_plugin_config(
        DataclassConfigPlugin,
        {"label": "demo"},
    )

    assert pydantic_data == {"greeting": "hi", "retries": 3}
    assert isinstance(pydantic_obj, PydanticConfig)
    assert dataclass_data == {"label": "demo", "enabled": True}
    assert dataclass_obj == DataclassConfig(label="demo")


def test_config_helper_preserves_invalid_config_reason() -> None:
    with pytest.raises(PluginConformanceError, match="configuration is invalid") as raised:
        assert_plugin_config(ConformingPlugin, {"retries": 0})

    assert isinstance(raised.value.__cause__, PluginConfigValidationError)


def test_handler_and_permission_helpers_cover_allow_and_deny(tmp_path: Path) -> None:
    plugin = ConformingPlugin(_make_runtime(tmp_path))
    allowed = assert_plugin_handler(plugin, "allowed", kind="message")
    denied = assert_plugin_handler(plugin, "denied", kind="message")

    asyncio.run(assert_plugin_permission(allowed, _context(plugin, allowed), expected=True))
    asyncio.run(assert_plugin_permission(denied, _context(plugin, denied), expected=False))


def test_permission_helper_reports_result_mismatch(tmp_path: Path) -> None:
    plugin = ConformingPlugin(_make_runtime(tmp_path))
    denied = assert_plugin_handler(plugin, "denied")

    with pytest.raises(PluginConformanceError, match="returned False; expected True"):
        asyncio.run(assert_plugin_permission(denied, _context(plugin, denied), expected=True))


def test_lifecycle_helper_accepts_sync_and_async_cleanup_checks(tmp_path: Path) -> None:
    class LifecyclePlugin(Plugin):
        name = "lifecycle"

        def __init__(self, runtime: Runtime) -> None:
            super().__init__(runtime)
            self.active = False

        async def startup(self) -> None:
            self.active = True

        async def shutdown(self) -> None:
            self.active = False

    sync_plugin = LifecyclePlugin(_make_runtime(tmp_path))
    asyncio.run(assert_plugin_lifecycle(sync_plugin, cleanup=lambda: not sync_plugin.active))

    async_plugin = LifecyclePlugin(_make_runtime(tmp_path))

    async def async_cleanup() -> bool:
        await asyncio.sleep(0)
        return not async_plugin.active

    asyncio.run(assert_plugin_lifecycle(async_plugin, cleanup=async_cleanup))


def test_lifecycle_helper_preserves_startup_failure(tmp_path: Path) -> None:
    class BrokenPlugin(Plugin):
        name = "broken"

        async def startup(self) -> None:
            raise RuntimeError("cannot connect")

    with pytest.raises(PluginConformanceError, match="startup failed") as raised:
        asyncio.run(
            assert_plugin_lifecycle(
                BrokenPlugin(_make_runtime(tmp_path)),
                cleanup=lambda: True,
            )
        )

    assert isinstance(raised.value.__cause__, RuntimeError)


def test_lifecycle_cleanup_probe_must_return_true(tmp_path: Path) -> None:
    plugin = Plugin(_make_runtime(tmp_path))

    with pytest.raises(PluginConformanceError, match="must return bool"):
        asyncio.run(assert_plugin_lifecycle(plugin, cleanup=lambda: None))  # type: ignore[arg-type]


@pytest.mark.parametrize("phase", ["startup", "shutdown", "cleanup"])
def test_lifecycle_helper_bounds_async_phases(tmp_path: Path, phase: str) -> None:
    class HangingPlugin(Plugin):
        def __init__(self, runtime: Runtime) -> None:
            super().__init__(runtime)
            self.active = False
            self.shutdown_calls = 0

        async def startup(self) -> None:
            self.active = True
            if phase == "startup":
                await asyncio.Event().wait()

        async def shutdown(self) -> None:
            self.shutdown_calls += 1
            if phase == "shutdown" and self.shutdown_calls == 1:
                await asyncio.Event().wait()
            self.active = False

    async def cleanup() -> bool:
        if phase == "cleanup":
            await asyncio.Event().wait()
        return True

    plugin = HangingPlugin(_make_runtime(tmp_path))
    with pytest.raises(PluginConformanceError, match="timeout|timed out"):
        asyncio.run(
            assert_plugin_lifecycle(
                plugin,
                cleanup=cleanup,
                timeout=0.01,
            )
        )

    assert plugin.active is False
    assert plugin.shutdown_calls >= 1


def test_startup_failure_helper_bounds_hanging_startup(tmp_path: Path) -> None:
    class HangingPlugin(Plugin):
        def __init__(self, runtime: Runtime) -> None:
            super().__init__(runtime)
            self.active = False
            self.shutdown_called = False

        async def startup(self) -> None:
            self.active = True
            await asyncio.Event().wait()

        async def shutdown(self) -> None:
            self.shutdown_called = True
            self.active = False

    plugin = HangingPlugin(_make_runtime(tmp_path))
    with pytest.raises(PluginConformanceError, match="before timeout"):
        asyncio.run(
            assert_plugin_startup_failure_cleanup(
                plugin,
                cleanup=lambda: not plugin.active,
                timeout=0.01,
            )
        )

    assert plugin.active is False
    assert plugin.shutdown_called is True


def test_lifecycle_cancellation_runs_recovery_cleanup(tmp_path: Path) -> None:
    class CancellablePlugin(Plugin):
        def __init__(self, runtime: Runtime) -> None:
            super().__init__(runtime)
            self.active = False
            self.shutdown_started = asyncio.Event()
            self.shutdown_calls = 0

        async def startup(self) -> None:
            self.active = True

        async def shutdown(self) -> None:
            self.shutdown_calls += 1
            if self.shutdown_calls == 1:
                self.shutdown_started.set()
                await asyncio.Event().wait()
            self.active = False

    async def scenario() -> CancellablePlugin:
        plugin = CancellablePlugin(_make_runtime(tmp_path))
        task = asyncio.create_task(
            assert_plugin_lifecycle(plugin, cleanup=lambda: not plugin.active)
        )
        await plugin.shutdown_started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        return plugin

    plugin = asyncio.run(scenario())

    assert plugin.active is False
    assert plugin.shutdown_calls == 2


def test_startup_failure_helper_cancellation_runs_recovery_cleanup(
    tmp_path: Path,
) -> None:
    class CancellablePlugin(Plugin):
        def __init__(self, runtime: Runtime) -> None:
            super().__init__(runtime)
            self.active = False
            self.startup_started = asyncio.Event()
            self.shutdown_called = False

        async def startup(self) -> None:
            self.active = True
            self.startup_started.set()
            await asyncio.Event().wait()

        async def shutdown(self) -> None:
            self.shutdown_called = True
            self.active = False

    async def scenario() -> CancellablePlugin:
        plugin = CancellablePlugin(_make_runtime(tmp_path))
        task = asyncio.create_task(
            assert_plugin_startup_failure_cleanup(
                plugin,
                cleanup=lambda: not plugin.active,
            )
        )
        await plugin.startup_started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        return plugin

    plugin = asyncio.run(scenario())

    assert plugin.active is False
    assert plugin.shutdown_called is True


def test_startup_failure_helper_accepts_self_cleanup(tmp_path: Path) -> None:
    class SelfCleaningPlugin(Plugin):
        name = "self-cleaning"

        def __init__(self, runtime: Runtime) -> None:
            super().__init__(runtime)
            self.active = False

        async def startup(self) -> None:
            self.active = True
            try:
                raise RuntimeError("startup failed")
            finally:
                self.active = False

    plugin = SelfCleaningPlugin(_make_runtime(tmp_path))

    async def async_cleanup() -> bool:
        await asyncio.sleep(0)
        return not plugin.active

    error = asyncio.run(
        assert_plugin_startup_failure_cleanup(
            plugin,
            cleanup=async_cleanup,
            expected_exception=RuntimeError,
        )
    )

    assert str(error) == "startup failed"


def test_startup_failure_helper_rejects_leaked_resources(tmp_path: Path) -> None:
    class LeakingPlugin(Plugin):
        name = "leaking"

        def __init__(self, runtime: Runtime) -> None:
            super().__init__(runtime)
            self.active = False

        async def startup(self) -> None:
            self.active = True
            raise RuntimeError("startup failed")

    plugin = LeakingPlugin(_make_runtime(tmp_path))

    with pytest.raises(PluginConformanceError, match="self-cleanup failed") as raised:
        asyncio.run(
            assert_plugin_startup_failure_cleanup(
                plugin,
                cleanup=lambda: not plugin.active,
                expected_exception=RuntimeError,
            )
        )

    assert isinstance(raised.value.__cause__, RuntimeError)
