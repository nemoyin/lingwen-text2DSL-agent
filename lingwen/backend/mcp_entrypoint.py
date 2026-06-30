#!/usr/bin/env python
"""Lingwen MCP Server — stdio mode entry point.

Usage:
    LINGWEN_JWT_TOKEN=eyJ... python mcp_entrypoint.py

Configure in Claude Desktop / Claude Code / Cursor:
    {
      "mcpServers": {
        "lingwen": {
          "command": "python",
          "args": ["path/to/mcp_entrypoint.py"],
          "env": {
            "LINGWEN_JWT_TOKEN": "your-jwt-token"
          }
        }
      }
    }
"""
import asyncio
import logging
import sys
import os

# Ensure the backend package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.mcp_server.server import run_stdio_server

logging.basicConfig(
    level=logging.WARNING,  # keep stderr clean for MCP protocol
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)

if __name__ == "__main__":
    asyncio.run(run_stdio_server())
