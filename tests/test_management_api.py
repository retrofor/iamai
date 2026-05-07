from __future__ import annotations

import json
from pathlib import Path

from iamai import Plugin, Runtime, command
from iamai.httpio import HttpRequest
from iamai.plugins.management_api import ManagementApiPlugin


class DemoPlugin(Plugin):
    name = "demo"

    @command("demo")
    async def demo_command(self) -> None:
        return None


def _make_runtime(tmp_path: Path) -> Runtime:
    return Runtime(
        {
            "runtime": {"adapters": [], "plugins": [], "builtin_plugins": False},
            "adapter": {},
            "plugin": {"management_api": {"host": "127.0.0.1", "port": 8765, "token": "secret"}},
            "state": {},
            "__meta__": {"root_dir": str(tmp_path)},
        },
        base_path=tmp_path,
    )


def _request(path: str, *, token: str | None = "secret") -> HttpRequest:
    headers = {"authorization": f"Bearer {token}"} if token is not None else {}
    return HttpRequest(method="GET", path=path, query_string="", headers=headers, body=b"")


def _json_response(body: bytes) -> object:
    return json.loads(body.decode("utf-8"))


def test_management_api_rejects_missing_token(tmp_path: Path) -> None:
    plugin = ManagementApiPlugin(_make_runtime(tmp_path))
    plugin._config_data = {"host": "127.0.0.1", "port": 8765, "token": "secret"}

    response = plugin._health(_request("/health", token=None))

    assert response.status == 401
    assert _json_response(response.body) == {"error": "unauthorized"}


def test_management_api_exposes_read_only_runtime_payloads(tmp_path: Path) -> None:
    runtime = _make_runtime(tmp_path)
    plugin = ManagementApiPlugin(runtime)
    plugin._config_data = {"host": "127.0.0.1", "port": 8765, "token": "secret"}
    runtime.plugins = [DemoPlugin(runtime)]
    runtime._plugin_map = {"demo": runtime.plugins[0]}
    runtime._plugin_descriptor_map = {}
    runtime.count_metric("demo_total", adapter="test")
    runtime.state["private"] = {"value": 1}

    assert _json_response(plugin._health(_request("/health")).body)["plugins"] == 1
    assert _json_response(plugin._metrics(_request("/metrics")).body)[0]["name"] == "demo_total"
    assert _json_response(plugin._plugins(_request("/plugins")).body)[0]["name"] == "demo"
    assert _json_response(plugin._handlers(_request("/handlers")).body)[0]["name"] == "demo_command"
    assert _json_response(plugin._sessions(_request("/sessions")).body) == []
    assert _json_response(plugin._schema(_request("/schema")).body) == {}
    assert _json_response(plugin._state(_request("/state")).body) == {"backend": "NullStateStore"}
