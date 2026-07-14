"""Built-in management commands for reloading and runtime inspection."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from pydantic import BaseModel

from ..permissions import permission
from ..plugin import Plugin, command

if TYPE_CHECKING:
    from ..context import Context


class ManagementConfig(BaseModel):
    """Configuration for the built-in management plugin."""

    allow_reload: bool = False
    allow_config_reload: bool = False
    allow_introspection: bool = False
    reload_requires_superuser: bool = True
    introspection_requires_superuser: bool = True


class ManagementPlugin(Plugin):
    """Expose operator commands for reloads, health, metrics, and introspection."""

    name = "management"
    description = "Builtin management commands for reloading and runtime inspection."
    priority = 0
    config_model = ManagementConfig

    def _is_superuser(self, ctx: "Context") -> bool:
        return (ctx.event.user_id or "") in ctx.runtime.superusers()

    def _can_reload(self, ctx: "Context") -> bool:
        if not self.config.get("allow_reload", False):
            return False
        return not self.config.get("reload_requires_superuser", True) or self._is_superuser(ctx)

    def _can_reload_config(self, ctx: "Context") -> bool:
        if not self.config.get("allow_config_reload", self.config.get("allow_reload", False)):
            return False
        return not self.config.get("reload_requires_superuser", True) or self._is_superuser(ctx)

    def _can_introspect(self, ctx: "Context") -> bool:
        if not self.config.get("allow_introspection", False):
            return False
        return not self.config.get("introspection_requires_superuser", True) or self._is_superuser(
            ctx
        )

    @command(
        "reload",
        priority=0,
        permission=permission(lambda ctx: ctx.plugin._can_reload(ctx)),
    )
    async def reload_plugins_command(self, ctx: "Context") -> None:
        """Schedule a plugin reload."""
        ctx.runtime.request_plugin_reload()
        await ctx.reply("已调度插件热重载。")

    @command(
        "reload-config",
        priority=0,
        permission=permission(lambda ctx: ctx.plugin._can_reload_config(ctx)),
    )
    async def reload_config_command(self, ctx: "Context") -> None:
        """Schedule a full configuration reload."""
        ctx.runtime.request_config_reload()
        await ctx.reply("已调度配置热重载。")

    @command(
        "plugins",
        priority=1,
        permission=permission(lambda ctx: ctx.plugin._can_introspect(ctx)),
    )
    async def list_plugins_command(self, ctx: "Context") -> None:
        """List loaded plugins."""
        lines = ["plugins:"]
        for info in ctx.runtime.list_plugins():
            tags: list[str] = []
            if info["builtin"]:
                tags.append("builtin")
            if info["requires"]:
                tags.append(f"requires={','.join(info['requires'])}")
            if info["optional_requires"]:
                tags.append(f"optional={','.join(info['optional_requires'])}")
            suffix = f" [{' | '.join(tags)}]" if tags else ""
            lines.append(f"{info['load_index']:02d}. {info['name']}{suffix}")
        await ctx.reply("\n".join(lines))

    @command(
        "plugin",
        priority=1,
        permission=permission(lambda ctx: ctx.plugin._can_introspect(ctx)),
    )
    async def plugin_detail_command(self, ctx: "Context", args: str) -> None:
        """Show metadata for one plugin."""
        name = args.strip()
        if not name:
            await ctx.reply("Usage: /plugin <name>")
            return
        for info in ctx.runtime.list_plugins():
            if info["name"] != name:
                continue
            lines = [f"plugin: {name}"]
            lines.append(f"description: {info['description']}")
            lines.append(f"ref: {info['ref']}")
            lines.append(f"load_index: {info['load_index']} priority: {info['priority']}")
            lines.append(f"requires: {', '.join(info['requires']) or '-'}")
            lines.append(f"optional: {', '.join(info['optional_requires']) or '-'}")
            lines.append(f"config_model: {info['config_model'] or '-'}")
            await ctx.reply("\n".join(lines))
            return
        await ctx.reply(f"plugin not found: {name}")

    @command(
        "plugin-config",
        priority=1,
        permission=permission(lambda ctx: ctx.plugin._can_introspect(ctx)),
    )
    async def plugin_config_command(self, ctx: "Context", args: str) -> None:
        """Show a plugin configuration JSON schema."""
        name = args.strip()
        if not name:
            await ctx.reply("Usage: /plugin-config <name>")
            return
        schema = ctx.runtime.get_plugin_schema(name)
        if schema is None:
            await ctx.reply(f"plugin has no config schema or does not exist: {name}")
            return
        await ctx.reply(json.dumps(schema, ensure_ascii=False, indent=2))

    @command(
        "handlers",
        priority=2,
        permission=permission(lambda ctx: ctx.plugin._can_introspect(ctx)),
    )
    async def list_handlers_command(self, ctx: "Context") -> None:
        """List registered plugin handlers."""
        handlers = ctx.runtime.list_handlers()
        if not handlers:
            await ctx.reply("handlers: none")
            return
        lines = ["handlers:"]
        for info in handlers:
            target = info["name"]
            if info["kind"] == "command" and info["commands"]:
                target = ", ".join(info["commands"])
            lines.append(
                f"- {info['plugin']}.{info['name']} "
                f"kind={info['kind']} target={target} priority={info['priority']}"
            )
        await ctx.reply("\n".join(lines))

    @command(
        "adapters",
        priority=3,
        permission=permission(lambda ctx: ctx.plugin._can_introspect(ctx)),
    )
    async def list_adapters_command(self, ctx: "Context") -> None:
        """List loaded adapters."""
        lines = ["adapters:"]
        for info in ctx.runtime.list_adapters():
            lines.append(f"- {info['name']} ({info['class']}) config={info['config']}")
        await ctx.reply("\n".join(lines))

    @command(
        "health",
        priority=4,
        permission=permission(lambda ctx: ctx.plugin._can_introspect(ctx)),
    )
    async def health_command(self, ctx: "Context") -> None:
        """Show runtime health information."""
        health = ctx.runtime.health()
        lines = ["health:"]
        for key, value in health.items():
            lines.append(f"- {key}: {value}")
        await ctx.reply("\n".join(lines))

    @command(
        "metrics",
        priority=5,
        permission=permission(lambda ctx: ctx.plugin._can_introspect(ctx)),
    )
    async def metrics_command(self, ctx: "Context") -> None:
        """Show runtime counters."""
        metrics = ctx.runtime.list_metrics()
        if not metrics:
            await ctx.reply("metrics: none")
            return
        lines = ["metrics:"]
        for item in metrics:
            labels = ", ".join(f"{key}={value}" for key, value in item["labels"].items())
            suffix = f" {{{labels}}}" if labels else ""
            lines.append(f"- {item['name']}{suffix}: {item['value']}")
        await ctx.reply("\n".join(lines))

    @command(
        "sessions",
        priority=6,
        permission=permission(lambda ctx: ctx.plugin._can_introspect(ctx)),
    )
    async def sessions_command(self, ctx: "Context") -> None:
        """Show active session waiters."""
        sessions = ctx.runtime.list_sessions()
        if not sessions:
            await ctx.reply("sessions: none")
            return
        lines = ["sessions:"]
        for session in sessions:
            lines.append(f"- key={session['key']} done={session['done']}")
        await ctx.reply("\n".join(lines))

    @command(
        "trace",
        priority=7,
        permission=permission(lambda ctx: ctx.plugin._can_introspect(ctx)),
    )
    async def trace_command(self, ctx: "Context", args: str) -> None:
        """Show trace summary or the latest trace payload."""
        traces = ctx.runtime.list_plugin_traces()
        if not traces:
            await ctx.reply("trace: none")
            return
        latest = traces[-1]
        if args.strip() == "last":
            await ctx.reply(json.dumps(latest, ensure_ascii=False, indent=2))
            return
        await ctx.reply(f"traces: {len(traces)} latest_plugin={latest.get('plugin')}")
