from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
import re
from uuid import uuid4

from pydantic import BaseModel, Field

from skill_chat_runtime.data import read_json, read_lines

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]+")
_STOPWORDS = {
    line.strip().lower()
    for line in read_lines("stopwords.txt")
    if line.strip() and not line.strip().startswith("#")
}


def now_iso() -> str:
    """Return the current UTC timestamp as an ISO 8601 string (seconds precision)."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def tokenize(text: str) -> list[str]:
    """Split text into meaningful tokens, discarding stopwords."""
    tokens = []
    for token in _TOKEN_RE.findall(text.lower()):
        if token in _STOPWORDS:
            continue
        if token.strip():
            tokens.append(token)
    return tokens


def slugify(text: str, *, fallback: str = "skill") -> str:
    """Convert text into a URL-safe slug using joined tokens."""
    tokens = tokenize(text)
    if not tokens:
        return fallback
    slug = "-".join(tokens[:8])
    slug = re.sub(r"[^a-z0-9\u4e00-\u9fff-]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or fallback


def summarize(text: str, *, limit: int = 120) -> str:
    """Truncate text to *limit* characters, appending '...' if needed."""
    value = " ".join(text.split()).strip()
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 3)].rstrip() + "..."


def clip_lines(lines: Iterable[str], *, limit: int = 6) -> str:
    """Return the last *limit* lines joined by newlines."""
    items = list(lines)[-limit:]
    return "\n".join(items)


class RouteDecision(BaseModel):
    """Routing result produced by the router plugin."""

    source: str = "heuristic"
    skill_id: str = ""
    skill_title: str = ""
    tool_name: str = "llm_reply"
    tool_input: str = ""
    reason: str = ""
    score: float = 0.0


class TraceRecord(BaseModel):
    """Single execution trace capturing input, routing, tool call, and outcome."""

    trace_id: str = Field(default_factory=lambda: uuid4().hex[:12])
    timestamp: str = Field(default_factory=now_iso)
    input_text: str
    reply_text: str = ""
    status: str = "success"
    mode: str = "chat"
    tool_name: str = "llm_reply"
    tool_input: str = ""
    route_reason: str = ""
    skill_id: str = ""
    skill_title: str = ""
    source_signature: str = ""
    path: list[str] = Field(default_factory=list)
    error: str = ""


class SkillManifest(BaseModel):
    """Skill definition with lifecycle tracking, scoring, and reuse metrics."""

    id: str
    title: str
    summary: str
    goal: str = ""
    tool_name: str
    tool_input_hint: str = "{input}"
    triggers: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)
    source_trace_id: str = ""
    source_signature: str = ""
    lifecycle: str = "draft"
    status: str = "generated"
    score: float = 0.0
    reuse_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    consecutive_success_count: int = 0
    last_used_at: str = ""
    last_outcome: str = ""
    promoted_at: str = ""
    deprecated_at: str = ""


def build_skill_manifest(trace: TraceRecord, *, title: str | None = None) -> SkillManifest:
    """Build a new SkillManifest from a trace record."""
    source_text = trace.input_text.strip() or trace.skill_title or trace.tool_name
    name = title.strip() if title and title.strip() else summarize(source_text, limit=48)
    signature = f"{trace.tool_name}:{slugify(source_text, fallback='generated')}"
    skill_id = f"skill.{trace.tool_name}.{slugify(name, fallback='generated')}"
    summary = f"Use {trace.tool_name} to handle {summarize(source_text, limit=72)}."
    goal = f"Handle requests that map to {trace.tool_name} with a reproducible response path."
    triggers = tokenize(source_text)[:8]
    if not triggers and trace.tool_name:
        triggers = [trace.tool_name]
    steps = [item for item in trace.path if item] or [f"tool:{trace.tool_name}"]
    tags = sorted({trace.tool_name, "trace"})
    if trace.skill_id:
        tags.append("routed")
    if trace.status == "failure":
        tags.append("failure")
    return SkillManifest(
        id=skill_id,
        title=name,
        summary=summary,
        goal=goal,
        tool_name=trace.tool_name,
        tool_input_hint="{input}",
        triggers=triggers,
        examples=[source_text],
        steps=steps,
        tags=tags,
        source_trace_id=trace.trace_id,
        source_signature=signature,
        status="generated",
        lifecycle="draft",
        score=0.0,
    )


def score_skill(query: str, manifest: SkillManifest) -> tuple[float, list[str]]:
    """Score a skill manifest against a query using token overlap heuristics."""
    query_tokens = set(tokenize(query))
    if not query_tokens:
        return 0.0, ["empty query"]

    field_tokens = set(tokenize(manifest.title))
    field_tokens |= set(tokenize(manifest.summary))
    field_tokens |= set(tokenize(" ".join(manifest.triggers)))
    field_tokens |= set(tokenize(" ".join(manifest.examples)))
    field_tokens |= set(tokenize(" ".join(manifest.tags)))
    field_tokens.add(manifest.tool_name.lower())

    overlaps = sorted(query_tokens & field_tokens)
    if not overlaps:
        return 0.0, ["no token overlap"]

    title_hits = sorted(query_tokens & set(tokenize(manifest.title)))
    trigger_hits = sorted(query_tokens & set(tokenize(" ".join(manifest.triggers))))
    summary_hits = sorted(query_tokens & set(tokenize(manifest.summary)))
    tag_hits = sorted(query_tokens & set(tokenize(" ".join(manifest.tags))))
    example_hits = sorted(query_tokens & set(tokenize(" ".join(manifest.examples))))

    score = (
        len(title_hits) * 3.0
        + len(trigger_hits) * 2.5
        + len(tag_hits) * 2.0
        + len(summary_hits) * 1.5
        + len(example_hits) * 1.0
    )
    if manifest.tool_name.lower() in query_tokens:
        score += 2.0
    if manifest.lifecycle == "verified":
        score += 2.0
    elif manifest.lifecycle == "promoted":
        score += 3.0
    elif manifest.lifecycle == "draft":
        score += 0.5
    elif manifest.lifecycle == "deprecated":
        score *= 0.3

    total = manifest.success_count + manifest.failure_count
    if total > 0:
        success_rate = manifest.success_count / total
        score += success_rate * 4.0
    score += min(manifest.reuse_count, 10) * 0.25
    reasons = []
    if title_hits:
        reasons.append(f"title:{','.join(title_hits[:3])}")
    if trigger_hits:
        reasons.append(f"triggers:{','.join(trigger_hits[:3])}")
    if tag_hits:
        reasons.append(f"tags:{','.join(tag_hits[:3])}")
    if summary_hits:
        reasons.append(f"summary:{','.join(summary_hits[:3])}")
    if example_hits:
        reasons.append(f"examples:{','.join(example_hits[:3])}")
    if manifest.tool_name.lower() in query_tokens:
        reasons.append(f"tool:{manifest.tool_name}")
    if manifest.lifecycle:
        reasons.append(f"lifecycle:{manifest.lifecycle}")
    return score, reasons or ["matched"]


def format_skill_hit(index: int, manifest: SkillManifest, score: float, reasons: list[str]) -> str:
    """Format a single skill search hit as a one-line summary."""
    return (
        f"{index}. {manifest.title} [{manifest.id}] -> {manifest.tool_name} "
        f"life={manifest.lifecycle} use={manifest.reuse_count} "
        f"score={score:.2f} reasons={'; '.join(reasons[:3])}"
    )


def format_trace(trace: TraceRecord) -> str:
    """Format a trace record as a multi-line diagnostic string."""
    lines = [
        f"trace_id: {trace.trace_id}",
        f"timestamp: {trace.timestamp}",
        f"status: {trace.status}",
        f"mode: {trace.mode}",
        f"input: {trace.input_text}",
        f"tool: {trace.tool_name}",
        f"path: {' -> '.join(trace.path) if trace.path else trace.tool_name}",
        f"route_reason: {trace.route_reason}",
    ]
    if trace.skill_id:
        lines.append(f"skill: {trace.skill_id} ({trace.skill_title})")
    if trace.tool_input:
        lines.append(f"tool_input: {trace.tool_input}")
    if trace.reply_text:
        lines.append(f"reply: {trace.reply_text}")
    if trace.error:
        lines.append(f"error: {trace.error}")
    return "\n".join(lines)


def default_seed_skills() -> list[SkillManifest]:
    """Return a pre-built list of seed skills for initial routing."""
    # Keep the seed skill catalog in a data file so the demo can evolve without code edits.
    raw_items = read_json("seed_skills.json")
    return [SkillManifest.model_validate(item) for item in raw_items]
