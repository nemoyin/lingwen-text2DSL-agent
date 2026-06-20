"""ChromaDB vector store wrapper for schema and few-shot embeddings."""

import logging
from typing import Dict, List, Optional

import chromadb
from chromadb.api.types import EmbeddingFunction, Embeddings, Documents

from app.config import settings

logger = logging.getLogger(__name__)


class _SimpleEmbeddingFunction(EmbeddingFunction):
    """Minimal embedding-function stub used only for ChromaDB metadata.

    Actual embeddings are computed by :class:`EmbeddingClient` and passed
    to ``add()`` directly, so this class is never called at runtime.
    """

    def __call__(self, input: Documents) -> Embeddings:
        raise NotImplementedError("Direct embedding injection is used — this should never be called")


class VectorStore:
    """Manages two ChromaDB collections: schema_embeddings and fewshot_embeddings.

    Usage::

        vs = VectorStore()
        await vs.add_schemas([...])
        results = vs.search_schemas("query text", top_k=5)
    """

    SCHEMA_COLLECTION = "schema_embeddings"
    FEWSHOT_COLLECTION = "fewshot_embeddings"

    def __init__(self) -> None:
        self._client: chromadb.PersistentClient = chromadb.PersistentClient(
            path=settings.chroma_dir,
            settings=chromadb.Settings(anonymized_telemetry=False),
        )
        self._ef: _SimpleEmbeddingFunction = _SimpleEmbeddingFunction()

        # Lazy — collections created on first access
        self._schema_col: Optional[chromadb.Collection] = None
        self._fewshot_col: Optional[chromadb.Collection] = None

    # ------------------------------------------------------------------
    # Collection accessors
    # ------------------------------------------------------------------

    @property
    def schema_col(self) -> chromadb.Collection:
        """Return (or create) the schema embeddings collection."""
        if self._schema_col is None:
            self._schema_col = self._client.get_or_create_collection(
                name=self.SCHEMA_COLLECTION,
                embedding_function=self._ef,
                metadata={"hnsw:space": "cosine"},
            )
            logger.debug("Schema collection ready: %d docs", self._schema_col.count())
        return self._schema_col

    @property
    def fewshot_col(self) -> chromadb.Collection:
        """Return (or create) the few-shot embeddings collection."""
        if self._fewshot_col is None:
            self._fewshot_col = self._client.get_or_create_collection(
                name=self.FEWSHOT_COLLECTION,
                embedding_function=self._ef,
                metadata={"hnsw:space": "cosine"},
            )
            logger.debug("FewShot collection ready: %d docs", self._fewshot_col.count())
        return self._fewshot_col

    # ------------------------------------------------------------------
    # Add / upsert
    # ------------------------------------------------------------------

    def _normalize_metadata(self, meta: Dict) -> Dict:
        """Convert all metadata values to ChromaDB-compatible primitives."""
        result: Dict = {}
        for k, v in meta.items():
            if v is None:
                result[k] = ""
            elif isinstance(v, (str, int, float, bool)):
                result[k] = v
            else:
                result[k] = str(v)
        return result

    def add_schemas(
        self,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict],
    ) -> None:
        """Insert or update schema documents in the vector store.

        Args:
            ids: Unique IDs (e.g. ``schema_1_users``).
            documents: Text representations of tables/columns.
            embeddings: Pre-computed embeddings (same order as documents).
            metadatas: Metadata dicts keyed by ``datasource_id``, ``table_name``, etc.
        """
        if not ids:
            return
        clean_meta = [self._normalize_metadata(m) for m in metadatas]
        self.schema_col.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=clean_meta,
        )
        logger.info("Schema collection: upserted %d documents", len(ids))

    def add_fewshots(
        self,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict],
    ) -> None:
        """Insert or update few-shot examples in the vector store.

        Args:
            ids: Unique IDs (e.g. ``fewshot_42``).
            documents: ``"问题: ...\nSQL: ..."`` strings.
            embeddings: Pre-computed embeddings.
            metadatas: Metadata dicts keyed by ``datasource_id``, ``question``, ``sql``, etc.
        """
        if not ids:
            return
        clean_meta = [self._normalize_metadata(m) for m in metadatas]
        self.fewshot_col.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=clean_meta,
        )
        logger.info("FewShot collection: upserted %d documents", len(ids))

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_schemas(
        self,
        query_embedding: List[float],
        top_k: int = 5,
    ) -> List[Dict]:
        """Search schema embeddings by cosine similarity.

        Args:
            query_embedding: The embedding of the user's question.
            top_k: Maximum number of results to return.

        Returns:
            A list of dicts with keys ``id``, ``content``, ``metadata``, ``distance``.
        """
        result = self.schema_col.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )
        return self._format_results(result)

    def search_fewshots(
        self,
        query_embedding: List[float],
        top_k: int = 3,
    ) -> List[Dict]:
        """Search few-shot embeddings by cosine similarity.

        Args:
            query_embedding: The embedding of the user's question.
            top_k: Maximum number of results to return.

        Returns:
            A list of dicts with keys ``id``, ``content``, ``metadata``, ``distance``.
        """
        result = self.fewshot_col.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )
        return self._format_results(result)

    def _format_results(self, result: Dict) -> List[Dict]:
        """Convert ChromaDB query result to a list of clean dicts.

        ChromaDB 0.5.x returns::

            {"ids": [[...]], "documents": [[...]], "metadatas": [[...]], "distances": [[...]]}

        """
        ids: List[List[str]] = result.get("ids", [[]])
        docs: List[List[str]] = result.get("documents", [[]])
        metas: List[List[Dict]] = result.get("metadatas", [[]])
        dists: List[List[float]] = result.get("distances", [[]])

        output: List[Dict] = []
        if not ids or not ids[0]:
            return output

        for i in range(len(ids[0])):
            output.append({
                "id": ids[0][i] if i < len(ids[0]) else "",
                "content": docs[0][i] if i < len(docs[0]) else "",
                "metadata": metas[0][i] if i < len(metas[0]) else {},
                "distance": dists[0][i] if i < len(dists[0]) else 1.0,
            })
        return output

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def count_schemas(self) -> int:
        """Return the number of documents in the schema collection."""
        return self.schema_col.count()

    def count_fewshots(self) -> int:
        """Return the number of documents in the few-shot collection."""
        return self.fewshot_col.count()

    def delete_by_datasource(self, datasource_id: int) -> None:
        """Remove all schema and few-shot entries for a given data source.

        Args:
            datasource_id: The data source whose entries should be purged.
        """
        # Delete from schema collection by metadata filter
        try:
            schema_docs = self.schema_col.get(
                where={"datasource_id": str(datasource_id)}
            )
            if schema_docs and schema_docs.get("ids"):
                self.schema_col.delete(ids=schema_docs["ids"])
                logger.info(
                    "Deleted %d schema docs for datasource %d",
                    len(schema_docs["ids"]),
                    datasource_id,
                )
        except Exception as exc:
            logger.warning("Schema delete for ds %d failed (may be empty): %s", datasource_id, exc)

        # Delete from fewshot collection
        try:
            fw_docs = self.fewshot_col.get(
                where={"datasource_id": str(datasource_id)}
            )
            if fw_docs and fw_docs.get("ids"):
                self.fewshot_col.delete(ids=fw_docs["ids"])
                logger.info(
                    "Deleted %d fewshot docs for datasource %d",
                    len(fw_docs["ids"]),
                    datasource_id,
                )
        except Exception as exc:
            logger.warning("FewShot delete for ds %d failed (may be empty): %s", datasource_id, exc)
