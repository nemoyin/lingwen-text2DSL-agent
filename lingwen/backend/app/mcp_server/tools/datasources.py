"""lingwen_list_datasources — Discover available data sources (MCP Tool)."""
import logging
from typing import Any

from mcp.types import Tool, TextContent

logger = logging.getLogger(__name__)


def _build_datasources_tool() -> Tool:
    return Tool(
        name="lingwen_list_datasources",
        description="""列出 Lingwen 中所有可用的数据源及其基本信息。

返回数据源 ID、名称、数据库类型、状态等，便于后续使用 lingwen_query 时指定 datasource_id。
""",
        inputSchema={
            "type": "object",
            "properties": {},
        },
    )


async def _call_datasources(user_id: int) -> list[TextContent]:
    """List all datasources visible to the given user."""
    from app.models.database import async_session
    from app.services.datasource_service import get_all

    async with async_session() as db:
        rows = await get_all(db)

    if not rows:
        return [TextContent(type="text", text="⚠️ 没有配置任何数据源。请在 Lingwen 管理后台添加数据源。")]

    lines = ["## 可用数据源", ""]
    lines.append("| ID | 名称 | 类型 | 状态 | 主机 | 数据库 |")
    lines.append("| --- | --- | --- | --- | --- | --- |")

    for r in rows:
        name = getattr(r, "name", "")
        db_type = getattr(r, "db_type", "")
        status = getattr(r, "status", "")
        host = getattr(r, "host", "")
        database = getattr(r, "database", "")
        rid = getattr(r, "id", "")
        status_icon = "✅" if status == "active" else "⏸️"
        lines.append(f"| {rid} | {name} | {db_type} | {status_icon} {status} | {host} | {database} |")

    lines.append("")
    lines.append(f"共 {len(rows)} 个数据源。使用 `lingwen_query` 时可通过 `datasource_id` 指定目标。")

    return [TextContent(type="text", text="\n".join(lines))]


# ── public API ──────────────────────────────────────────────

def get_datasources_tool_definition() -> Tool:
    return _build_datasources_tool()


async def handle_datasources_tool(user_id: int) -> list[TextContent]:
    return await _call_datasources(user_id)
