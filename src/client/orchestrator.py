"""Multi-server MCP connection manager."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool

from client.config import MCPServerConfig
from client.tracing import TraceCollector
from shared.logging import get_logger
from shared.models import TraceEventType

logger = get_logger("client.orchestrator")


@dataclass
class ConnectedServer:
    """An active MCP server connection with its available tools."""

    name: str
    description: str
    session: ClientSession
    tools: list[Tool] = field(default_factory=list)
    _read = None
    _write = None
    _transport_ctx = None
    _session_ctx = None


class MCPOrchestrator:
    """Manages connections to multiple MCP servers and routes tool calls."""

    def __init__(self, tracer: TraceCollector | None = None) -> None:
        self.servers: dict[str, ConnectedServer] = {}
        self.tracer = tracer or TraceCollector()
        self._tool_registry: dict[str, str] = {}

    async def connect_server(self, config: MCPServerConfig) -> ConnectedServer:
        """Connect to a single MCP server via stdio transport."""
        env = {**os.environ, **config.env}
        server_params = StdioServerParameters(
            command=config.command,
            args=config.args,
            env=env,
        )

        transport_ctx = stdio_client(server_params)
        read, write = await transport_ctx.__aenter__()

        session_ctx = ClientSession(read, write)
        session = await session_ctx.__aenter__()
        await session.initialize()

        tools_response = await session.list_tools()
        tools = tools_response.tools

        connected = ConnectedServer(
            name=config.name,
            description=config.description,
            session=session,
            tools=tools,
            _read=read,
            _write=write,
            _transport_ctx=transport_ctx,
            _session_ctx=session_ctx,
        )

        for tool in tools:
            qualified_name = f"{config.name}__{tool.name}"
            self._tool_registry[qualified_name] = config.name
            self._tool_registry[tool.name] = config.name

        self.servers[config.name] = connected

        self.tracer.record(
            TraceEventType.SERVER_CONNECT,
            server_name=config.name,
            metadata={
                "tools": [t.name for t in tools],
                "description": config.description,
            },
        )

        logger.info("Connected to '%s' with %d tools", config.name, len(tools))
        return connected

    async def connect_all(self, configs: list[MCPServerConfig]) -> list[ConnectedServer]:
        """Connect to all configured MCP servers."""
        connected = []
        for config in configs:
            try:
                server = await self.connect_server(config)
                connected.append(server)
            except Exception as exc:
                logger.error("Failed to connect to '%s': %s", config.name, exc)
                self.tracer.record(
                    TraceEventType.ERROR,
                    server_name=config.name,
                    error=str(exc),
                )
        return connected

    async def disconnect_all(self) -> None:
        """Gracefully disconnect from all servers."""
        for name, server in list(self.servers.items()):
            try:
                await server._session_ctx.__aexit__(None, None, None)
                await server._transport_ctx.__aexit__(None, None, None)
                self.tracer.record(TraceEventType.SERVER_DISCONNECT, server_name=name)
                logger.info("Disconnected from '%s'", name)
            except Exception as exc:
                logger.warning("Error disconnecting from '%s': %s", name, exc)
        self.servers.clear()
        self._tool_registry.clear()

    def get_all_tools(self) -> list[dict[str, Any]]:
        """Return all tools from all connected servers in Anthropic tool format."""
        anthropic_tools = []
        for server_name, server in self.servers.items():
            for tool in server.tools:
                anthropic_tools.append(
                    {
                        "name": f"{server_name}__{tool.name}",
                        "description": tool.description or f"Tool from {server_name}",
                        "input_schema": tool.inputSchema,
                    }
                )
        return anthropic_tools

    def resolve_server(self, tool_name: str) -> tuple[str, str]:
        """Resolve a tool name to (server_name, original_tool_name)."""
        if "__" in tool_name:
            server_name, original = tool_name.split("__", 1)
            if server_name in self.servers:
                return server_name, original

        server_name = self._tool_registry.get(tool_name)
        if server_name:
            return server_name, tool_name

        raise ValueError(f"Unknown tool: {tool_name}")

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Route a tool call to the appropriate MCP server with tracing."""
        server_name, original_name = self.resolve_server(tool_name)
        server = self.servers[server_name]

        with self.tracer.timed_tool_call(server_name, original_name, arguments):
            result = await server.session.call_tool(original_name, arguments=arguments)

        text_parts = []
        for block in result.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)
            else:
                text_parts.append(str(block))

        return "\n".join(text_parts) if text_parts else "(empty result)"

    def list_tools_summary(self) -> str:
        """Return a human-readable summary of all available tools."""
        lines = ["Available MCP Tools:", ""]
        for server_name, server in self.servers.items():
            lines.append(f"## {server_name}")
            if server.description:
                lines.append(f"   {server.description}")
            for tool in server.tools:
                desc = f" — {tool.description}" if tool.description else ""
                lines.append(f"  - {server_name}__{tool.name}{desc}")
            lines.append("")
        return "\n".join(lines)
