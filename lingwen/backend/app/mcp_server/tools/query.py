"""lingwen_query — Natural language to SQL query (core MCP Tool)."""
import logging
import os
from typing import Any

from mcp.types import Tool, TextContent

logger = logging.getLogger(__name__)


def _build_query_tool() -> Tool:
    return Tool(
        name="lingwen_query",
        description="""使用自然语言查询数据库。支持 MySQL、PostgreSQL、ClickHouse、Oracle、Doris、Hive、ES、达梦 DM8。

输入中文问题，返回数据表格、AI 文字分析、以及生成的 SQL。

示例:
- "本月各部门销售额排行"
- "近30天预警数量趋势"
- "三公经费实际支出与预算对比"

支持多轮对话：传入 history 参数可进行追问和澄清。
""",
        inputSchema={
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "自然语言数据查询问题",
                },
                "datasource_id": {
                    "type": "integer",
                    "description": "数据源 ID（可选，不传则使用第一个活跃数据源）",
                },
                "history": {
                    "type": "array",
                    "description": "多轮对话历史 [{\"question\": \"...\", \"answer\": \"...\"}]（可选）",
                    "items": {"type": "object"},
                },
            },
            "required": ["question"],
        },
    )


async def _call_query(
    user_id: int,
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Execute a natural language query and return formatted results."""
    question = arguments["question"]
    datasource_id = arguments.get("datasource_id")
    history = arguments.get("history")

    # Resolve datasource_id if not provided
    if datasource_id is None:
        datasource_id = await _resolve_default_datasource()

    # Run the full Agent pipeline
    from app.models.database import async_session
    from app.services.query_service import QueryService
    from app.api.deps import get_agent

    agent = await get_agent()
    query_service = QueryService(agent)
    result = await query_service.execute(
        question=question,
        datasource_id=datasource_id,
        user_id=user_id,
        history=history,
    )

    # Format result as readable text
    columns = result.get("columns", [])
    data = result.get("data", [])
    analysis = result.get("analysis", "")
    sql = result.get("sql", "")
    row_count = result.get("row_count", 0)
    is_truncated = result.get("is_truncated", False)
    latency_ms = result.get("latency_ms", 0)
    suggested = result.get("suggested_questions", [])

    lines = [
        f"## {question}",
        "",
        f"### SQL ({latency_ms:.0f}ms)",
        f"```sql\n{sql}\n```",
        "",
        f"### 结果 ({row_count} 行{'，已截断' if is_truncated else ''})",
        "",
    ]

    # Render table
    if columns and data:
        lines.append(_format_table(columns, data))
        lines.append("")

    if analysis:
        lines.append("### AI 分析")
        lines.append(analysis)
        lines.append("")

    if suggested:
        lines.append("### 追问建议")
        for q in suggested[:3]:
            lines.append(f"- {q}")

    return [TextContent(type="text", text="\n".join(lines))]


async def _resolve_default_datasource() -> int:
    """Pick the first active datasource when none is specified."""
    from app.models.database import async_session
    from app.services.datasource_service import get_all

    async with async_session() as db:
        rows = await get_all(db)
        active = [r for r in rows if getattr(r, "status", "") == "active"]
        if active:
            return active[0].id
        if rows:
            return rows[0].id
        raise ValueError("没有可用的数据源，请先在 Lingwen 管理后台配置数据源")


def _format_table(columns: list[str], data: list[dict]) -> str:
    """Render data as a markdown table."""
    if not data:
        return "(无数据)"

    # Header
    header = "| " + " | ".join(str(c) for c in columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"

    # Rows (limit to 20 for readability in MCP responses)
    rows = []
    for row in data[:20]:
        vals = [str(row.get(c, "")) if row.get(c) is not None else "" for c in columns]
        rows.append("| " + " | ".join(vals) + " |")

    if len(data) > 20:
        rows.append(f"| ... | *（共 {len(data)} 行，仅显示前 20 行）* |")

    return "\n".join([header, sep] + rows)


# ── public API ──────────────────────────────────────────────

def get_query_tool_definition() -> Tool:
    return _build_query_tool()


async def handle_query_tool(
    user_id: int,
    arguments: dict[str, Any],
) -> list[TextContent]:
    return await _call_query(user_id, arguments)
