from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest
from iamai.agent import AgentError, LLMClient, LLMConfig

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_SHARED = ROOT / "examples" / "_shared" / "src"
sys.path.insert(0, str(EXAMPLE_SHARED))

from iamai_example_utils import resolve_llm_settings  # noqa: E402


def test_llm_client_applies_env_fallback_for_dataclass_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env-test")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("OPENAI_MODEL", "env-model")

    client = LLMClient(LLMConfig())

    assert client.config.api_key == "sk-env-test"
    assert client.config.base_url == "https://example.test/v1"
    assert client.config.model == "env-model"


def test_resolve_llm_settings_populates_env_defaults_for_dataclass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env-test")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("OPENAI_MODEL", "env-model")

    config_obj = type("Config", (), {"llm": LLMConfig(temperature=0.8, max_tokens=620)})()
    settings = resolve_llm_settings(config_obj, default_temperature=0.8, default_max_tokens=620)

    assert settings.api_key == "sk-env-test"
    assert settings.base_url == "https://example.test/v1"
    assert settings.model == "env-model"
    assert settings.temperature == 0.8
    assert settings.max_tokens == 620


def test_llm_client_uses_documented_mock_environment_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("IAMAI_LLM_MOCK", "1")
    monkeypatch.delenv("iamai_LLM_MOCK", raising=False)

    result = asyncio.run(LLMClient(LLMConfig()).chat_text([{"role": "user", "content": "hello"}]))

    assert result == "mock llm response"


def test_llm_client_parses_extra_body_for_openai_compatible_providers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class FakeCompletions:
        async def create(self, **kwargs: Any) -> Any:
            captured.update(kwargs)
            message = SimpleNamespace(content="provider response")
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    class FakeAsyncOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            captured["client"] = kwargs
            self.chat = SimpleNamespace(completions=FakeCompletions())

        async def close(self) -> None:
            return None

    openai_module = ModuleType("openai")
    openai_module.AsyncOpenAI = FakeAsyncOpenAI  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "openai", openai_module)
    monkeypatch.delenv("IAMAI_LLM_MOCK", raising=False)

    client = LLMClient(
        {
            "api_key": "sk-test",
            "model": "test-model",
            "extra_body": '{"thinking": {"type": "enabled"}}',
        }
    )
    result = asyncio.run(client.chat_text([{"role": "user", "content": "hello"}]))

    assert result == "provider response"
    assert captured["extra_body"] == {"thinking": {"type": "enabled"}}


def test_llm_client_rejects_invalid_extra_body_json() -> None:
    with pytest.raises(AgentError, match="OPENAI_EXTRA_BODY must be a JSON object"):
        LLMClient({"extra_body": "not-json"})
