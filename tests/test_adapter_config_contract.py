from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest
from iamai import Runtime
from iamai.adapters.onebot11 import OneBot11Adapter
from iamai.adapters.telegram import TelegramAdapter
from iamai.adapters.terminal import TerminalAdapter
from iamai.adapters.webhook import WebhookAdapter
from iamai.config import (
    OneBot11ConfigModel,
    TelegramConfigModel,
    TerminalConfigModel,
    WebhookConfigModel,
    load_config,
)
from iamai.validation import AdapterConfigValidationError
from pydantic import BaseModel


def _make_runtime(tmp_path: Path, *, adapters: list[str] | None = None) -> Runtime:
    return Runtime(
        {
            "runtime": {"adapters": adapters or []},
            "adapter": {},
            "plugin": {},
            "state": {},
            "__meta__": {"root_dir": str(tmp_path)},
        },
        base_path=tmp_path,
    )


def test_builtin_adapters_publish_config_models_and_normalized_objects(tmp_path: Path) -> None:
    runtime = _make_runtime(tmp_path)

    terminal = TerminalAdapter(runtime, {"exit_commands": ["done"]})
    onebot = OneBot11Adapter(runtime, {"mode": "reverse-ws"})
    webhook = WebhookAdapter(runtime)
    telegram = TelegramAdapter(runtime, {"token": "123:secret"})

    assert isinstance(terminal.config_obj, TerminalConfigModel)
    assert isinstance(onebot.config_obj, OneBot11ConfigModel)
    assert isinstance(webhook.config_obj, WebhookConfigModel)
    assert isinstance(telegram.config_obj, TelegramConfigModel)
    assert terminal.config["exit_commands"] == ["done"]
    assert onebot.config["mode"] == "ws-reverse"
    assert webhook.config["allowed_reply_schemes"] == ["https"]
    assert telegram.config["request_timeout"] == 40.0


def test_adapter_validation_rejects_unknown_fields_at_direct_construction(tmp_path: Path) -> None:
    with pytest.raises(AdapterConfigValidationError, match="unexpected"):
        TerminalAdapter(_make_runtime(tmp_path), {"unexpected": True})


def test_onebot_legacy_paths_normalize_without_stringifying_none(tmp_path: Path) -> None:
    runtime = _make_runtime(tmp_path)
    legacy = OneBot11Adapter(
        runtime,
        {
            "event_path": "/legacy/events",
            "api_path": "/legacy/api",
            "api_url": "http://127.0.0.1:5800",
        },
    )
    defaulted = OneBot11Adapter(runtime)

    assert legacy.path_event == "/legacy/events"
    assert legacy.path_api == "/legacy/api"
    assert legacy.api_base_url == "http://127.0.0.1:5800"
    assert "event_path" not in legacy.config
    assert "api_path" not in legacy.config
    assert "api_url" not in legacy.config
    assert defaulted.path_event == defaulted.path
    assert defaulted.path_api == defaulted.path
    assert defaulted.path_event != "None"
    assert defaulted.path_api != "None"


def test_onebot_explicit_empty_paths_remain_explicit(tmp_path: Path) -> None:
    adapter = OneBot11Adapter(
        _make_runtime(tmp_path),
        {"path_event": "", "path_api": ""},
    )

    assert adapter.path_event == ""
    assert adapter.path_api == ""


def test_load_config_normalizes_terminal_and_onebot_aliases(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        dedent("""
            [adapter.terminal]
            exit_commands = ["stop"]

            [adapter.onebot11]
            event_path = "/events"
            api_path = "/api"
            api_url = "http://127.0.0.1:5800"
            """).strip(),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config["adapter"]["terminal"]["exit_commands"] == ["stop"]
    assert config["adapter"]["onebot11"]["path_event"] == "/events"
    assert config["adapter"]["onebot11"]["path_api"] == "/api"
    assert config["adapter"]["onebot11"]["api_base_url"] == "http://127.0.0.1:5800"


def test_runtime_and_direct_adapter_construction_share_normalized_config(tmp_path: Path) -> None:
    raw_config = {"exit_commands": ["stop"]}
    runtime = Runtime(
        {
            "runtime": {"adapters": ["terminal"]},
            "adapter": {"terminal": raw_config},
            "plugin": {},
            "state": {},
            "__meta__": {"root_dir": str(tmp_path)},
        },
        base_path=tmp_path,
    )

    direct = TerminalAdapter(runtime, raw_config)
    runtime.load_adapters()

    assert runtime.adapters[0].config == direct.config
    assert runtime.adapters[0].config_obj == direct.config_obj


@pytest.mark.parametrize(
    ("model", "field"),
    [
        (OneBot11ConfigModel, "access_token"),
        (WebhookConfigModel, "access_token"),
        (WebhookConfigModel, "signature_secret"),
        (TelegramConfigModel, "token"),
    ],
)
def test_builtin_adapter_secret_fields_are_explicitly_write_only(
    model: type[BaseModel],
    field: str,
) -> None:
    schema = model.model_json_schema()

    assert schema["properties"][field]["writeOnly"] is True


@pytest.mark.parametrize(
    ("model", "field", "default"),
    [
        (TerminalConfigModel, "exit_commands", ["/quit", "/exit", ":q"]),
        (WebhookConfigModel, "reply_url_allowlist", []),
        (WebhookConfigModel, "allowed_reply_schemes", ["https"]),
        (TelegramConfigModel, "allowed_updates", ["message"]),
    ],
)
def test_builtin_adapter_factory_defaults_are_static_in_schema(
    model: type[BaseModel],
    field: str,
    default: object,
) -> None:
    schema = model.model_json_schema()

    assert schema["properties"][field]["default"] == default
