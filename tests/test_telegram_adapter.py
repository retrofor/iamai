from __future__ import annotations

import asyncio
from pathlib import Path
from textwrap import dedent
from typing import Any

import pytest
from iamai import Message, Runtime
from iamai.adapters.telegram import TelegramAdapter
from iamai.config import load_config


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


def test_load_config_accepts_builtin_telegram_adapter(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        dedent("""
            [runtime]
            adapters = ["telegram"]

            [adapter.telegram]
            token = "123:secret"
            poll_timeout = 5
            allowed_updates = ["message", "edited_message"]
            """).strip(),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config["adapter"]["telegram"]["token"] == "123:secret"
    assert config["adapter"]["telegram"]["poll_timeout"] == 5


def test_runtime_loads_telegram_adapter(tmp_path: Path) -> None:
    runtime = Runtime(
        {
            "runtime": {"adapters": ["telegram"]},
            "adapter": {"telegram": {"token": "123:secret"}},
            "plugin": {},
            "state": {},
            "__meta__": {"root_dir": str(tmp_path)},
        },
        base_path=tmp_path,
    )

    runtime.load_adapters()

    assert runtime.adapters[0].name == "telegram"


def test_telegram_update_normalizes_to_message_event(tmp_path: Path) -> None:
    adapter = TelegramAdapter(_make_runtime(tmp_path), {"token": "123:secret"})

    event = adapter._normalize_update(
        {
            "update_id": 10,
            "message": {
                "message_id": 20,
                "from": {"id": 30},
                "chat": {"id": -40, "type": "group"},
                "text": "hello",
            },
        }
    )

    assert event is not None
    assert event.adapter == "telegram"
    assert event.platform == "telegram"
    assert event.type == "message"
    assert event.detail_type == "group"
    assert event.user_id == "30"
    assert event.channel_id == "-40"
    assert event.guild_id == "-40"
    assert event.text == "hello"


def test_telegram_send_message_calls_send_message_api(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict[str, Any]] = []

    async def fake_request_json(url: str, **kwargs: Any) -> dict[str, Any]:
        calls.append({"url": url, **kwargs})
        return {"ok": True, "result": {"message_id": 1}}

    monkeypatch.setattr("iamai.adapters.telegram.request_json", fake_request_json)
    adapter = TelegramAdapter(_make_runtime(tmp_path), {"token": "123:secret"})

    result = asyncio.run(adapter.send_message(Message("pong"), target=12345))

    assert result == {"message_id": 1}
    assert calls[0]["url"].endswith("/bot123:secret/sendMessage")
    assert calls[0]["json_body"] == {"chat_id": 12345, "text": "pong"}


def test_telegram_call_api_raises_on_failed_response(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_request_json(url: str, **kwargs: Any) -> dict[str, Any]:
        return {"ok": False, "description": "Bad Request"}

    monkeypatch.setattr("iamai.adapters.telegram.request_json", fake_request_json)
    adapter = TelegramAdapter(_make_runtime(tmp_path), {"token": "123:secret"})

    with pytest.raises(RuntimeError, match="Bad Request"):
        asyncio.run(adapter.call_api("sendMessage", chat_id=1, text="x"))
