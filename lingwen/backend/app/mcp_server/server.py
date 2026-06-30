"""Lingwen MCP Server — register tools, handle calls, manage lifecycle."""
import logging
import os
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .auth import MCPAuth
from .tools.query import get_query_tool_definition, handle_query_tool
from .tools.datasources import get_datasources_tool_definition, handle_datasources_tool

logger = logging.getLogger(__name__)

# ── Tool registry ────────────────────────────────────────────

_TOOLS: list[tuple[Tool, str]] = [
    (get_query_tool_definition(), "lingwen_query"),
    (get_datasources_tool_definition(), "lingwen_list_datasources"),
]

_HANDLERS: dict[str, Any] = {
    "lingwen_query": handle_query_tool,
    "lingwen_list_datasources": handle_datasources_tool,
}


# ── Server factory ───────────────────────────────────────────

def create_lingwen_mcp_server(token: str | None = None) -> Server:
    """Create a configured Lingwen MCP Server instance.

    Args:
        token: JWT token for authentication. If None, read from
               LINGWEN_JWT_TOKEN env var.
    """
    auth = MCPAuth()
    server = Server("lingwen-mcp")

    # Resolve token once at startup
    _token = token or os.getenv("LINGWEN_JWT_TOKEN")
    if _token:
        try:
            auth.authenticate(_token)
            logger.info("MCP Server authenticated")
        except ValueError as e:
            logger.warning("MCP Server auth failed at startup: %s — tools will require valid token", e)

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [t for t, _ in _TOOLS]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        handler = _HANDLERS.get(name)
        if handler is None:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        # Authenticate
        try:
            user = auth.authenticate(_token)
            user_id = user.get("user_id") or user.get("sub")
            if user_id is None:
                return [TextContent(type="text", text="❌ 认证失败：token 中缺少用户标识")]
        except ValueError as e:
            return [TextContent(type="text", text=f"❌ 认证失败：{e}")]

        # Dispatch
        try:
            if name == "lingwen_list_datasources":
                return await handler(user_id)
            return await handler(user_id, arguments)
        except ValueError as e:
            return [TextContent(type="text", text=f"❌ {e}")]
        except Exception:
            logger.exception("Tool '%s' failed", name)
            return [TextContent(type="text", text=f"❌ 查询执行失败，请检查 Lingwen 服务状态后重试")]

    return server


# ── stdio entry point ────────────────────────────────────────

async def run_stdio_server():
    """Run the MCP server over stdio transport (for local IDE use)."""
    server = create_lingwen_mcp_server()
    async with stdio_server() as (read_stream, write_stream):
        logger.info("Lingwen MCP Server starting (stdio mode)...")
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )
