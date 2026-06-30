"""MCP SSE transport — exposes Lingwen MCP Server for remote clients.

Provides two endpoints:
  GET  /api/mcp/sse       — establish SSE stream
  POST /api/mcp/messages  — receive client messages
"""
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/sse")
async def mcp_sse_endpoint(request: Request):
    """Establish MCP SSE connection.

    The client opens this endpoint to receive server-initiated messages.
    """
    try:
        from mcp.server.sse import SseServerTransport
        from app.mcp_server.server import create_lingwen_mcp_server
    except ImportError:
        return JSONResponse({"detail": "MCP not available"}, status_code=501)

    server = create_lingwen_mcp_server()
    sse = SseServerTransport("/api/mcp/messages")

    async with sse.connect_sse(
        request.scope, request.receive, request._send  # type: ignore[arg-type]
    ) as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


@router.post("/messages")
async def mcp_messages_endpoint(request: Request):
    """Receive MCP client messages over POST."""
    try:
        from mcp.server.sse import SseServerTransport
    except ImportError:
        return JSONResponse({"detail": "MCP not available"}, status_code=501)

    sse = SseServerTransport("/api/mcp/messages")

    await sse.handle_post_message(
        request.scope, request.receive, request._send  # type: ignore[arg-type]
    )
