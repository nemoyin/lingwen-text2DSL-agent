"""Schema and few-shot retrievers with datasource filtering."""

import logging
from typing import List, Dict

from app.rag.embeddings import EmbeddingClient
from app.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)

# Last known embedding dimension (updated on first successful query)
_embed_dim: int | None = None


def _check_dimension(query_dim: int, source: str) -> bool:
    """Validate query embedding dimension against stored vectors.

    Returns True if valid (or if no prior dim known).  Logs a warning
    if a mismatch is detected.

    Args:
        query_dim: Dimension of the new query embedding.
        source: Label for log messages (e.g. "SchemaRetriever").
    """
    global _embed_dim
    if _embed_dim is None:
        _embed_dim = query_dim
        return True
    if _embed_dim != query_dim:
        logger.warning(
            "[%s] Embedding dimension mismatch: query=%d vs stored=%d. "
            "This usually means the embedding model was changed. "
            "Run POST /api/rag/reindex to rebuild all vectors.",
            source, query_dim, _embed_dim,
        )
        return False
    return True


class SchemaRetriever:
    """Retrieve relevant table/column schemas for a given natural-language question.

    Uses embedding-based semantic search, then filters results by data source.
    """

    def __init__(self, embedding_client: EmbeddingClient, vector_store: VectorStore) -> None:
        self._embed = embedding_client
        self._store = vector_store

    async def retrieve(
        self,
        question: str,
        datasource_id: int,
        top_k: int = 5,
    ) -> List[Dict]:
        """Search for schema documents relevant to the question.

        Strategy:
            1. Embed the question.
            2. Query schema collection with ``top_k * 2`` candidates.
            3. Filter to retain only results matching ``datasource_id``.
            4. Return the top ``top_k`` after filtering.

        Args:
            question: The user's natural-language question.
            datasource_id: The data source to filter by.
            top_k: Maximum number of results to return.

        Returns:
            A list of dicts, each with ``id``, ``content``, ``metadata``, ``distance``.
        """
        try:
            query_embedding = await self._embed.embed_text(question)
            # Validate dimension compatibility
            if not _check_dimension(len(query_embedding), "SchemaRetriever"):
                return []
            candidates = self._store.search_schemas(query_embedding, top_k=top_k * 2)
        except Exception as exc:
            logger.warning("Schema embedding failed (will skip RAG): %s", exc)
            return []

        # Filter by datasource_id (metadata stored as string)
        filtered = [
            c for c in candidates
            if str(c.get("metadata", {}).get("datasource_id", "")) == str(datasource_id)
        ]

        results = filtered[:top_k]
        logger.debug(
            "SchemaRetriever: %d candidates → %d after filter → %d returned",
            len(candidates), len(filtered), len(results),
        )
        return results


class FewShotRetriever:
    """Retrieve relevant few-shot examples (question→SQL pairs) for a given question.

    Uses embedding-based semantic search with data source filtering.
    """

    def __init__(self, embedding_client: EmbeddingClient, vector_store: VectorStore) -> None:
        self._embed = embedding_client
        self._store = vector_store

    async def retrieve(
        self,
        question: str,
        datasource_id: int,
        top_k: int = 3,
    ) -> List[Dict]:
        """Search for few-shot examples relevant to the question.

        Strategy:
            1. Embed the question.
            2. Query few-shot collection with ``top_k * 2`` candidates.
            3. Filter to retain only results matching ``datasource_id``.
            4. Return the top ``top_k`` after filtering.

        Args:
            question: The user's natural-language question.
            datasource_id: The data source to filter by.
            top_k: Maximum number of results to return.

        Returns:
            A list of dicts, each with ``id``, ``content``, ``metadata``, ``distance``.
        """
        try:
            query_embedding = await self._embed.embed_text(question)
            # Validate dimension compatibility
            if not _check_dimension(len(query_embedding), "FewShotRetriever"):
                return []
            candidates = self._store.search_fewshots(query_embedding, top_k=top_k * 2)
        except Exception as exc:
            logger.warning("FewShot embedding failed (will skip RAG): %s", exc)
            return []

        # Filter by datasource_id (metadata stored as string)
        filtered = [
            c for c in candidates
            if str(c.get("metadata", {}).get("datasource_id", "")) == str(datasource_id)
        ]

        results = filtered[:top_k]
        logger.debug(
            "FewShotRetriever: %d candidates → %d after filter → %d returned",
            len(candidates), len(filtered), len(results),
        )
        return results
