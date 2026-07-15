from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

from iamai import AgentError, LLMClient, LLMConfig
from iamai.agent import clip_text as _clip_text
from iamai.agent import format_transcript as _format_transcript
from iamai.config import load_env_file
from pydantic import BaseModel

load_env_file(Path.cwd() / ".env")

DEFAULT_BASE_URL: str | None = os.getenv("OPENAI_BASE_URL")
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "kimi-k2.5")
LLMSettings = LLMConfig
LLMError = AgentError
clip_text = _clip_text
format_transcript = _format_transcript


def resolve_llm_settings(
    config_obj: Any | None,
    *,
    default_temperature: float = 0.7,
    default_max_tokens: int = 800,
) -> LLMSettings:
    raw = getattr(config_obj, "llm", None) if config_obj is not None else None
    if isinstance(raw, BaseModel):
        payload = raw.model_dump(mode="python")
    elif isinstance(raw, dict):
        payload = dict(raw)
    elif isinstance(raw, LLMConfig):
        payload = asdict(raw)
    else:
        payload = {}
    base_url_default = os.getenv("OPENAI_BASE_URL") or DEFAULT_BASE_URL
    model_default = os.getenv("OPENAI_MODEL") or DEFAULT_MODEL
    if payload.get("base_url") in (None, ""):
        payload["base_url"] = base_url_default
    if not payload.get("model") or payload.get("model") == LLMConfig().model:
        payload["model"] = model_default
    if payload.get("temperature") is None:
        payload["temperature"] = default_temperature
    if payload.get("max_tokens") is None:
        payload["max_tokens"] = default_max_tokens
    return LLMConfig.from_mapping(payload)


async def chat_text(
    settings: LLMSettings,
    messages: list[dict[str, str]],
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    return await LLMClient(settings).chat_text(
        messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )


async def chat_json(
    settings: LLMSettings,
    messages: list[dict[str, str]],
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> dict[str, Any] | list[Any]:
    return cast(
        dict[str, Any] | list[Any],
        await LLMClient(settings).chat_json(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
        ),
    )
