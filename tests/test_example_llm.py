from __future__ import annotations

import sys
from pathlib import Path

from iamai.agent import LLMClient, LLMConfig

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_SHARED = ROOT / "examples" / "_shared" / "src"
sys.path.insert(0, str(EXAMPLE_SHARED))

from iamai_example_utils import resolve_llm_settings  # noqa: E402


def test_llm_client_applies_env_fallback_for_dataclass_config(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env-test")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("OPENAI_MODEL", "env-model")

    client = LLMClient(LLMConfig())

    assert client.config.api_key == "sk-env-test"
    assert client.config.base_url == "https://example.test/v1"
    assert client.config.model == "env-model"


def test_resolve_llm_settings_populates_env_defaults_for_dataclass(monkeypatch) -> None:
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
