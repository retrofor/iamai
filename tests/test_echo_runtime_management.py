from __future__ import annotations

import asyncio
from pathlib import Path

from iamai import Event, Message, Runtime
from iamai.config import load_config

ROOT = Path(__file__).resolve().parents[1]


def test_echo_runtime_terminal_config_exposes_management_commands() -> None:
    async def run() -> list[str]:
        config_path = ROOT / "examples/echo-runtime/config.terminal.toml"
        config = load_config(config_path)
        config["logging"]["file"] = None
        runtime = Runtime(config, base_path=Path(config["__meta__"]["root_dir"]))
        await runtime.bootstrap()
        adapter = runtime.get_adapter("terminal")
        sent: list[str] = []

        async def send_message(
            message: Message,
            *,
            event: Event | None = None,
            target: object | None = None,
        ) -> dict[str, object]:
            sent.append(Message.ensure(message).render_text())
            return {
                "ok": True,
                "event_id": getattr(event, "id", None),
                "target": target,
            }

        adapter.send_message = send_message  # type: ignore[method-assign]
        event = Event(
            id="test-management",
            adapter="terminal",
            platform="terminal",
            type="message",
            detail_type="line",
            user_id="terminal-user",
            channel_id="terminal",
            self_id="terminal-runtime",
            message=Message("/plugins"),
        )
        await runtime.dispatch(event, adapter)
        await asyncio.sleep(0)
        await runtime.shutdown()
        return sent

    replies = asyncio.run(run())

    assert replies
    assert "management" in replies[0]
    assert "echo" in replies[0]
