from __future__ import annotations

import json
import logging

from iamai import Context, Plugin, command
from pydantic import BaseModel

from skill_chat_runtime.skilllib import (
    SkillManifest,
    TraceRecord,
    build_skill_manifest,
    default_seed_skills,
    format_skill_hit,
    score_skill,
    summarize,
)

logger = logging.getLogger(__name__)


class SkillsConfig(BaseModel):
    """Configuration for the skills plugin."""

    skill_limit: int = 20
    auto_promote: bool = True
    search_limit: int = 5
    verified_success_threshold: int = 2
    promoted_success_threshold: int = 4
    deprecated_failure_threshold: int = 3
    deprecated_failure_ratio: float = 0.6


class SkillsPlugin(Plugin):
    """Stores skill manifests and searches them for routing."""

    name = "skills"
    description = "Stores skill manifests and searches them for routing."
    state_scope = "persistent"
    config_model = SkillsConfig
    requires = ("memory",)

    def _skills(self) -> list[SkillManifest]:
        """Load skills from state, seeding defaults if empty."""
        raw = self.state.setdefault("skills", [])
        skills = [SkillManifest.model_validate(item) for item in raw]
        if not skills:
            skills = default_seed_skills()
            self._store_skills(skills)
        return skills

    def _store_skills(self, skills: list[SkillManifest]) -> None:
        """Persist skills to plugin state, trimming to the configured limit."""
        limit = int(self.config.get("skill_limit", 20))
        trimmed = skills[-limit:]
        self.state["skills"] = [skill.model_dump(mode="python") for skill in trimmed]

    def _bump_lifecycle(self, skill: SkillManifest) -> SkillManifest:
        """Advance or degrade the skill lifecycle based on success/failure metrics."""
        total = skill.success_count + skill.failure_count
        failure_rate = (skill.failure_count / total) if total else 0.0
        verified_threshold = int(self.config.get("verified_success_threshold", 2))
        promoted_threshold = int(self.config.get("promoted_success_threshold", 4))
        deprecated_threshold = int(self.config.get("deprecated_failure_threshold", 3))
        deprecated_ratio = float(self.config.get("deprecated_failure_ratio", 0.6))

        if skill.failure_count >= deprecated_threshold and failure_rate >= deprecated_ratio:
            skill.lifecycle = "deprecated"
            skill.status = "deprecated"
            if not skill.deprecated_at:
                skill.deprecated_at = skill.updated_at
            return skill

        if skill.success_count >= promoted_threshold:
            skill.lifecycle = "promoted"
            skill.status = "promoted"
            if not skill.promoted_at:
                skill.promoted_at = skill.updated_at
            return skill

        if skill.success_count >= verified_threshold:
            skill.lifecycle = "verified"
            skill.status = "verified"
            if not skill.promoted_at:
                skill.promoted_at = skill.updated_at
            return skill

        skill.lifecycle = "draft"
        skill.status = "draft"
        return skill

    def _touch_skill(self, skill: SkillManifest, *, outcome: str, timestamp: str) -> SkillManifest:
        """Update a skill's usage counters and score based on an outcome."""
        skill.reuse_count += 1
        skill.updated_at = timestamp
        skill.last_used_at = timestamp
        skill.last_outcome = outcome
        if outcome == "success":
            skill.success_count += 1
        else:
            skill.failure_count += 1
        total = skill.success_count + skill.failure_count
        if total > 0:
            skill.score = round((skill.success_count / total) * 10 + min(skill.reuse_count, 10) * 0.3, 3)
        return skill

    def _find_skill_index(self, skills: list[SkillManifest], trace: TraceRecord) -> int | None:
        """Find the index of a skill matching the given trace (by ID or signature)."""
        if trace.skill_id:
            for index, skill in enumerate(skills):
                if skill.id == trace.skill_id:
                    return index
        if trace.source_signature:
            for index, skill in enumerate(skills):
                if skill.source_signature and skill.source_signature == trace.source_signature:
                    return index
        return None

    def search(self, query: str, *, limit: int | None = None) -> list[tuple[SkillManifest, float, list[str]]]:
        """Search skills matching *query*, returning top results sorted by score."""
        candidates = []
        for skill in self._skills():
            if skill.lifecycle == "deprecated":
                continue
            score, reasons = score_skill(query, skill)
            if score <= 0:
                continue
            candidates.append((skill, score, reasons))
        candidates.sort(key=lambda item: (item[1], item[0].score, item[0].created_at), reverse=True)
        max_items = limit if limit is not None else int(self.config.get("search_limit", 5))
        return candidates[:max_items]

    def best_match(self, query: str) -> tuple[SkillManifest | None, float, list[str]]:
        """Return the single best matching skill for *query*."""
        hits = self.search(query, limit=1)
        if not hits:
            return None, 0.0, ["no skill matched"]
        return hits[0]

    def ingest_trace(self, trace: TraceRecord, *, title: str | None = None) -> SkillManifest | None:
        """Ingest a trace record: update existing skill or create a new one."""
        skills = self._skills()
        index = self._find_skill_index(skills, trace)
        if trace.status != "success":
            if index is None:
                return None
            skill = skills[index]
            self._touch_skill(skill, outcome="failure", timestamp=trace.timestamp)
            skill.updated_at = trace.timestamp
            skill = self._bump_lifecycle(skill)
            skills[index] = skill
            self._store_skills(skills)
            logger.info("skill degraded skill_id=%s source_trace=%s", skill.id, trace.trace_id)
            return skill

        if index is None:
            manifest = build_skill_manifest(trace, title=title)
            manifest.reuse_count = 1
            manifest.success_count = 1
            manifest.last_used_at = trace.timestamp
            manifest.last_outcome = "success"
            manifest.updated_at = trace.timestamp
            manifest.score = 1.0
            manifest = self._bump_lifecycle(manifest)
            skills.append(manifest)
            self._store_skills(skills)
            logger.info("skill added skill_id=%s source_trace=%s", manifest.id, trace.trace_id)
            return manifest

        skill = skills[index]
        self._touch_skill(skill, outcome="success", timestamp=trace.timestamp)
        skill.last_used_at = trace.timestamp
        skill.updated_at = trace.timestamp
        if trace.input_text and trace.input_text not in skill.examples:
            skill.examples.append(trace.input_text)
        if title and title.strip():
            skill.title = title.strip()
        if trace.skill_title and not skill.title:
            skill.title = trace.skill_title
        if trace.path:
            for step in trace.path:
                if step not in skill.steps:
                    skill.steps.append(step)
        skill = self._bump_lifecycle(skill)
        skills[index] = skill
        self._store_skills(skills)
        logger.info("skill updated skill_id=%s source_trace=%s", skill.id, trace.trace_id)
        return skill

    def promote_latest_trace(self, *, title: str | None = None) -> SkillManifest | None:
        """Promote the latest successful trace into a skill manifest."""
        memory = self.runtime.get_plugin("memory")
        trace = memory.last_trace()
        if trace is None:
            return None
        return self.ingest_trace(trace, title=title)

    def format_search(self, query: str, *, limit: int | None = None) -> str:
        """Format skill search results as a human-readable string."""
        hits = self.search(query, limit=limit)
        if not hits:
            return f'No skill matched "{query}".'
        lines = [f'skills for "{query}":']
        for index, (skill, score, reasons) in enumerate(hits, 1):
            lines.append(format_skill_hit(index, skill, score, reasons))
        return "\n".join(lines)

    @command("skills", priority=20)
    async def skills(self, ctx: Context, args: str) -> None:
        """List matching skills or show all recent skills if no query given."""
        query = args.strip()
        if query:
            await ctx.reply(self.format_search(query))
            return
        skills = self._skills()
        if not skills:
            await ctx.reply("No skill manifest stored yet.")
            return
        lines = ["recent skills:"]
        for skill in [item for item in skills if item.lifecycle != "deprecated"][-6:]:
            lines.append(f"- {skill.id}: {summarize(skill.summary, limit=80)}")
        await ctx.reply("\n".join(lines))

    @command("skill", priority=21)
    async def skill(self, ctx: Context, args: str) -> None:
        """Inspect a specific skill by ID, promote the latest trace, or replay a trace."""
        parts = args.split()
        if not parts:
            await ctx.reply("Usage: /skill <skill_id> [explain|replay] | /skill promote [title]")
            return
        if parts[0] == "promote":
            title = " ".join(parts[1:]).strip() or None
            manifest = self.promote_latest_trace(title=title)
            if manifest is None:
                await ctx.reply("No successful trace to promote yet.")
                return
            await ctx.reply(json.dumps(manifest.model_dump(mode="python"), indent=2, ensure_ascii=False))
            return

        skill_id = parts[0]
        action = parts[1] if len(parts) > 1 else "explain"
        target = next((item for item in self._skills() if item.id == skill_id), None)
        if target is None:
            await ctx.reply(f'No skill found for "{skill_id}".')
            return
        if action == "replay":
            memory = self.runtime.get_plugin("memory")
            trace_data = next(
                (
                    item
                    for item in reversed(memory.state.get("traces", []))
                    if item.get("trace_id") == target.source_trace_id or item.get("skill_id") == target.id
                ),
                None,
            )
            lines = [
                f"skill: {target.id}",
                f"life: {target.lifecycle}",
                f"goal: {target.goal or '-'}",
                f"steps: {' | '.join(target.steps) if target.steps else '-'}",
                f"source: {target.source_trace_id or '-'}",
            ]
            if trace_data is None:
                lines.append("source trace: not found in recent memory")
            else:
                trace = TraceRecord.model_validate(trace_data)
                lines.extend(
                    [
                        "",
                        "source trace:",
                        f"- input: {trace.input_text}",
                        f"- tool: {trace.tool_name}",
                        f"- status: {trace.status}",
                        f"- path: {' -> '.join(trace.path) if trace.path else trace.tool_name}",
                        f"- reply: {trace.reply_text or '-'}",
                        f"- error: {trace.error or '-'}",
                    ]
                )
            await ctx.reply("\n".join(lines))
            return
        await ctx.reply(json.dumps(target.model_dump(mode="python"), indent=2, ensure_ascii=False))
