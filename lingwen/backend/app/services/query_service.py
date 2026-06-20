"""Query execution service — orchestrates the QueryAgent pipeline."""

import logging
import time
from typing import Any, Dict, List

from app.agent.graph import QueryAgent

logger = logging.getLogger(__name__)


class QueryService:
    """Runs the full Text2SQL pipeline and returns a clean response dict.

    Usage::

        service = QueryService(agent)
        result = await service.execute(
            question="销售额最高的10个产品？",
            datasource_id=1,
            user_id=1,
        )
    """

    def __init__(self, agent: QueryAgent) -> None:
        """Args:
            agent: A compiled :class:`QueryAgent` instance.
        """
        self._agent: QueryAgent = agent

    async def execute(
        self,
        question: str,
        datasource_id: int,
        user_id: int,
        history: List[dict] | None = None,
        max_context_turns: int = 6,
    ) -> Dict[str, Any]:
        """Execute a natural-language query through the Agent pipeline.

        Args:
            question: The user's natural-language question.
            datasource_id: The target data source ID.
            user_id: The authenticated user ID.
            history: Optional multi-turn conversation history (list of
                ``{"question": ..., "answer": ...}`` dicts).
            max_context_turns: Maximum conversation turns to include (default 6).

        Returns:
            A dict with ``question``, ``data``, ``columns``, ``analysis``,
            ``sql``, ``chart_suggestion``, ``row_count``, ``is_truncated``,
            ``latency_ms``, and ``suggested_questions``.
        """
        start: float = time.time()

        logger.info(
            "QueryService.execute: ds=%d user=%d question=%s history=%d turns",
            datasource_id, user_id, question[:80], len(history or []),
        )

        result = await self._agent.run(
            question, datasource_id, user_id,
            history=history, max_context_turns=max_context_turns,
        )
        latency_ms: float = round((time.time() - start) * 1000, 2)

        # Extract from the Agent's final_result if available,
        # otherwise use the raw result dict.
        final: Dict[str, Any] = (
            result.get("final_result", {}) if isinstance(result, dict) else {}
        )
        if not final:
            final = result if isinstance(result, dict) else {}

        return {
            "question": question,
            "data": final.get("data", []),
            "columns": final.get("columns", []),
            "analysis": final.get("analysis", ""),
            "sql": final.get("sql", ""),
            "chart_suggestion": final.get("chart_suggestion"),
            "row_count": final.get("row_count", 0),
            "is_truncated": final.get("is_truncated", False),
            "latency_ms": latency_ms,
            "pipeline_steps": result.get("pipeline_steps", []) if isinstance(result, dict) else [],
            "suggested_questions": final.get("suggested_questions", []),
            "total_tokens": final.get("total_tokens", 0),
        }
