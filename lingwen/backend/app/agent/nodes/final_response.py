"""Final response node — assembles the structured query result dict."""

import logging
from typing import Any, Dict

from app.agent.state import AgentState

logger = logging.getLogger(__name__)


def _estimate_tokens(state: dict) -> int:
    """Rough token estimate based on total text output length (chars / 2)."""
    total_chars = 0
    for key in ("generated_sql", "ai_analysis", "cot_reasoning"):
        val = state.get(key, "")
        if val:
            total_chars += len(str(val))
    # Avg 2 chars per token for Chinese text
    return max(total_chars // 2, 100)


class FinalResponseNode:
    """Assembles the final response dictionary returned to the API caller.

    This is the terminal node in the StateGraph — it does not modify the
    state but produces a standalone result dict that the ``QueryAgent.run()``
    method returns to the caller.
    """

    async def __call__(self, state: AgentState) -> Dict[str, Any]:
        """Build the final structured response.

        Args:
            state: The complete agent state after all pipeline stages.

        Returns:
            A dict suitable for the ``/api/query`` response, with keys:
            ``question``, ``data``, ``columns``, ``analysis``, ``sql``,
            ``chart_suggestion``, ``row_count``, ``is_truncated``.
        """
        execution_result: list[dict] = state.get("execution_result", [])
        status: str = state.get("status", "failed")

        # Infer column names from the first row
        columns: list[str] = []
        if execution_result and len(execution_result) > 0:
            columns = list(execution_result[0].keys())

        row_count = len(execution_result)
        is_truncated = row_count >= 1000
        sql_len = len(state.get("generated_sql", ""))
        question = state.get("question", "")

        logger.info(
            "[Pipeline|响应组装] status=%s rows=%d columns=%d sql=%dchars truncated=%s question=%s",
            status, row_count, len(columns), sql_len, is_truncated, question[:40],
        )

        result: Dict[str, Any] = {
            "question": question,
            "data": execution_result,
            "columns": columns,
            "analysis": state.get("ai_analysis", ""),
            "sql": state.get("generated_sql", ""),
            "chart_suggestion": state.get("chart_suggestion"),
            "row_count": row_count,
            "is_truncated": is_truncated,
            "pipeline_steps": state.get("pipeline_steps", []),
            "suggested_questions": state.get("suggested_questions", []),
            "total_tokens": state.get("total_tokens", _estimate_tokens(state)),
        }

        logger.info(
            "[Pipeline|响应组装] 完成, total_keys=%d analysis=%dchars suggested=%d",
            len(result), len(result.get("analysis", "")), len(result.get("suggested_questions", [])),
        )

        return {"final_result": result}
