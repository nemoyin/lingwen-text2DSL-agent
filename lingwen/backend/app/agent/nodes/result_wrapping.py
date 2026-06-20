"""Result wrapping node — generates natural-language analysis and chart suggestions."""

import json
import logging
import time
from typing import Dict

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import AgentState

logger = logging.getLogger(__name__)


def _summarize_data(rows: list[dict], max_sample: int = 5) -> str:
    """Create a compact text summary of query results for the LLM."""
    if not rows:
        return "查询结果为空（0 行）。"

    total_rows = len(rows)
    sample = rows[:max_sample]

    # Column names
    columns = list(sample[0].keys()) if sample else []

    lines = [f"查询共返回 {total_rows} 行，以下为前 {len(sample)} 行示例："]
    lines.append(" | ".join(columns))
    lines.append("-" * 40)
    for row in sample:
        values = [str(row.get(c, "")) for c in columns]
        lines.append(" | ".join(values))

    return "\n".join(lines)


class ResultWrappingNode:
    """Wraps query results into a human-readable analysis using the LLM.

    For successful queries, the LLM is asked to:
        1. Summarise the data in natural language.
        2. Suggest an appropriate chart type (bar / line / pie / table / none).

    For failed or auth-failed queries, the error is surfaced directly.
    """

    def __init__(self, llm) -> None:
        """Args:
            llm: A ``ChatDeepSeek`` (or compatible) chat model instance.
        """
        self._llm = llm

    async def __call__(self, state: AgentState) -> Dict:
        """Generate narrative analysis and chart suggestions.

        Args:
            state: Agent state with ``execution_result``, ``status``,
                ``error_info``, ``question``, ``generated_sql``.

        Returns:
            Partial state with ``ai_analysis`` and ``chart_suggestion``.
        """
        status: str = state.get("status", "failed")
        error_info: str | None = state.get("error_info")

        # ---- Failure / auth-failed path ----
        if status in ("failed", "auth_failed"):
            msg = error_info or "查询执行失败"
            logger.warning("[Pipeline|结果分析] 跳过(pipeline失败), status=%s error=%s", status, msg[:80])
            return {
                "ai_analysis": f"查询失败：{msg}",
                "chart_suggestion": None,
                "status": status,
            }

        # ---- Success path ----
        rows: list[dict] = state.get("execution_result", [])
        question: str = state.get("question", "")
        sql: str = state.get("generated_sql", "")
        t0 = time.time()

        logger.info("[Pipeline|结果分析] 开始, rows=%d question=%s", len(rows), question[:40])

        data_summary = _summarize_data(rows)

        prompt = (
            f"用户问题：{question}\n\n"
            f"执行的 SQL：{sql}\n\n"
            f"查询结果：\n{data_summary}\n\n"
            "请根据查询结果，用简洁的自然语言（中文）总结数据发现。\n"
            "然后推荐一个最合适的图表类型。\n"
            "最后，根据当前问题和分析结果，生成 3 个相关的后续问题，帮助用户深入探索数据。\n\n"
            "请按以下 JSON 格式输出（不要输出其他内容）：\n"
            '{{"analysis": "你的分析文本", "chart_type": "bar|line|pie|table|none", '
            '"chart_title": "图表标题", "suggested_questions": ["问题1", "问题2", "问题3"]}}'
        )

        messages = [
            SystemMessage(content=(
                "你是一个数据分析师，擅长用简洁的语言解读数据查询结果，并推荐合适的可视化方式。"
                "请严格按照要求的 JSON 格式输出。"
            )),
            HumanMessage(content=prompt),
        ]

        try:
            response = await self._llm.ainvoke(messages)
            raw_text: str = response.content if hasattr(response, "content") else str(response)
            elapsed = round((time.time() - t0) * 1000)

            # Extract native reasoning_content for streaming display
            native_reasoning = ""
            if hasattr(response, "additional_kwargs"):
                native_reasoning = response.additional_kwargs.get("reasoning_content", "") or ""
            if not native_reasoning and hasattr(response, "response_metadata"):
                native_reasoning = str(response.response_metadata.get("reasoning_content", ""))
            logger.debug("Result wrap native reasoning: %d chars", len(native_reasoning))
            logger.debug("Result wrapping LLM response: %s", raw_text[:500])

            # Try to parse JSON from response
            parsed = self._parse_json_response(raw_text)
            analysis = parsed.get("analysis", "查询成功，共返回数据。")
            chart_type = parsed.get("chart_type", "table")
            chart_title = parsed.get("chart_title", "查询结果")
            suggested_questions = parsed.get("suggested_questions", [])

            chart_suggestion = {
                "type": chart_type,
                "title": chart_title,
            } if chart_type != "none" else None

            logger.info("[Pipeline|结果分析] 完成, chart=%s analysis=%dchars suggested=%d elapsed=%dms",
                        chart_type, len(analysis), len(suggested_questions), elapsed)

            return {
                "ai_analysis": analysis,
                "chart_suggestion": chart_suggestion,
                "suggested_questions": suggested_questions[:3],
                "native_reasoning": native_reasoning,
            }
        except Exception as exc:
            elapsed = round((time.time() - t0) * 1000)
            logger.error("[Pipeline|结果分析] LLM调用失败, error=%s elapsed=%dms", exc, elapsed)
            row_count = len(rows)
            return {
                "ai_analysis": f"查询成功，共返回 {row_count} 行数据。",
                "chart_suggestion": {"type": "table", "title": "查询结果"},
            }

    @staticmethod
    def _parse_json_response(text: str) -> Dict:
        """Extract JSON from LLM response, with markdown fence handling."""
        # Strip markdown code fences
        cleaned = text.strip()
        if cleaned.startswith("```"):
            # Remove ```json or ``` and trailing ```
            cleaned = cleaned.split("\n", 1)[-1] if "\n" in cleaned else cleaned
            cleaned = cleaned.rsplit("```", 1)[0] if cleaned.endswith("```") else cleaned

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Try regex extraction as fallback
            import re
            analysis_match = re.search(r'"analysis"\s*:\s*"([^"]*)"', text)
            chart_match = re.search(r'"chart_type"\s*:\s*"([^"]*)"', text)
            title_match = re.search(r'"chart_title"\s*:\s*"([^"]*)"', text)

            return {
                "analysis": analysis_match.group(1) if analysis_match else "查询成功。",
                "chart_type": chart_match.group(1) if chart_match else "table",
                "chart_title": title_match.group(1) if title_match else "查询结果",
            }
