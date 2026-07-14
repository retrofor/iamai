from __future__ import annotations

import ast
import operator
import random
import re
from collections.abc import Callable
from typing import Any

from iamai import Context, Plugin, ToolRegistry, command

_BINARY_OPS: dict[type[ast.operator], Callable[[Any, Any], Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPS: dict[type[ast.unaryop], Callable[[Any], Any]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class ToolsPlugin(Plugin):
    name = "tools"
    description = "Local tools available to the ReAct agent."
    requires = ("memory",)

    def startup_registry(self) -> ToolRegistry:
        registry = ToolRegistry()
        registry.register(
            "math",
            "evaluate arithmetic",
            lambda value, **_: self._run_math(str(value or "")),
        )
        registry.register(
            "remember",
            "store a fact — input is plain text, e.g. 用户叫简律纯",
            lambda value, **_: self._remember(str(value or "")),
        )
        registry.register(
            "recall",
            "search notes by keyword — input is a single word/phrase, e.g. 简律纯. empty input lists recent notes",
            lambda value, **_: self._recall(str(value or "")),
        )
        registry.register(
            "roll",
            "roll dice like d20 or 2d6",
            lambda value, **_: self._roll(str(value or "d20")),
        )
        registry.register("profile", "show the current user and adapter", self._profile)
        self.state["registry"] = registry
        return registry

    async def startup(self) -> None:
        self.startup_registry()

    def registry(self) -> ToolRegistry:
        value = self.state.get("registry")
        if isinstance(value, ToolRegistry):
            return value
        return self.startup_registry()

    def describe_tools(self) -> str:
        return self.registry().describe()

    async def run_tool(self, tool_name: str, tool_input: str, ctx: Context) -> str:
        return str(await self.registry().call(tool_name, tool_input, ctx=ctx))

    def _profile(self, value: str, *, ctx: Context) -> str:
        return (
            f"user_id={ctx.event.user_id or 'unknown'} "
            f"channel_id={ctx.event.channel_id or 'unknown'} "
            f"adapter={ctx.event.adapter}"
        )

    def _remember(self, value: str) -> str:
        text = " ".join(value.split()).strip()
        if not text:
            return "Nothing stored."
        memory = self.runtime.get_plugin("memory")
        notes = memory.state.setdefault("notes", [])
        notes.append(text)
        limit = int(memory.config.get("note_limit", 12))
        if len(notes) > limit:
            del notes[:-limit]
        return f"Stored note: {text}"

    def _recall(self, query: str) -> str:
        memory = self.runtime.get_plugin("memory")
        notes = memory.state.get("notes", [])
        if not notes:
            return "No notes stored."
        token = query.strip().lower()
        if not token:
            return " | ".join(notes[-5:])
        matches = [item for item in notes if token in item.lower()]
        return " | ".join(matches[-5:]) if matches else "No matching note."

    def _roll(self, token: str) -> str:
        match = re.fullmatch(r"(?:(\d+)d)?(\d+)", token.strip())
        if match is None:
            raise ValueError("roll expects d20 or 2d6 style input")
        count = int(match.group(1) or 1)
        sides = int(match.group(2))
        if count < 1 or count > 8 or sides < 2 or sides > 100:
            raise ValueError("roll out of supported range")
        values = [random.randint(1, sides) for _ in range(count)]
        return f"{values} total={sum(values)}"

    def _run_math(self, expression: str) -> str:
        if not expression.strip():
            raise ValueError("math expects an expression")
        tree = ast.parse(expression, mode="eval")
        return str(self._eval_node(tree.body))

    def _eval_node(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPS:
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return _BINARY_OPS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
            value = self._eval_node(node.operand)
            return _UNARY_OPS[type(node.op)](value)
        raise ValueError("unsupported math expression")

    @command("remember", priority=70)
    async def remember(self, ctx: Context, args: str) -> None:
        await ctx.reply(self._remember(args))
