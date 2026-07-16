from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
import iamai.runtime as runtime_module
from iamai import (
    Adapter,
    Context,
    ContextInvalidatedError,
    Event,
    Message,
    Plugin,
    Runtime,
    depends,
    message_handler,
    middleware,
)
from iamai.plugin import BoundHandler, HandlerSpec


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


class TracePlugin(Plugin):
    def __init__(
        self,
        runtime: Runtime,
        name: str,
        trace: list[str],
        *,
        failure: BaseException | None = None,
        shutdown_failure: BaseException | None = None,
        inspect_registry: bool = False,
    ) -> None:
        super().__init__(runtime)
        self.name = name
        self.trace = trace
        self.failure = failure
        self.shutdown_failure = shutdown_failure
        self.inspect_registry = inspect_registry
        self.active = False
        self.registry_at_start: tuple[str, ...] = ()
        self.adapter_registry_at_start: tuple[str, ...] = ()

    async def startup(self) -> None:
        self.trace.append(f"start:{self.plugin_name}")
        self.active = True
        if self.inspect_registry:
            self.registry_at_start = tuple(plugin.plugin_name for plugin in self.runtime.plugins)
            self.adapter_registry_at_start = tuple(
                adapter.name for adapter in self.runtime.adapters
            )
        if self.failure is not None:
            self.active = False
            raise self.failure

    async def shutdown(self) -> None:
        self.trace.append(f"stop:{self.plugin_name}")
        self.active = False
        if self.shutdown_failure is not None:
            raise self.shutdown_failure


class TraceAdapter(Adapter):
    name = "trace"

    def __init__(
        self,
        runtime: Runtime,
        trace: list[str],
        *,
        failure: BaseException | None = None,
        close_failure: BaseException | None = None,
    ) -> None:
        super().__init__(runtime)
        self.trace = trace
        self.failure = failure
        self.close_failure = close_failure
        self.release = asyncio.Event()
        self.closed = False
        self.sent: list[dict[str, Any]] = []
        self.api_calls: list[tuple[str, dict[str, Any]]] = []

    async def start(self) -> None:
        self.trace.append("start:adapter")
        if self.failure is not None:
            raise self.failure
        await self.release.wait()

    async def close(self) -> None:
        self.trace.append("close:adapter")
        self.closed = True
        self.release.set()
        if self.close_failure is not None:
            raise self.close_failure

    async def send_message(
        self,
        message: Message,
        *,
        event: Event | None = None,
        target: Any | None = None,
    ) -> Any:
        result = {"text": message.plain_text(), "event": event, "target": target}
        self.sent.append(result)
        return result

    async def call_api(self, action: str, **params: Any) -> Any:
        self.api_calls.append((action, params))
        return {"action": action, "params": params}


class ContextIdentityPlugin(Plugin):
    name = "context-identity"

    def __init__(self, runtime: Runtime) -> None:
        super().__init__(runtime)
        self.handler_contexts: list[Context] = []
        self.middleware_contexts: list[Context] = []

    @middleware(phase="around")
    async def observe_middleware(self, context: Context, call_next: Any) -> Any:
        self.middleware_contexts.append(context)
        return await call_next()

    @message_handler()
    async def first_handler(self, context: Context) -> None:
        self.handler_contexts.append(context)

    @message_handler()
    async def second_handler(self, context: Context) -> None:
        self.handler_contexts.append(context)


class DrainPlugin(Plugin):
    name = "drain"

    def __init__(
        self,
        runtime: Runtime,
        trace: list[str],
        started: asyncio.Event,
        release: asyncio.Event,
    ) -> None:
        super().__init__(runtime)
        self.trace = trace
        self.started = started
        self.release = release
        self.context: Context | None = None

    @middleware(phase="around")
    async def around(self, call_next: Any) -> Any:
        self.trace.append("around:before")
        result = await call_next()
        self.trace.append("around:after")
        return result

    @middleware(phase="after")
    async def after(self) -> None:
        self.trace.append("after")

    @message_handler()
    async def handle(self, context: Context) -> None:
        self.context = context
        self.trace.append("handler:before")
        self.started.set()
        await self.release.wait()
        self.trace.append("handler:after")


def _make_context(runtime: Runtime, plugin: Plugin, adapter: Adapter) -> Context:
    handler = BoundHandler(
        plugin=plugin,
        spec=HandlerSpec(func_name="handle", kind="message"),
        callback=lambda: None,
    )
    return Context(
        runtime=runtime,
        adapter=adapter,
        plugin=plugin,
        event=Event(
            id="evt-1",
            adapter=adapter.name,
            platform="test",
            type="message",
            channel_id="room",
            user_id="alice",
            message=Message("hello"),
        ),
        handler=handler,
        matches={"command": "demo", "args": "one two", "captured": "match"},
    )


def test_bootstrap_failure_rolls_back_started_plugins_and_preserves_error(
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        trace: list[str] = []
        failure = RuntimeError("startup failed")
        runtime = _make_runtime(tmp_path)
        first = TracePlugin(runtime, "first", trace)
        second = TracePlugin(runtime, "second", trace)
        failing = TracePlugin(runtime, "failing", trace, failure=failure)
        adapter = TraceAdapter(runtime, trace)
        runtime.load_plugins = lambda: runtime._set_plugins(  # type: ignore[method-assign]
            [first, second, failing], []
        )
        runtime.load_adapters = lambda: runtime._set_adapters(  # type: ignore[method-assign]
            [adapter], {adapter.name: adapter}, []
        )

        with pytest.raises(RuntimeError) as raised:
            await runtime.bootstrap()

        assert raised.value is failure
        assert trace == [
            "start:first",
            "start:second",
            "start:failing",
            "close:adapter",
            "stop:second",
            "stop:first",
        ]
        assert failing.active is False
        assert runtime._bootstrapped is False

    asyncio.run(scenario())


def test_shutdown_saves_and_stops_plugins_independently_in_reverse_order(
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        trace: list[str] = []
        runtime = _make_runtime(tmp_path)
        first = TracePlugin(runtime, "first", trace)
        second = TracePlugin(runtime, "second", trace)
        adapter = TraceAdapter(runtime, trace)
        runtime._set_plugins([first, second], [])
        runtime._set_adapters([adapter], {adapter.name: adapter}, [])

        def fail_save(plugin: Plugin) -> None:
            trace.append(f"save:{plugin.plugin_name}")
            raise RuntimeError("state backend unavailable")

        runtime._save_plugin_state = fail_save  # type: ignore[method-assign]

        await runtime.shutdown()
        await runtime.shutdown()

        assert trace == [
            "close:adapter",
            "save:second",
            "stop:second",
            "save:first",
            "stop:first",
        ]
        assert runtime._shutdown_complete is True

    asyncio.run(scenario())


def test_cleanup_cancellation_preserves_original_error_and_continues_rollback(
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        trace: list[str] = []
        failure = RuntimeError("startup failed")
        runtime = _make_runtime(tmp_path)
        first = TracePlugin(
            runtime,
            "first",
            trace,
            shutdown_failure=asyncio.CancelledError(),
        )
        second = TracePlugin(runtime, "second", trace)
        failing = TracePlugin(runtime, "failing", trace, failure=failure)
        adapter = TraceAdapter(
            runtime,
            trace,
            close_failure=asyncio.CancelledError(),
        )
        runtime.load_plugins = lambda: runtime._set_plugins(  # type: ignore[method-assign]
            [first, second, failing], []
        )
        runtime.load_adapters = lambda: runtime._set_adapters(  # type: ignore[method-assign]
            [adapter], {adapter.name: adapter}, []
        )

        with pytest.raises(RuntimeError) as raised:
            await runtime.bootstrap()

        assert raised.value is failure
        assert trace == [
            "start:first",
            "start:second",
            "start:failing",
            "close:adapter",
            "stop:second",
            "stop:first",
        ]
        assert first.active is False
        assert second.active is False

    asyncio.run(scenario())


def test_shutdown_cleanup_cancellation_is_best_effort_and_idempotent(tmp_path: Path) -> None:
    async def scenario() -> None:
        trace: list[str] = []
        runtime = _make_runtime(tmp_path)
        first = TracePlugin(runtime, "first", trace)
        second = TracePlugin(
            runtime,
            "second",
            trace,
            shutdown_failure=asyncio.CancelledError(),
        )
        adapter = TraceAdapter(
            runtime,
            trace,
            close_failure=asyncio.CancelledError(),
        )
        runtime._set_plugins([first, second], [])
        runtime._set_adapters([adapter], {adapter.name: adapter}, [])

        await runtime.shutdown()
        await runtime.shutdown()

        assert trace == ["close:adapter", "stop:second", "stop:first"]
        assert runtime._shutdown_complete is True

    asyncio.run(scenario())


def test_adapter_failure_preserves_error_and_triggers_full_cleanup(tmp_path: Path) -> None:
    async def scenario() -> None:
        trace: list[str] = []
        failure = RuntimeError("adapter disconnected")
        runtime = _make_runtime(tmp_path)
        plugin = TracePlugin(runtime, "plugin", trace)
        adapter = TraceAdapter(runtime, trace, failure=failure)
        runtime.load_plugins = lambda: runtime._set_plugins(  # type: ignore[method-assign]
            [plugin], []
        )
        runtime.load_adapters = lambda: runtime._set_adapters(  # type: ignore[method-assign]
            [adapter], {adapter.name: adapter}, []
        )

        with pytest.raises(RuntimeError) as raised:
            await runtime.serve()

        assert raised.value is failure
        assert trace == ["start:plugin", "start:adapter", "close:adapter", "stop:plugin"]
        assert adapter.closed is True
        assert plugin.active is False

    asyncio.run(scenario())


def test_plugin_reload_stages_new_registry_before_startup_and_commits_atomically(
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        trace: list[str] = []
        runtime = _make_runtime(tmp_path)
        old = TracePlugin(runtime, "old", trace)
        first = TracePlugin(runtime, "new-first", trace, inspect_registry=True)
        second = TracePlugin(runtime, "new-second", trace, inspect_registry=True)
        runtime._set_plugins([old], [])
        runtime._build_plugins = lambda **_: ([first, second], [])  # type: ignore[method-assign]

        await runtime.reload_plugins()

        assert runtime.plugins == [first, second]
        assert first.registry_at_start == ("new-first", "new-second")
        assert second.registry_at_start == ("new-first", "new-second")
        assert trace == ["start:new-first", "start:new-second", "stop:old"]

    asyncio.run(scenario())


def test_plugin_reload_failure_restores_old_registry_and_cleans_started_new_plugins(
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        trace: list[str] = []
        failure = RuntimeError("replacement failed")
        runtime = _make_runtime(tmp_path)
        old = TracePlugin(runtime, "old", trace)
        started = TracePlugin(runtime, "new-started", trace, inspect_registry=True)
        failing = TracePlugin(
            runtime,
            "new-failing",
            trace,
            failure=failure,
            inspect_registry=True,
        )
        runtime._set_plugins([old], [])
        runtime._build_plugins = lambda **_: ([started, failing], [])  # type: ignore[method-assign]

        with pytest.raises(RuntimeError) as raised:
            await runtime.reload_plugins()

        assert raised.value is failure
        assert runtime.plugins == [old]
        assert old.active is False
        assert started.active is False
        assert failing.active is False
        assert started.registry_at_start == ("new-started", "new-failing")
        assert trace == ["start:new-started", "start:new-failing", "stop:new-started"]
        assert runtime._accepting_handlers is True

    asyncio.run(scenario())


def test_config_reload_stages_both_registries_before_plugin_startup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def scenario() -> None:
        trace: list[str] = []
        runtime = _make_runtime(tmp_path)
        runtime.config["__meta__"]["config_path"] = str(tmp_path / "config.toml")
        old_plugin = TracePlugin(runtime, "old", trace)
        old_adapter = TraceAdapter(runtime, trace)
        new_plugin = TracePlugin(runtime, "new", trace, inspect_registry=True)
        new_adapter = TraceAdapter(runtime, trace)
        new_adapter.name = "new-adapter"
        runtime._set_plugins([old_plugin], [])
        runtime._set_adapters([old_adapter], {old_adapter.name: old_adapter}, [])
        runtime._build_plugins = lambda **_: ([new_plugin], [])  # type: ignore[method-assign]
        runtime._build_adapters = lambda: (  # type: ignore[method-assign]
            [new_adapter],
            {new_adapter.name: new_adapter},
            [],
        )
        new_config = _make_runtime(tmp_path).config
        new_config["__meta__"]["config_path"] = str(tmp_path / "config.toml")
        monkeypatch.setattr(runtime_module, "load_config", lambda _: new_config)

        await runtime.reload_config()

        assert runtime.plugins == [new_plugin]
        assert runtime.adapters == [new_adapter]
        assert new_plugin.registry_at_start == ("new",)
        assert new_plugin.adapter_registry_at_start == ("new-adapter",)
        assert old_adapter.closed is True
        assert new_adapter.closed is False
        assert trace == ["start:new", "close:adapter", "stop:old"]

    asyncio.run(scenario())


def test_config_reload_failure_restores_old_registries_and_closes_staged_adapters(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def scenario() -> None:
        trace: list[str] = []
        failure = RuntimeError("new config plugin failed")
        runtime = _make_runtime(tmp_path)
        runtime.config["__meta__"]["config_path"] = str(tmp_path / "config.toml")
        old_plugin = TracePlugin(runtime, "old", trace)
        old_adapter = TraceAdapter(runtime, trace)
        new_plugin = TracePlugin(
            runtime,
            "new",
            trace,
            failure=failure,
            inspect_registry=True,
        )
        new_adapter = TraceAdapter(runtime, trace)
        new_adapter.name = "new-adapter"
        runtime._set_plugins([old_plugin], [])
        runtime._set_adapters([old_adapter], {old_adapter.name: old_adapter}, [])
        runtime._build_plugins = lambda **_: ([new_plugin], [])  # type: ignore[method-assign]
        runtime._build_adapters = lambda: (  # type: ignore[method-assign]
            [new_adapter],
            {new_adapter.name: new_adapter},
            [],
        )
        new_config = _make_runtime(tmp_path).config
        new_config["__meta__"]["config_path"] = str(tmp_path / "config.toml")
        monkeypatch.setattr(runtime_module, "load_config", lambda _: new_config)

        with pytest.raises(RuntimeError) as raised:
            await runtime.reload_config()

        assert raised.value is failure
        assert runtime.plugins == [old_plugin]
        assert runtime.adapters == [old_adapter]
        assert new_plugin.registry_at_start == ("new",)
        assert new_plugin.adapter_registry_at_start == ("new-adapter",)
        assert old_adapter.closed is False
        assert new_adapter.closed is True
        assert trace == ["start:new", "close:adapter"]

    asyncio.run(scenario())


def test_config_reload_rolls_back_failures_before_extension_construction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def scenario() -> None:
        trace: list[str] = []
        runtime = _make_runtime(tmp_path)
        runtime.config["__meta__"]["config_path"] = str(tmp_path / "config.toml")
        old_config = runtime.config
        old_base_path = runtime.base_path
        old_state_store = runtime.state_store
        old_plugin = TracePlugin(runtime, "old", trace)
        old_adapter = TraceAdapter(runtime, trace)
        runtime._set_plugins([old_plugin], [])
        runtime._set_adapters([old_adapter], {old_adapter.name: old_adapter}, [])
        new_config = _make_runtime(tmp_path / "new-root").config
        new_config["__meta__"]["config_path"] = str(tmp_path / "config.toml")
        monkeypatch.setattr(runtime_module, "load_config", lambda _: new_config)

        failure = RuntimeError("state store construction failed")

        def fail_state_store(*_: Any, **__: Any) -> Any:
            raise failure

        monkeypatch.setattr(runtime_module, "create_state_store", fail_state_store)

        with pytest.raises(RuntimeError) as raised:
            await runtime.reload_config()

        assert raised.value is failure
        assert runtime.config is old_config
        assert runtime.base_path == old_base_path
        assert runtime.state_store is old_state_store
        assert runtime.plugins == [old_plugin]
        assert runtime.adapters == [old_adapter]
        assert old_adapter.closed is False

    asyncio.run(scenario())


def test_config_reload_rolls_back_post_startup_precommit_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def scenario() -> None:
        trace: list[str] = []
        runtime = _make_runtime(tmp_path)
        runtime.config["__meta__"]["config_path"] = str(tmp_path / "config.toml")
        old_config = runtime.config
        old_plugin = TracePlugin(runtime, "old", trace)
        old_adapter = TraceAdapter(runtime, trace)
        new_plugin = TracePlugin(runtime, "new", trace)
        new_adapter = TraceAdapter(runtime, trace)
        new_adapter.name = "new-adapter"
        runtime._set_plugins([old_plugin], [])
        runtime._set_adapters([old_adapter], {old_adapter.name: old_adapter}, [])
        runtime._build_plugins = lambda **_: ([new_plugin], [])  # type: ignore[method-assign]
        runtime._build_adapters = lambda: (  # type: ignore[method-assign]
            [new_adapter],
            {new_adapter.name: new_adapter},
            [],
        )
        new_config = _make_runtime(tmp_path).config
        new_config["__meta__"]["config_path"] = str(tmp_path / "config.toml")
        monkeypatch.setattr(runtime_module, "load_config", lambda _: new_config)
        failure = RuntimeError("runtime limits rejected")

        def fail_limits() -> None:
            raise failure

        runtime._configure_runtime_limits = fail_limits  # type: ignore[method-assign]

        with pytest.raises(RuntimeError) as raised:
            await runtime.reload_config()

        assert raised.value is failure
        assert runtime.config is old_config
        assert runtime.plugins == [old_plugin]
        assert runtime.adapters == [old_adapter]
        assert new_plugin.active is False
        assert new_adapter.closed is True
        assert old_adapter.closed is False
        assert trace == ["start:new", "close:adapter", "stop:new"]

    asyncio.run(scenario())


def test_staged_registry_does_not_hide_active_adapter_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def scenario() -> None:
        trace: list[str] = []
        runtime = _make_runtime(tmp_path)
        runtime.config["__meta__"]["config_path"] = str(tmp_path / "config.toml")
        old_plugin = TracePlugin(runtime, "old", trace)
        old_adapter = TraceAdapter(runtime, trace)
        new_adapter = TraceAdapter(runtime, trace)
        new_adapter.name = "new-adapter"
        old_failure = RuntimeError("old adapter failed during staging")
        reload_failure = RuntimeError("new plugin failed")
        release_old = asyncio.Event()

        async def run_old_adapter() -> None:
            await release_old.wait()
            raise old_failure

        async def fail_new_plugin_startup() -> None:
            trace.append("start:new")
            release_old.set()
            await asyncio.sleep(0)
            raise reload_failure

        old_adapter.start = run_old_adapter  # type: ignore[method-assign]
        new_plugin = TracePlugin(runtime, "new", trace)
        new_plugin.startup = fail_new_plugin_startup  # type: ignore[method-assign]
        runtime._set_plugins([old_plugin], [])
        runtime._set_adapters([old_adapter], {old_adapter.name: old_adapter}, [])
        runtime._start_adapters()
        runtime._build_plugins = lambda **_: ([new_plugin], [])  # type: ignore[method-assign]
        runtime._build_adapters = lambda: (  # type: ignore[method-assign]
            [new_adapter],
            {new_adapter.name: new_adapter},
            [],
        )
        new_config = _make_runtime(tmp_path).config
        new_config["__meta__"]["config_path"] = str(tmp_path / "config.toml")
        monkeypatch.setattr(runtime_module, "load_config", lambda _: new_config)

        with pytest.raises(RuntimeError) as raised:
            await runtime.reload_config()

        assert raised.value is reload_failure
        assert runtime.adapters == [old_adapter]
        assert runtime._adapter_failures.get_nowait() is old_failure
        await runtime.shutdown()

    asyncio.run(scenario())


def test_reload_drains_the_complete_active_handler_pipeline(tmp_path: Path) -> None:
    async def scenario() -> None:
        trace: list[str] = []
        started = asyncio.Event()
        release = asyncio.Event()
        runtime = _make_runtime(tmp_path)
        runtime._handler_shutdown_timeout_seconds = 1.0
        plugin = DrainPlugin(runtime, trace, started, release)
        replacement = TracePlugin(runtime, "replacement", trace)
        adapter = TraceAdapter(runtime, trace)
        runtime._set_plugins([plugin], [])
        runtime._build_plugins = lambda **_: ([replacement], [])  # type: ignore[method-assign]
        event = Event(
            id="evt-drain",
            adapter=adapter.name,
            platform="test",
            type="message",
            channel_id="room",
            user_id="alice",
            message=Message("hello"),
        )

        assert await runtime.dispatch(event, adapter) is True
        await started.wait()
        reload_task = asyncio.create_task(runtime.reload_plugins())
        await asyncio.sleep(0)
        assert reload_task.done() is False
        release.set()
        await reload_task

        assert trace == [
            "around:before",
            "handler:before",
            "handler:after",
            "around:after",
            "after",
            "start:replacement",
        ]

    asyncio.run(scenario())


def test_cancelled_reload_during_drain_restores_handler_admission(tmp_path: Path) -> None:
    async def scenario() -> None:
        trace: list[str] = []
        started = asyncio.Event()
        release = asyncio.Event()
        runtime = _make_runtime(tmp_path)
        runtime._handler_shutdown_timeout_seconds = 60.0
        plugin = DrainPlugin(runtime, trace, started, release)
        replacement = TracePlugin(runtime, "replacement", trace)
        adapter = TraceAdapter(runtime, trace)
        runtime._set_plugins([plugin], [])
        runtime._build_plugins = lambda **_: ([replacement], [])  # type: ignore[method-assign]
        event = Event(
            id="evt-cancel-reload",
            adapter=adapter.name,
            platform="test",
            type="message",
            channel_id="room",
            user_id="alice",
            message=Message("hello"),
        )

        assert await runtime.dispatch(event, adapter) is True
        await started.wait()
        reload_task = asyncio.create_task(runtime.reload_plugins())
        while runtime._accepting_handlers:
            await asyncio.sleep(0)
        reload_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await reload_task

        assert runtime._accepting_handlers is True
        assert runtime._handler_generation == 0
        assert plugin.context is not None
        assert plugin.context.is_valid is True
        assert runtime.plugins == [plugin]

        release.set()
        await asyncio.gather(*list(runtime._handler_tasks))
        assert trace == [
            "around:before",
            "handler:before",
            "handler:after",
            "around:after",
            "after",
        ]

    asyncio.run(scenario())


def test_context_routes_operations_and_di_with_documented_precedence(tmp_path: Path) -> None:
    async def scenario() -> None:
        trace: list[str] = []
        runtime = _make_runtime(tmp_path)
        plugin = TracePlugin(runtime, "plugin", trace)
        adapter = TraceAdapter(runtime, trace)
        ctx = _make_context(runtime, plugin, adapter)

        assert (await ctx.reply("reply"))["event"] is ctx.event
        assert (await ctx.reply("reply"))["target"] is None
        assert (await ctx.send("send", target="elsewhere"))["event"] is None
        assert (await ctx.send("send", target="elsewhere"))["target"] == "elsewhere"
        assert await ctx.call_api("ping", value=1) == {
            "action": "ping",
            "params": {"value": 1},
        }

        runtime.register_dependency("captured", "registered")
        runtime.register_dependency("service", "named-service")
        provider_calls = 0

        async def provider(context: Context) -> str:
            nonlocal provider_calls
            provider_calls += 1
            assert context is ctx
            return "provided"

        shared_dependency = depends(provider)

        async def callback(
            context: Context,
            event: Event,
            captured: str,
            service: str,
            first: str = shared_dependency,
            second: str = shared_dependency,
            fallback: str = "default",
        ) -> tuple[Any, ...]:
            return context, event, captured, service, first, second, fallback

        result = await runtime._invoke_callable(callback, ctx, cache={})
        assert result == (
            ctx,
            ctx.event,
            "match",
            "named-service",
            "provided",
            "provided",
            "default",
        )
        assert provider_calls == 1

        result = await runtime._invoke_callable(
            callback,
            ctx,
            extra={"service": "phase-extra"},
            cache={},
        )
        assert result[3] == "phase-extra"
        assert provider_calls == 2

    asyncio.run(scenario())


def test_context_scope_is_distinct_per_handler_and_shared_with_middleware(
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        trace: list[str] = []
        runtime = _make_runtime(tmp_path)
        runtime._max_concurrent_handlers = 2
        runtime._max_pending_handlers = 0
        plugin = ContextIdentityPlugin(runtime)
        adapter = TraceAdapter(runtime, trace)
        runtime._set_plugins([plugin], [])
        event = Event(
            id="evt-scope",
            adapter=adapter.name,
            platform="test",
            type="message",
            channel_id="room",
            user_id="alice",
            message=Message("hello"),
        )

        assert await runtime.dispatch(event, adapter) is True
        await asyncio.gather(*list(runtime._handler_tasks))

        assert len(plugin.handler_contexts) == 2
        assert len({id(context) for context in plugin.handler_contexts}) == 2
        assert len(plugin.middleware_contexts) == 2
        assert {id(context) for context in plugin.middleware_contexts} == {
            id(context) for context in plugin.handler_contexts
        }

    asyncio.run(scenario())


def test_wait_for_message_returns_the_new_event_context(tmp_path: Path) -> None:
    async def scenario() -> None:
        trace: list[str] = []
        runtime = _make_runtime(tmp_path)
        plugin = TracePlugin(runtime, "plugin", trace)
        adapter = TraceAdapter(runtime, trace)
        waiting_ctx = _make_context(runtime, plugin, adapter)
        incoming_ctx = _make_context(runtime, plugin, adapter)
        incoming_ctx.event.id = "evt-2"

        waiter = asyncio.create_task(
            waiting_ctx.wait_for_message(timeout=1.0, rule=lambda _: True)
        )
        await asyncio.sleep(0)
        assert await runtime.sessions.consume(incoming_ctx) is True

        delivered = await waiter
        assert delivered is incoming_ctx
        assert delivered is not waiting_ctx
        assert waiting_ctx.event.id == "evt-1"

    asyncio.run(scenario())


def test_di_cache_is_shared_across_runtime_callback_boundaries(tmp_path: Path) -> None:
    async def scenario() -> None:
        trace: list[str] = []
        runtime = _make_runtime(tmp_path)
        plugin = TracePlugin(runtime, "plugin", trace)
        adapter = TraceAdapter(runtime, trace)
        ctx = _make_context(runtime, plugin, adapter)
        provider_calls = 0

        async def provider() -> str:
            nonlocal provider_calls
            provider_calls += 1
            return "shared"

        shared_dependency = depends(provider)

        async def first(value: str = shared_dependency) -> str:
            return value

        async def second(value: str = shared_dependency) -> str:
            return value

        cache: dict[Any, Any] = {}
        assert await runtime._invoke_callable(first, ctx, cache=cache) == "shared"
        assert await runtime._invoke_callable(second, ctx, cache=cache) == "shared"
        assert provider_calls == 1

    asyncio.run(scenario())


def test_depends_use_cache_false_reexecutes_for_every_parameter(tmp_path: Path) -> None:
    async def scenario() -> None:
        trace: list[str] = []
        runtime = _make_runtime(tmp_path)
        plugin = TracePlugin(runtime, "plugin", trace)
        adapter = TraceAdapter(runtime, trace)
        ctx = _make_context(runtime, plugin, adapter)
        provider_calls = 0

        async def provider() -> int:
            nonlocal provider_calls
            provider_calls += 1
            return provider_calls

        uncached = depends(provider, use_cache=False)

        async def callback(first: int = uncached, second: int = uncached) -> tuple[int, int]:
            return first, second

        assert await runtime._invoke_callable(callback, ctx, cache={}) == (1, 2)
        assert provider_calls == 2

    asyncio.run(scenario())


def test_async_depends_cannot_cross_generation_or_populate_cache(tmp_path: Path) -> None:
    async def scenario() -> None:
        trace: list[str] = []
        runtime = _make_runtime(tmp_path)
        plugin = TracePlugin(runtime, "plugin", trace)
        adapter = TraceAdapter(runtime, trace)
        ctx = _make_context(runtime, plugin, adapter)
        provider_started = asyncio.Event()
        release_provider = asyncio.Event()
        callback_ran = False

        async def provider() -> str:
            provider_started.set()
            await release_provider.wait()
            return "stale"

        dependency = depends(provider)

        async def callback(value: str = dependency) -> str:
            nonlocal callback_ran
            callback_ran = True
            return value

        cache: dict[Any, Any] = {}
        invocation = asyncio.create_task(runtime._invoke_callable(callback, ctx, cache=cache))
        await provider_started.wait()
        runtime._handler_generation += 1
        release_provider.set()

        with pytest.raises(ContextInvalidatedError):
            await invocation
        assert callback_ran is False
        assert cache == {}

    asyncio.run(scenario())


def test_async_session_rules_cannot_deliver_contexts_across_generations(
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        trace: list[str] = []
        runtime = _make_runtime(tmp_path)
        plugin = TracePlugin(runtime, "plugin", trace)
        adapter = TraceAdapter(runtime, trace)
        waiting_ctx = _make_context(runtime, plugin, adapter)
        incoming_ctx = _make_context(runtime, plugin, adapter)
        rule_started = asyncio.Event()
        release_rule = asyncio.Event()

        async def delayed_rule(_: Context) -> bool:
            rule_started.set()
            await release_rule.wait()
            return True

        waiter = asyncio.create_task(
            runtime.sessions.wait_for(waiting_ctx, timeout=1.0, rule=delayed_rule)
        )
        await asyncio.sleep(0)
        delivery = asyncio.create_task(runtime.sessions.consume(incoming_ctx))
        await rule_started.wait()
        runtime._handler_generation += 1
        release_rule.set()

        assert await delivery is False
        assert waiter.done() is False
        waiter.cancel()
        with pytest.raises(asyncio.CancelledError):
            await waiter

    asyncio.run(scenario())


def test_session_waiter_revalidates_context_before_returning(tmp_path: Path) -> None:
    async def scenario() -> None:
        trace: list[str] = []
        runtime = _make_runtime(tmp_path)
        plugin = TracePlugin(runtime, "plugin", trace)
        adapter = TraceAdapter(runtime, trace)
        waiting_ctx = _make_context(runtime, plugin, adapter)
        incoming_ctx = _make_context(runtime, plugin, adapter)
        waiter = asyncio.create_task(runtime.sessions.wait_for(waiting_ctx, timeout=1.0))
        await asyncio.sleep(0)

        assert await runtime.sessions.consume(incoming_ctx) is True
        runtime._handler_generation += 1

        with pytest.raises(ContextInvalidatedError):
            await waiter

    asyncio.run(scenario())


def test_lifecycle_cancellation_records_dropped_work(tmp_path: Path) -> None:
    async def scenario() -> None:
        runtime = _make_runtime(tmp_path)
        dispatch_task = asyncio.create_task(asyncio.sleep(60, result=[]))
        handler_task = asyncio.create_task(asyncio.sleep(60))
        runtime._dispatch_tasks.add(dispatch_task)
        runtime._handler_tasks.add(handler_task)

        await runtime._pause_handler_dispatch(cancel_active=True)

        assert dispatch_task.cancelled()
        assert handler_task.cancelled()
        assert runtime.metrics.snapshot()[
            "runtime_handler_dropped_total{reason=lifecycle}"
        ] == 2

    asyncio.run(scenario())


def test_reload_invalidates_context_runtime_surfaces_and_discards_session_backlog(
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        trace: list[str] = []
        runtime = _make_runtime(tmp_path)
        old = TracePlugin(runtime, "old", trace)
        replacement = TracePlugin(runtime, "replacement", trace)
        adapter = TraceAdapter(runtime, trace)
        runtime._set_plugins([old], [])
        runtime._set_adapters([adapter], {adapter.name: adapter}, [])
        runtime._build_plugins = lambda **_: ([replacement], [])  # type: ignore[method-assign]
        ctx = _make_context(runtime, old, adapter)

        assert await runtime.sessions.consume(ctx) is False
        assert sum(len(items) for items in runtime.sessions._backlog.values()) == 1

        await runtime.reload_plugins()

        assert ctx.is_valid is False
        assert ctx.event.id == "evt-1"
        assert ctx.text == "hello"
        assert ctx.matches["captured"] == "match"
        assert runtime.sessions._backlog == {}
        assert await runtime.sessions.consume(ctx) is False
        assert runtime.sessions._backlog == {}

        for accessor in (
            lambda: ctx.config,
            lambda: ctx.state,
            lambda: ctx.shared_state,
        ):
            with pytest.raises(ContextInvalidatedError):
                accessor()

        async def injected(context: Context) -> None:
            return None

        with pytest.raises(ContextInvalidatedError):
            await runtime._invoke_callable(injected, ctx, cache={})
        with pytest.raises(ContextInvalidatedError):
            await ctx.reply("late")
        with pytest.raises(ContextInvalidatedError):
            await ctx.send("late")
        with pytest.raises(ContextInvalidatedError):
            await ctx.call_api("late")
        with pytest.raises(ContextInvalidatedError):
            await ctx.reload_plugins()
        with pytest.raises(ContextInvalidatedError):
            await ctx.wait_for_message(timeout=0.01)

    asyncio.run(scenario())


def test_shutdown_invalidates_context_runtime_surfaces(tmp_path: Path) -> None:
    async def scenario() -> None:
        trace: list[str] = []
        runtime = _make_runtime(tmp_path)
        plugin = TracePlugin(runtime, "plugin", trace)
        adapter = TraceAdapter(runtime, trace)
        runtime._set_plugins([plugin], [])
        runtime._set_adapters([adapter], {adapter.name: adapter}, [])
        ctx = _make_context(runtime, plugin, adapter)

        await runtime.shutdown()

        assert ctx.is_valid is False
        assert ctx.event.id == "evt-1"
        assert ctx.matches["captured"] == "match"
        with pytest.raises(ContextInvalidatedError):
            await ctx.reply("late")

    asyncio.run(scenario())
