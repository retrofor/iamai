from __future__ import annotations

import logging
import re

from iamai import Context, Plugin, command, message_handler
from pydantic import BaseModel, Field

from skill_chat_runtime.data import read_json
from skill_chat_runtime.skilllib import RouteDecision, TraceRecord, slugify, summarize

logger = logging.getLogger(__name__)


class RouteRule(BaseModel):
    tool_name: str
    tokens: list[str] = Field(default_factory=list)
    reason: str = ""
    pattern: str = ""


class RouterConfig(BaseModel):
    skill_threshold: float = 0.45
    route_rules_file: str = "data/route_rules.json"


class RouterPlugin(Plugin):
    name = "router"
    description = "Routes chat messages through skills and tools."
    requires = ("memory", "skills", "tools")
    load_after = ("memory", "skills", "tools")
    config_model = RouterConfig

    def _route_rules(self) -> list[RouteRule]:
        # Keep routing text in a data file so the demo can be tuned without code changes.
        config_file = (
            self.config_obj.route_rules_file
            if self.config_obj is not None
            else "data/route_rules.json"
        )
        raw_items = read_json(config_file)
        return [RouteRule.model_validate(item) for item in raw_items]

    def _route(self, text: str) -> RouteDecision:
        clean = " ".join(text.split()).strip()
        skills = self.runtime.get_plugin("skills")
        candidate, score, reasons = skills.best_match(clean)
        if candidate is not None and score >= float(self.config.get("skill_threshold", 0.45)):
            return RouteDecision(
                source="skill",
                skill_id=candidate.id,
                skill_title=candidate.title,
                tool_name=candidate.tool_name,
                tool_input=clean,
                reason="; ".join(reasons[:3]),
                score=score,
            )

        lower = clean.lower()
        for rule in self._route_rules():
            if rule.pattern and re.fullmatch(rule.pattern, clean):
                return RouteDecision(
                    source="heuristic",
                    tool_name=rule.tool_name,
                    tool_input=clean,
                    reason=rule.reason or "heuristic rule",
                    score=0.5,
                )
            if rule.tokens and any(token.lower() in lower for token in rule.tokens):
                return RouteDecision(
                    source="heuristic",
                    tool_name=rule.tool_name,
                    tool_input=clean,
                    reason=rule.reason or "heuristic rule",
                    score=0.5,
                )
        return RouteDecision(
            source="heuristic",
            tool_name="echo",
            tool_input=clean,
            reason="fallback reply",
            score=0.1,
        )

    async def _turn(self, ctx: Context, text: str, *, origin: str) -> str:
        clean = " ".join(text.split()).strip()
        if not clean:
            return ""
        tools = self.runtime.get_plugin("tools")
        memory = self.runtime.get_plugin("memory")
        skills = self.runtime.get_plugin("skills")
        decision = self._route(clean)
        logger.info(
            "route origin=%s source=%s tool=%s skill=%s reason=%s input=%s",
            origin,
            decision.source,
            decision.tool_name,
            decision.skill_id or "-",
            decision.reason,
            summarize(clean, limit=80),
        )
        trace = TraceRecord(
            input_text=clean,
            mode=origin,
            tool_name=decision.tool_name,
            tool_input=decision.tool_input or clean,
            route_reason=decision.reason,
            skill_id=decision.skill_id,
            skill_title=decision.skill_title,
            source_signature=decision.skill_id
            or f"{decision.tool_name}:{slugify(clean, fallback='input')}",
            path=[
                f"{decision.source}:{decision.skill_id or decision.tool_name}",
                f"tool:{decision.tool_name}",
            ],
        )
        try:
            reply = await tools.run_tool(decision.tool_name, decision.tool_input or clean, ctx)
            trace.status = "success"
            trace.reply_text = reply
            memory.append_trace(trace)
            if origin != "inspect" and bool(skills.config.get("auto_promote", True)):
                generated = skills.ingest_trace(trace)
                if generated is not None:
                    logger.info(
                        "auto skill promoted skill_id=%s source_trace=%s",
                        generated.id,
                        trace.trace_id,
                    )
            return reply
        except Exception as exc:  # pragma: no cover - example runtime path
            trace.status = "failure"
            trace.error = str(exc)
            trace.reply_text = f"tool {decision.tool_name} failed: {exc}"
            memory.append_trace(trace)
            logger.exception("tool execution failed")
            return trace.reply_text

    @command("chat", priority=10)
    async def chat(self, ctx: Context, args: str) -> None:
        text = args.strip()
        if not text:
            await ctx.reply("Usage: /chat <message>")
            return
        await ctx.reply(await self._turn(ctx, text, origin="command"))

    @command("route", priority=11)
    async def route(self, ctx: Context, args: str) -> None:
        text = args.strip()
        if not text:
            await ctx.reply("Usage: /route <message>")
            return
        reply = await self._turn(ctx, text, origin="inspect")
        trace = self.runtime.get_plugin("memory").last_trace()
        if trace is None:
            await ctx.reply(reply)
            return
        await ctx.reply(
            "\n".join(
                [
                    "route decision:",
                    f"- tool={trace.tool_name}",
                    f"- path={' -> '.join(trace.path) if trace.path else trace.tool_name}",
                    f"- reason={trace.route_reason}",
                    f"- status={trace.status}",
                    "",
                    reply,
                ]
            )
        )

    @message_handler(priority=50)
    async def free_chat(self, ctx: Context) -> None:
        text = ctx.text.strip()
        if not text or text.startswith("/"):
            return
        await ctx.reply(await self._turn(ctx, text, origin="message"))
