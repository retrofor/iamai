from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
from pathlib import Path
from textwrap import dedent
from types import SimpleNamespace

import pytest
from iamai import Event, Message, Plugin, Runtime, message_handler
from iamai.adapters.onebot11 import OneBot11Adapter
from iamai.adapters.webhook import WebhookAdapter
from iamai.config import ConfigValidationError, load_config
from iamai.httpio import HttpRequest
from iamai.runtime import check_config
from iamai.session import SessionManager


def _make_runtime(tmp_path: Path) -> Runtime:
    return Runtime(
        {
            "runtime": {"adapters": []},
            "adapter": {},
            "plugin": {},
            "state": {},
            "__meta__": {"root_dir": str(tmp_path)},
        },
        base_path=tmp_path,
    )


def _make_webhook_request(
    body: bytes,
    *,
    headers: dict[str, str] | None = None,
    query_string: str = "",
) -> HttpRequest:
    return HttpRequest(
        method="POST",
        path="/events",
        query_string=query_string,
        headers=headers or {},
        body=body,
        client=("127.0.0.1", 12345),
    )


def _sign_webhook(secret: str, body: bytes, *, timestamp: str | None = None) -> str:
    payload = body if timestamp is None else f"{timestamp}.".encode("utf-8") + body
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def _response_json(payload: bytes) -> dict[str, object]:
    return json.loads(payload.decode("utf-8"))


def test_load_config_rejects_exposed_onebot_without_token(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        dedent("""
            [runtime]
            adapters = ["onebot11"]

            [adapter.onebot11]
            mode = "ws-reverse"
            host = "0.0.0.0"
            access_token = ""
            """).strip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigValidationError, match="access_token is required"):
        load_config(config_path)


def test_load_config_rejects_unknown_webhook_signature_provider(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        dedent("""
            [runtime]
            adapters = ["webhook"]

            [adapter.webhook]
            signature_provider = "unknown"
            """).strip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigValidationError, match="signature_provider must be one of"):
        load_config(config_path)


def test_check_config_supports_python_paths(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    plugin_dir = app_dir / "plugins"
    shared_dir = tmp_path / "_shared" / "src" / "demo_utils"
    plugin_dir.mkdir(parents=True)
    shared_dir.mkdir(parents=True)

    (shared_dir / "__init__.py").write_text('VALUE = "shared-helper"\n', encoding="utf-8")
    (plugin_dir / "helper.py").write_text(
        dedent("""
            from iamai import Plugin
            from demo_utils import VALUE


            class HelperPlugin(Plugin):
                name = "helper"
                description = VALUE
            """).strip()
        + "\n",
        encoding="utf-8",
    )
    config_path = app_dir / "config.toml"
    config_path.write_text(
        dedent("""
            [runtime]
            adapters = []
            plugin_dirs = ["plugins"]
            python_paths = ["../_shared/src"]
            allow_external_paths = true
            """).strip(),
        encoding="utf-8",
    )

    result = check_config(config_path)

    assert "runtime.allow_external_paths is enabled" in result["warnings"]
    helper = next(item for item in result["plugins"] if item["name"] == "helper")
    assert helper["description"] == "shared-helper"


def test_session_key_is_scoped_by_adapter_channel_and_user() -> None:
    manager = SessionManager()
    base_event = Event(
        id="evt-1",
        adapter="onebot11",
        platform="qq",
        type="message",
        channel_id="room-1",
        user_id="alice",
        message=Message("hello"),
    )
    same_channel_other_user = Event(
        id="evt-2",
        adapter="onebot11",
        platform="qq",
        type="message",
        channel_id="room-1",
        user_id="bob",
        message=Message("hello"),
    )

    first_key = manager.session_key(SimpleNamespace(event=base_event))
    second_key = manager.session_key(SimpleNamespace(event=same_channel_other_user))

    assert first_key == "onebot11:room-1:alice"
    assert second_key == "onebot11:room-1:bob"
    assert first_key != second_key


def test_session_backlog_evicts_oldest_keys_and_limits_each_key() -> None:
    async def run() -> None:
        manager = SessionManager(max_backlog_keys=2, max_backlog_per_key=1)

        def context(user: str, event_id: str) -> SimpleNamespace:
            return SimpleNamespace(
                event=Event(
                    id=event_id,
                    adapter="onebot11",
                    platform="qq",
                    type="message",
                    channel_id="room-1",
                    user_id=user,
                    message=Message(event_id),
                )
            )

        alice = context("alice", "alice-old")
        bob_old = context("bob", "bob-old")
        bob_new = context("bob", "bob-new")
        carol = context("carol", "carol")
        await manager.consume(alice)  # type: ignore[arg-type]
        await manager.consume(bob_old)  # type: ignore[arg-type]
        await manager.consume(bob_new)  # type: ignore[arg-type]
        await manager.consume(carol)  # type: ignore[arg-type]

        with pytest.raises(TimeoutError):
            await manager.wait_for(alice, timeout=0.001)  # type: ignore[arg-type]
        bob = await manager.wait_for(bob_new, timeout=0.001)  # type: ignore[arg-type]
        assert bob.event.id == "bob-new"

    asyncio.run(run())


def test_session_backlog_discards_expired_contexts() -> None:
    async def run() -> None:
        now = 100.0
        manager = SessionManager(backlog_ttl_seconds=10.0)
        manager._clock = lambda: now
        ctx = SimpleNamespace(
            event=Event(
                id="expired",
                adapter="onebot11",
                platform="qq",
                type="message",
                channel_id="room-1",
                user_id="alice",
                message=Message("expired"),
            )
        )
        await manager.consume(ctx)  # type: ignore[arg-type]

        now = 111.0
        with pytest.raises(TimeoutError):
            await manager.wait_for(ctx, timeout=0.001)  # type: ignore[arg-type]

    asyncio.run(run())


def test_runtime_applies_handler_concurrency_backpressure(tmp_path: Path) -> None:
    class BlockingPlugin(Plugin):
        name = "blocking"

        def __init__(self, runtime: Runtime) -> None:
            super().__init__(runtime)
            self.release = asyncio.Event()
            self.started = asyncio.Event()
            self.finished = asyncio.Event()
            self.running = 0
            self.max_running = 0
            self.handled = 0

        @message_handler()
        async def handle(self) -> None:
            self.running += 1
            self.max_running = max(self.max_running, self.running)
            self.started.set()
            await self.release.wait()
            self.running -= 1
            self.handled += 1
            if self.handled == 2:
                self.finished.set()

    async def run() -> None:
        runtime = _make_runtime(tmp_path)
        runtime.config["runtime"]["max_concurrent_handlers"] = 1
        runtime = Runtime(runtime.config, base_path=tmp_path)
        plugin = BlockingPlugin(runtime)
        runtime._set_plugins([plugin], [])
        adapter = SimpleNamespace(name="test")

        def event(event_id: str) -> Event:
            return Event(
                id=event_id,
                adapter="test",
                platform="test",
                type="message",
                channel_id="room-1",
                user_id=event_id,
                message=Message(event_id),
            )

        await runtime.dispatch(event("first"), adapter)  # type: ignore[arg-type]
        await plugin.started.wait()
        second_dispatch = asyncio.create_task(
            runtime.dispatch(event("second"), adapter)  # type: ignore[arg-type]
        )
        await asyncio.sleep(0)
        assert not second_dispatch.done()

        plugin.release.set()
        await second_dispatch
        await asyncio.wait_for(plugin.finished.wait(), timeout=1.0)
        await runtime.shutdown()
        assert plugin.max_running == 1

    asyncio.run(run())


@pytest.mark.parametrize(
    "field,value",
    [
        ("max_concurrent_handlers", "0"),
        ("session_backlog_max_keys", "0"),
        ("session_backlog_per_key", "0"),
        ("session_backlog_ttl_seconds", "0.0"),
    ],
)
def test_load_config_rejects_non_positive_runtime_limits(
    tmp_path: Path,
    field: str,
    value: str,
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(f"[runtime]\n{field} = {value}\n", encoding="utf-8")

    with pytest.raises(ConfigValidationError, match="greater than 0"):
        load_config(config_path)


def test_runtime_list_adapters_redacts_sensitive_values(tmp_path: Path) -> None:
    config = {
        "runtime": {"adapters": ["onebot11"]},
        "adapter": {"onebot11": {"mode": "ws", "access_token": "super-secret"}},
        "plugin": {},
        "state": {},
        "__meta__": {"root_dir": str(tmp_path)},
    }

    runtime = Runtime(config, base_path=tmp_path)
    runtime.load_adapters()

    adapter_config = runtime.list_adapters()[0]["config"]
    assert adapter_config["access_token"] == "***"


def test_onebot_query_token_is_disabled_by_default(tmp_path: Path) -> None:
    runtime = _make_runtime(tmp_path)
    adapter = OneBot11Adapter(
        runtime,
        {
            "mode": "ws",
            "url": "ws://127.0.0.1:6700",
            "access_token": "secret",
        },
    )

    assert adapter._authorize_headers({}, "?access_token=secret") is False

    permissive = OneBot11Adapter(
        runtime,
        {
            "mode": "ws",
            "url": "ws://127.0.0.1:6700",
            "access_token": "secret",
            "allow_query_token": True,
        },
    )
    assert permissive._authorize_headers({}, "?access_token=secret") is True


def test_webhook_reply_url_policy_blocks_private_hosts(tmp_path: Path) -> None:
    runtime = _make_runtime(tmp_path)
    adapter = WebhookAdapter(
        runtime,
        {
            "host": "127.0.0.1",
            "port": 8090,
            "path": "/events",
            "allow_event_reply_url": True,
        },
    )
    event = Event(
        id="evt-1",
        adapter="webhook",
        platform="webhook",
        type="message",
        user_id="webhook-user",
        message=Message("hello"),
        raw={"reply_url": "https://127.0.0.1:8080/reply"},
    )

    with pytest.raises(ValueError, match="non-public"):
        asyncio.run(adapter.send_message("pong", event=event))


def test_check_config_reports_risky_runtime_warnings(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        dedent("""
            [runtime]
            adapters = ["webhook"]
            allow_external_paths = true

            [adapter.webhook]
            host = "0.0.0.0"
            access_token = "dev-token"

            [plugin.management]
            allow_reload = true
            allow_introspection = true
            reload_requires_superuser = false
            introspection_requires_superuser = false
            """).strip(),
        encoding="utf-8",
    )

    result = check_config(config_path)

    assert "runtime.allow_external_paths is enabled" in result["warnings"]
    assert (
        "webhook is exposed on a non-loopback host without signature_secret" in result["warnings"]
    )
    assert "management reload is enabled but runtime.superusers is empty" in result["warnings"]
    assert "management reload is enabled without requiring a superuser" in result["warnings"]
    assert (
        "management introspection is enabled but runtime.superusers is empty" in result["warnings"]
    )
    assert "management introspection is enabled without requiring a superuser" in result["warnings"]


def test_check_config_reports_management_api_exposure(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        dedent("""
            [runtime]
            adapters = []
            builtin_plugins = ["management_api"]

            [plugin.management_api]
            host = "0.0.0.0"
            port = 8765
            token = "secret"
            """).strip(),
        encoding="utf-8",
    )

    result = check_config(config_path)

    assert "management_api is exposed on a non-loopback host" in result["warnings"]


def test_webhook_accepts_valid_signature_and_token(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = 1_700_000_000
    monkeypatch.setattr("iamai.webhook_security.time.time", lambda: now)
    runtime = _make_runtime(tmp_path)
    adapter = WebhookAdapter(
        runtime,
        {
            "host": "127.0.0.1",
            "port": 8090,
            "path": "/events",
            "access_token": "secret-token",
            "signature_secret": "signing-secret",
            "timestamp_tolerance_seconds": 300,
        },
    )
    body = b'{"message":"hello","user_id":"alice"}'
    timestamp = str(now)
    signature = _sign_webhook("signing-secret", body, timestamp=timestamp)
    request = _make_webhook_request(
        body,
        headers={
            "authorization": "Bearer secret-token",
            "content-type": "application/json",
            "x-iamai-signature": f"sha256={signature}",
            "x-iamai-timestamp": timestamp,
        },
    )

    response = asyncio.run(adapter._handle_request(request))

    assert response.status == 200
    assert _response_json(response.body)["ok"] is True


def test_webhook_rejects_invalid_signature(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    now = 1_700_000_000
    monkeypatch.setattr("iamai.webhook_security.time.time", lambda: now)
    adapter = WebhookAdapter(
        _make_runtime(tmp_path),
        {
            "host": "127.0.0.1",
            "port": 8090,
            "path": "/events",
            "signature_secret": "signing-secret",
        },
    )
    request = _make_webhook_request(
        b'{"message":"hello"}',
        headers={
            "content-type": "application/json",
            "x-iamai-signature": "sha256=deadbeef",
            "x-iamai-timestamp": str(now),
        },
    )

    response = asyncio.run(adapter._handle_request(request))

    assert response.status == 401


def test_webhook_rejects_expired_timestamp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    now = 1_700_000_000
    monkeypatch.setattr("iamai.webhook_security.time.time", lambda: now)
    adapter = WebhookAdapter(
        _make_runtime(tmp_path),
        {
            "host": "127.0.0.1",
            "port": 8090,
            "path": "/events",
            "signature_secret": "signing-secret",
            "timestamp_tolerance_seconds": 60,
        },
    )
    body = b'{"message":"hello"}'
    timestamp = str(now - 120)
    signature = _sign_webhook("signing-secret", body, timestamp=timestamp)
    request = _make_webhook_request(
        body,
        headers={
            "content-type": "application/json",
            "x-iamai-signature": f"sha256={signature}",
            "x-iamai-timestamp": timestamp,
        },
    )

    response = asyncio.run(adapter._handle_request(request))

    assert response.status == 401


def test_webhook_rejects_replayed_signature(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = 1_700_000_000
    monkeypatch.setattr("iamai.webhook_security.time.time", lambda: now)
    adapter = WebhookAdapter(
        _make_runtime(tmp_path),
        {
            "host": "127.0.0.1",
            "port": 8090,
            "path": "/events",
            "signature_secret": "signing-secret",
            "timestamp_tolerance_seconds": 300,
        },
    )
    body = b'{"message":"hello"}'
    timestamp = str(now)
    signature = _sign_webhook("signing-secret", body, timestamp=timestamp)
    request = _make_webhook_request(
        body,
        headers={
            "content-type": "application/json",
            "x-iamai-signature": f"sha256={signature}",
            "x-iamai-timestamp": timestamp,
        },
    )

    first = asyncio.run(adapter._handle_request(request))
    second = asyncio.run(adapter._handle_request(request))

    assert first.status == 200
    assert second.status == 401


def test_webhook_github_signature_provider_accepts_valid_signature(
    tmp_path: Path,
) -> None:
    adapter = WebhookAdapter(
        _make_runtime(tmp_path),
        {
            "host": "127.0.0.1",
            "port": 8090,
            "path": "/events",
            "signature_provider": "github",
            "signature_secret": "signing-secret",
        },
    )
    body = b'{"message":"hello"}'
    signature = _sign_webhook("signing-secret", body)
    request = _make_webhook_request(
        body,
        headers={
            "content-type": "application/json",
            "x-hub-signature-256": f"sha256={signature}",
        },
    )

    response = asyncio.run(adapter._handle_request(request))

    assert response.status == 200


def test_webhook_stripe_signature_provider_accepts_valid_signature(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = 1_700_000_000
    monkeypatch.setattr("iamai.webhook_security.time.time", lambda: now)
    adapter = WebhookAdapter(
        _make_runtime(tmp_path),
        {
            "host": "127.0.0.1",
            "port": 8090,
            "path": "/events",
            "signature_provider": "stripe",
            "signature_secret": "whsec_test",
            "timestamp_tolerance_seconds": 300,
        },
    )
    body = b'{"message":"hello"}'
    timestamp = str(now)
    signature = _sign_webhook("whsec_test", body, timestamp=timestamp)
    request = _make_webhook_request(
        body,
        headers={
            "content-type": "application/json",
            "stripe-signature": f"t={timestamp},v1={signature}",
        },
    )

    response = asyncio.run(adapter._handle_request(request))

    assert response.status == 200


def test_webhook_records_metrics_for_authorization_failures(tmp_path: Path) -> None:
    runtime = _make_runtime(tmp_path)
    adapter = WebhookAdapter(
        runtime,
        {
            "host": "127.0.0.1",
            "port": 8090,
            "path": "/events",
            "access_token": "secret-token",
        },
    )
    request = _make_webhook_request(
        b'{"message":"hello"}',
        headers={"content-type": "application/json"},
    )

    response = asyncio.run(adapter._handle_request(request))

    assert response.status == 401
    metrics = runtime.metrics.snapshot()
    assert (
        metrics[
            "webhook_requests_total{adapter=webhook,outcome=unauthorized,provider=generic,status=401}"
        ]
        == 1
    )


def test_webhook_rejects_explicit_non_json_content_type(tmp_path: Path) -> None:
    adapter = WebhookAdapter(
        _make_runtime(tmp_path),
        {
            "host": "127.0.0.1",
            "port": 8090,
            "path": "/events",
        },
    )
    request = _make_webhook_request(
        b'{"message":"hello"}',
        headers={"content-type": "text/plain"},
    )

    response = asyncio.run(adapter._handle_request(request))

    assert response.status == 415


def test_onebot_http_rejects_explicit_non_json_content_type(tmp_path: Path) -> None:
    runtime = _make_runtime(tmp_path)
    adapter = OneBot11Adapter(
        runtime,
        {
            "mode": "http",
            "host": "127.0.0.1",
            "port": 8080,
            "path": "/onebot/v11/http",
            "access_token": "secret-token",
        },
    )
    request = HttpRequest(
        method="POST",
        path="/onebot/v11/http",
        query_string="",
        headers={
            "authorization": "Bearer secret-token",
            "content-type": "text/plain",
        },
        body=b"{}",
        client=("127.0.0.1", 23456),
    )

    response = asyncio.run(adapter._handle_http_request(request))

    assert response.status == 415
    metrics = runtime.metrics.snapshot()
    assert (
        metrics[
            "onebot_http_requests_total{adapter=onebot11,outcome=unsupported_media_type,status=415}"
        ]
        == 1
    )
