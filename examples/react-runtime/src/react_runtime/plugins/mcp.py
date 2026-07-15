from __future__ import annotations

from typing import Any

from fastmcp import Client
from iamai import Plugin
from pydantic import BaseModel, Field


class McpConfig(BaseModel):
    mcp_server: dict[str, dict[str, object]] = Field(default_factory=dict)


class McpPlugin(Plugin):
    name = "mcp"
    description = "用于与MCP服务器进行通信和交互"
    config_model = McpConfig

    async def startup(self) -> None:
        self.state.setdefault("client", {})
        self.state.setdefault("tools", {})
        config = self.config_obj
        if not isinstance(config, McpConfig):
            config = McpConfig.model_validate(self.config)
        for server_name, server_cfg in config.mcp_server.items():
            client = Client({"mcpServers": {server_name: server_cfg}})
            await client.__aenter__()
            self.state["client"][server_name] = client
            mcp_tools = await client.list_tools()
            self.state["tools"][server_name] = [(tool.name, tool.description) for tool in mcp_tools]

    async def shutdown(self) -> None:
        for client in self.state.get("client", {}).values():
            await client.__aexit__(None, None, None)

    async def call_tool(self, tool_name: str, tool_input: Any) -> str:
        arguments = tool_input if isinstance(tool_input, dict) else {"input": tool_input}
        for server_name, client in self.state["client"].items():
            prefix = f"{server_name}."
            if tool_name.startswith(prefix):
                raw_name = tool_name[len(prefix) :]
                result = await client.call_tool(raw_name, arguments)
                return str(result)
        raise ValueError(f"unknown MCP tool: {tool_name}")

    def describe_tools(self) -> str:
        lines = []
        for server_name, tools in self.state.get("tools", {}).items():
            for name, desc in tools:
                lines.append(f"{server_name}.{name}: {desc}")
        return "\n".join(lines) or "(no MCP tools)"
