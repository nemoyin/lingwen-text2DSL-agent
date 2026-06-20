"""RAG retrieval node — parallel schema + few-shot semantic search."""

import asyncio
import logging
import time
from typing import Dict

from app.agent.state import AgentState
from app.rag.retriever import SchemaRetriever, FewShotRetriever

logger = logging.getLogger(__name__)


class RAGRetrievalNode:
    """Runs schema and few-shot retrieval in parallel via ``asyncio.gather``.

    Requires two retriever instances injected at construction time.
    """

    def __init__(
        self,
        schema_retriever: SchemaRetriever,
        fewshot_retriever: FewShotRetriever,
    ) -> None:
        self._schema_retriever = schema_retriever
        self._fewshot_retriever = fewshot_retriever

    async def __call__(self, state: AgentState) -> Dict:
        """Execute parallel RAG retrieval.

        Args:
            state: The current agent state with ``question`` and ``datasource_id``.

        Returns:
            Partial state with ``retrieved_schemas`` and ``retrieved_examples``.
        """
        question: str = state["question"]
        ds_id: int = state["datasource_id"]
        t0 = time.time()

        logger.info("[Pipeline|RAG检索] 开始, ds_id=%d question=%s", ds_id, question[:60])

        try:
            schemas, examples = await asyncio.gather(
                self._schema_retriever.retrieve(question, ds_id, top_k=5),
                self._fewshot_retriever.retrieve(question, ds_id, top_k=3),
            )
            elapsed = round((time.time() - t0) * 1000)
            logger.info(
                "[Pipeline|RAG检索] 完成, schemas=%d examples=%d elapsed=%dms",
                len(schemas), len(examples), elapsed,
            )
        except Exception as exc:
            elapsed = round((time.time() - t0) * 1000)
            logger.warning("[Pipeline|RAG检索] 失败(将使用元数据回退), error=%s elapsed=%dms", exc, elapsed)
            schemas, examples = [], []

        return {
            "retrieved_schemas": schemas,
            "retrieved_examples": examples,
        }
