from iamai import Plugin
from pydantic import BaseModel
from fastmcp import Client


class McpConfig(BaseModel):
    mcp_sever:dict[str, dict[str, object]]

class McpPlugin(Plugin):
    name = "mcp"
    description = "用于与MCP服务器进行通信和交互"
    config_model = McpConfig

    async def startup(self) -> None:
        self.state.setdefault("client", {})
        self.state.setdefault("tools", {})
        for sever_name, sever_cfg in self.config_obj.mcp_sever.items():  # ty:ignore[unresolved-attribute]
            client = Client({
                "mcpServers": {sever_name: sever_cfg}
            })
            await client.__aenter__()
            self.state["client"][sever_name] = client
            # 加载工具列表
            mcp_tools = await client.list_tools()
            self.state["tools"][sever_name] = [
                (mt.name, mt.description) for mt in mcp_tools
            ]

    async def shutdown(self) -> None:
        for client in self.state.get("client", {}).values():
            await client.__aexit__(None, None, None)

    async def call_tool(self, tool_name: str, tool_input: dict) -> str:
        for sever_name, client in self.state["client"].items():
            prefix = f"{sever_name}."
            if tool_name.startswith(prefix):
                raw_name = tool_name[len(prefix):]
                result = await client.call_tool(raw_name, tool_input)
                return str(result)
        raise ValueError(f"unknown MCP tool: {tool_name}")

    def describe_tools(self) -> str:
        lines = []
        for sever_name, tools in self.state.get("tools", {}).items():
            for name, desc in tools:
                lines.append(f"{sever_name}.{name}: {desc}")
        return "\n".join(lines) or "(no MCP tools)"


