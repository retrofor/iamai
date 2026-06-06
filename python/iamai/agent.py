"""Small agent runtime used by the example runtimes and plugin workflows."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass, field
from typing import Any, cast, Optional

DEFAULT_LLM_MODEL = ""


class AgentError(RuntimeError):
    """Raised when an agent helper cannot complete a model or tool operation."""

    pass


@dataclass(slots=True)
class LLMConfig:
    """Connection and generation settings for an OpenAI-compatible chat model."""

    api_key: str = ""
    base_url: str | None = None
    model: str = DEFAULT_LLM_MODEL
    temperature: float = 0.7
    max_tokens: int = 800
    timeout: float = 60.0

    @classmethod
    def from_mapping(cls, payload: dict[str, Any] | None = None) -> "LLMConfig":
        """Build configuration from a mapping and environment fallbacks."""
        data = dict(payload or {})
        env_model = os.getenv("OPENAI_MODEL", "")
        raw_model = data.get("model")
        return cls(
            api_key=str(data.get("api_key") or os.getenv("OPENAI_API_KEY", "")),
            base_url=_normalize_optional_str(data.get("base_url") or os.getenv("OPENAI_BASE_URL")),
            model=(
                str(env_model or raw_model or DEFAULT_LLM_MODEL)
                if raw_model == DEFAULT_LLM_MODEL and env_model
                else str(raw_model or env_model or DEFAULT_LLM_MODEL)
            ),
            temperature=float(data.get("temperature", 0.7)),
            max_tokens=int(data.get("max_tokens", 800)),
            timeout=float(data.get("timeout", 60.0)),
        )


@dataclass(slots=True)
class TraceEvent:
    """One recorded step in an agent trace."""

    kind: str
    name: str
    input: Any = None
    output: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the trace event into a JSON-compatible dictionary."""
        return {
            "kind": self.kind,
            "name": self.name,
            "input": self.input,
            "output": self.output,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class AgentTrace:
    """Append-only trace used to inspect model calls, tool calls, and observations."""

    name: str
    events: list[TraceEvent] = field(default_factory=list)

    def add(
        self,
        kind: str,
        name: str,
        *,
        input: Any = None,
        output: Any = None,
        **metadata: Any,
    ) -> TraceEvent:
        """Append a trace event and return it."""
        event = TraceEvent(kind=kind, name=name, input=input, output=output, metadata=metadata)
        self.events.append(event)
        return event

    def lines(self, *, limit: int = 12) -> list[str]:
        """Return compact human-readable trace lines."""
        lines: list[str] = []
        for event in self.events[-limit:]:
            output = clip_text(event.output, limit=180) if event.output is not None else ""
            lines.append(f"{event.kind}:{event.name} -> {output}")
        return lines

    def to_dict(self) -> dict[str, Any]:
        """Serialize the full trace into a JSON-compatible dictionary."""
        return {"name": self.name, "events": [event.to_dict() for event in self.events]}


@dataclass(slots=True)
class Tool:
    """Registered callable tool metadata."""

    name: str
    description: str
    callback: Callable[..., Any]
    permission_name: str = ""
    input_schema: dict[str, Any] | None = None
    audit_fields: tuple[str, ...] = ()
    requires_approval: bool = False
    runtime_capabilities: tuple[str, ...] = ()


class ToolRegistry:
    """Registry for named tools that can be called by agent workflows."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(
        self,
        name: str,
        description: str,
        callback: Callable[..., Any],
        *,
        permission_name: str = "",
        input_schema: dict[str, Any] | None = None,
        audit_fields: tuple[str, ...] | list[str] = (),
        requires_approval: bool = False,
        runtime_capabilities: tuple[str, ...] | list[str] = (),
    ) -> None:
        """Register or replace a named tool."""
        normalized = name.strip().lower()
        if not normalized:
            raise ValueError("tool name cannot be empty")
        self._tools[normalized] = Tool(
            name=normalized,
            description=description,
            callback=callback,
            permission_name=str(permission_name or normalized),
            input_schema=input_schema,
            audit_fields=tuple(str(item) for item in audit_fields),
            requires_approval=bool(requires_approval),
            runtime_capabilities=tuple(str(item) for item in runtime_capabilities),
        )

    def describe(self) -> str:
        """Return a text listing of available tools."""
        if not self._tools:
            return "(no tools)"
        return "\n".join(f"{tool.name}: {tool.description}" for tool in self._tools.values())

    def list_tools(self) -> list[dict[str, Any]]:
        """Return tool metadata for prompts or diagnostics."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "permission_name": tool.permission_name,
                "input_schema": tool.input_schema,
                "audit_fields": list(tool.audit_fields),
                "requires_approval": tool.requires_approval,
                "runtime_capabilities": list(tool.runtime_capabilities),
            }
            for tool in self._tools.values()
        ]

    async def call(
        self,
        name: str,
        tool_input: Any = None,
        *,
        trace: AgentTrace | None = None,
        approved: bool = False,
        approval_callback: Callable[[Tool, Any], bool | Awaitable[bool]] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Call a registered tool by name."""
        normalized = name.strip().lower()
        if normalized not in self._tools:
            raise AgentError(f"unknown tool: {name}")
        tool = self._tools[normalized]
        audit_input = _select_audit_input(tool, tool_input)
        if trace is not None:
            trace.add(
                "tool",
                tool.name,
                input=audit_input,
                permission_name=tool.permission_name,
                requires_approval=tool.requires_approval,
                outcome="started",
            )
        if tool.requires_approval and not approved:
            approved = await _check_tool_approval(tool, tool_input, approval_callback)
        if tool.requires_approval and not approved:
            if trace is not None:
                trace.add(
                    "tool",
                    tool.name,
                    input=audit_input,
                    permission_name=tool.permission_name,
                    requires_approval=True,
                    outcome="denied",
                )
            raise AgentError(f"tool requires approval: {tool.name}")
        try:
            result = tool.callback(tool_input, **kwargs)
            if isinstance(result, Awaitable):
                result = await result
        except Exception as exc:
            if trace is not None:
                trace.add(
                    "tool",
                    tool.name,
                    input=audit_input,
                    output=str(exc),
                    permission_name=tool.permission_name,
                    outcome="error",
                )
            raise
        if trace is not None:
            trace.add(
                "tool",
                tool.name,
                input=audit_input,
                output=clip_text(result),
                permission_name=tool.permission_name,
                outcome="ok",
            )
        return result


class Guardrail:
    """Simple token-based output guardrail."""

    def __init__(self, *blocked_tokens: str) -> None:
        self.blocked_tokens = tuple(token.lower() for token in blocked_tokens if token)

    def check(self, text: str) -> None:
        """Raise ``AgentError`` if ``text`` contains a blocked token."""
        lowered = text.lower()
        for token in self.blocked_tokens:
            if token in lowered:
                raise AgentError(f"guardrail blocked token: {token}")


class LLMClient:
    """Small async client for text and JSON chat completions."""

    def __init__(self, config: LLMConfig | dict[str, Any] | None = None) -> None:
        self.config = (
            LLMConfig.from_mapping(asdict(config))
            if isinstance(config, LLMConfig)
            else LLMConfig.from_mapping(config)
        )

    async def chat_text(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        trace: AgentTrace | None = None,
        response_format: Optional[dict[str,str]] = None
    ) -> str:
        """Call the configured chat model and return stripped text."""
        if os.getenv("iamai_LLM_MOCK"):
            result = _mock_chat_reply(messages)
            if trace is not None:
                trace.add("llm", "mock", input=messages[-1].get("content", ""), output=result)
            return result
        try:
            from openai import AsyncOpenAI
        except Exception as exc:
            raise AgentError("openai package is required for LLMClient") from exc
        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY", "")
        base_url = self.config.base_url or _normalize_optional_str(os.getenv("OPENAI_BASE_URL"))
        if not api_key:
            raise AgentError("OPENAI_API_KEY is not configured")
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=self.config.timeout,
        )
        try:
            response = await client.chat.completions.create(
                model=self.config.model,
                messages=cast(Any, messages),
                temperature=(self.config.temperature if temperature is None else temperature),
                max_tokens=self.config.max_tokens if max_tokens is None else max_tokens,
                response_format=response_format
            )
        except Exception as exc:
            raise AgentError(f"chat completion failed: {exc}") from exc
        finally:
            await client.close()
        content = response.choices[0].message.content or ""
        text = content if isinstance(content, str) else str(content)
        result = text.strip()
        if trace is not None:
            trace.add(
                "llm",
                self.config.model,
                input=messages[-1].get("content", ""),
                output=result,
            )
        return result

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        trace: AgentTrace | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Call the chat model and parse a JSON object or array."""
        text = await self.chat_text(
            [
                {
                    "role": "system",
                    "content": "Return valid JSON only. Do not wrap it in markdown fences.",
                },
                
                *messages,
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            trace=trace,
            response_format={"type":"json_object"}
        )
        value = extract_json_value(text)
        if isinstance(value, (dict, list)):
            return value
        raise AgentError(f"model returned non-JSON content: {text}")


def clip_text(value: Any, *, limit: int = 280) -> str:
    """Collapse whitespace and truncate text for trace displays."""
    text = " ".join(str(value).split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def format_transcript(lines: list[str], *, limit: int = 10) -> str:
    """Return a compact transcript string from the last ``limit`` lines."""
    trimmed = [clip_text(line, limit=240) for line in lines[-limit:]]
    return "\n".join(trimmed) if trimmed else "(empty)"


def _select_audit_input(tool: Tool, tool_input: Any) -> Any:
    if not tool.audit_fields or not isinstance(tool_input, dict):
        return clip_text(tool_input)
    return {
        field: clip_text(tool_input.get(field))
        for field in tool.audit_fields
        if field in tool_input
    }


async def _check_tool_approval(
    tool: Tool,
    tool_input: Any,
    approval_callback: Callable[[Tool, Any], bool | Awaitable[bool]] | None,
) -> bool:
    if approval_callback is None:
        return False
    result = approval_callback(tool, tool_input)
    if isinstance(result, Awaitable):
        result = await result
    return bool(result)


def _normalize_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def extract_json_value(text: str) -> Any:
    """Extract a JSON object or array from plain model output."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.DOTALL).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    for opener, closer in (("{", "}"), ("[", "]")):
        start = cleaned.find(opener)
        if start < 0:
            continue
        candidate = _balanced_slice(cleaned, start, opener, closer)
        if candidate is None:
            continue
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise AgentError(f"could not parse JSON from model output: {cleaned}")


def _balanced_slice(text: str, start: int, opener: str, closer: str) -> str | None:
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


def _mock_chat_reply(messages: list[dict[str, str]]) -> str:
    text = "\n".join(message.get("content", "") for message in messages)
    if "Return JSON with keys title, strategy, and steps" in text:
        return json.dumps(
            {
                "title": "mock plan",
                "strategy": "take small verifiable steps",
                "steps": [
                    {
                        "step": "draft",
                        "deliverable": "draft output",
                        "done_when": "draft exists",
                    },
                    {
                        "step": "review",
                        "deliverable": "review note",
                        "done_when": "risks are listed",
                    },
                ],
            }
        )
    if "Return JSON with result, artifact, and risk" in text:
        return json.dumps(
            {
                "result": "step completed",
                "artifact": "artifact ready",
                "risk": "low risk",
            }
        )
    if "Return JSON with thought" in text:
        return json.dumps({"thought": "mock thought", "final": "mock react answer"})
    if "Return JSON with objective, synthesis_brief, and assignments" in text:
        return json.dumps(
            {
                "objective": "mock objective",
                "synthesis_brief": "merge the specialist notes",
                "assignments": [
                    {"role": "strategist", "task": "plan the sequence"},
                    {"role": "builder", "task": "draft the output"},
                    {"role": "skeptic", "task": "review risks"},
                ],
            }
        )
    if "Return JSON with scene and choices" in text:
        return json.dumps(
            {
                "scene": "A mock yearly event appears at the edge of the map.",
                "choices": [
                    {
                        "label": "Choose focus",
                        "note": "You focus well.",
                        "effect": {"wealth": 1, "health": 0, "joy": 1, "reputation": 1},
                    },
                    {
                        "label": "Choose rest",
                        "note": "You recover.",
                        "effect": {"wealth": 0, "health": 2, "joy": 1, "reputation": 0},
                    },
                    {
                        "label": "Choose risk",
                        "note": "You gamble.",
                        "effect": {
                            "wealth": 2,
                            "health": -1,
                            "joy": 0,
                            "reputation": 1,
                        },
                    },
                ],
            }
        )
    return "mock llm response"
