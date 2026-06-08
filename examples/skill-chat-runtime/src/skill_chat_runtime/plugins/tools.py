from __future__ import annotations

import ast
import logging
import operator
from collections.abc import Callable
from typing import Any

from iamai import Context, Plugin, ToolRegistry
from pydantic import BaseModel

from skill_chat_runtime.skilllib import summarize

logger = logging.getLogger(__name__)

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


class ToolsConfig(BaseModel):
    """Configuration for the tools plugin."""

    math_limit: float | None = None


class ToolsPlugin(Plugin):
    """Atomic tools used by the minimal chat router."""

    name = "tools"
    description = "Atomic tools used by the minimal chat router."
    requires = ("memory", "skills")
    load_after = ("memory", "skills")
    config_model = ToolsConfig

    def startup_registry(self) -> ToolRegistry:
        """Create and populate the tool registry, then persist it in state."""
        registry = ToolRegistry()
        for name, description, callback, needs_ctx in (
            ("echo", "echo a compact response", self._echo, False),
            ("math", "evaluate an arithmetic expression", self._math, False),
            ("remember", "store a short note or preference", self._remember, True),
            ("recall", "search stored notes by keyword", self._recall, True),
            ("search_skill", "search stored skill manifests", self._search_skill, True),
        ):
            registry.register(name, description, self._wrap_tool(callback, needs_ctx=needs_ctx))
        self.state["registry"] = registry
        return registry

    def _wrap_tool(self, callback: Callable[..., str], *, needs_ctx: bool) -> Callable[..., str]:
        """Adapt plugin methods to the registry signature without leaking ctx into plain tools."""
        if needs_ctx:
            return lambda value, **kwargs: callback(str(value or ""), **kwargs)
        return lambda value, **_: callback(str(value or ""))

    async def startup(self) -> None:
        """Initialize the tool registry on plugin startup."""
        self.startup_registry()

    def registry(self) -> ToolRegistry:
        """Return the tool registry, re-initializing if needed."""
        value = self.state.get("registry")
        if isinstance(value, ToolRegistry):
            return value
        return self.startup_registry()

    def describe_tools(self) -> str:
        """Return a human-readable description of all registered tools."""
        return self.registry().describe()

    async def run_tool(self, tool_name: str, tool_input: str, ctx: Context) -> str:
        """Invoke a named tool with the given input and return its result."""
        logger.info("tool call tool=%s input=%s", tool_name, summarize(tool_input, limit=80))
        result = await self.registry().call(tool_name, tool_input, ctx=ctx)
        return str(result)

    def _echo(self, value: str) -> str:
        """Echo the input text back to the user."""
        text = " ".join(value.split()).strip()
        if not text:
            return "Say something and I will route it to a tool."
        return f"heard: {text}"

    def _math(self, expression: str) -> str:
        """Evaluate a safe arithmetic expression using AST parsing."""
        expression = expression.strip()
        if not expression:
            raise ValueError("math expects an arithmetic expression")
        tree = ast.parse(expression, mode="eval")
        result = self._eval_node(tree.body)
        limit = self.config.get("math_limit")
        if limit is not None and abs(result) > float(limit):
            raise ValueError(f"result {result} exceeds math_limit {limit}")
        return str(result)

    def _eval_node(self, node: ast.AST) -> Any:
        """Recursively evaluate a safe AST node (constants, binary/unary ops only)."""
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

    def _remember(self, value: str, *, ctx: Context) -> str:
        """Store a short note or preference in the memory plugin."""
        text = " ".join(value.split()).strip()
        if not text:
            return "Nothing stored."
        memory = self.runtime.get_plugin("memory")
        notes = memory.state.setdefault("notes", [])
        notes.append(f"{ctx.event.user_id or 'user'}: {text}")
        limit = int(memory.config.get("note_limit", 12))
        if len(notes) > limit:
            del notes[:-limit]
        logger.info(
            "note stored user=%s note=%s", ctx.event.user_id or "user", summarize(text, limit=80)
        )
        return f"stored note: {text}"

    def _recall(self, value: str, *, ctx: Context) -> str:
        """Search stored notes by keyword and return matches."""
        query = " ".join(value.split()).strip().lower()
        memory = self.runtime.get_plugin("memory")
        notes = [str(item) for item in memory.state.get("notes", [])]
        if not notes:
            return "No notes stored yet."
        if not query:
            return " | ".join(notes[-5:])
        matches = [item for item in notes if query in item.lower()]
        return " | ".join(matches[-5:]) if matches else "No matching note."

    def _search_skill(self, value: str, *, ctx: Context) -> str:
        """Search skill manifests by query and return formatted results."""
        skills = self.runtime.get_plugin("skills")
        return skills.format_search(value or ctx.text, limit=5)
