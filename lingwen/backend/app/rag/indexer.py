"""Indexer — builds vector-store documents from table/column metadata and few-shot examples."""

import logging
from typing import List, Dict

from app.rag.embeddings import EmbeddingClient
from app.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


class Indexer:
    """Indexes schema metadata and few-shot examples into ChromaDB.

    Usage::

        indexer = Indexer(embedding_client, vector_store)
        await indexer.index_schemas(datasource_id, tables, columns_by_table)
        await indexer.index_fewshot(example)
    """

    def __init__(
        self,
        embedding_client: EmbeddingClient,
        vector_store: VectorStore,
    ) -> None:
        self._embed = embedding_client
        self._store = vector_store

    # ------------------------------------------------------------------
    # Schema indexing
    # ------------------------------------------------------------------

    async def index_schemas(
        self,
        datasource_id: int,
        tables: list,
        columns_by_table: Dict[str, list],
    ) -> int:
        """Build and index schema documents for all tables of a data source.

        Args:
            datasource_id: The data source ID.
            tables: List of ``TableMetadata`` ORM objects.
            columns_by_table: Dict mapping ``table_name`` → list of
                ``ColumnMetadata`` ORM objects.

        Returns:
            The number of documents indexed.
        """
        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict] = []

        for table in tables:
            tname: str = table.table_name
            display: str = table.display_name or tname
            desc: str = table.business_description or "暂无描述"

            # Collect column info
            cols = columns_by_table.get(tname, [])
            col_parts: List[str] = []
            for col in cols:
                cname = col.column_name
                ctype = col.data_type
                cdesc = col.business_description or ""
                pk_mark = " [主键]" if col.is_primary_key else ""
                col_parts.append(f"{cname}({ctype}){pk_mark} 含义:{cdesc or '暂无'}")

            col_text = "；".join(col_parts) if col_parts else "暂无字段信息"
            doc = f"表 {tname}({display}): {desc}。字段: {col_text}"

            doc_id = f"schema_{datasource_id}_{tname}"

            ids.append(doc_id)
            documents.append(doc)
            metadatas.append({
                "datasource_id": str(datasource_id),
                "table_name": tname,
                "display_name": display,
                "type": "schema",
            })

        # Embed all documents in a single batch
        if documents:
            embeddings = await self._embed.embed_documents(documents)
            self._store.add_schemas(ids, documents, embeddings, metadatas)
            logger.info(
                "Indexed %d schema documents for datasource %d",
                len(documents), datasource_id,
            )

        return len(documents)

    # ------------------------------------------------------------------
    # Few-shot indexing
    # ------------------------------------------------------------------

    async def index_fewshot(self, example) -> None:
        """Index a single few-shot example.

        Args:
            example: A ``FewShotExample`` ORM object with fields:
                ``id``, ``datasource_id``, ``question``, ``sql``,
                ``description``, ``tags``.
        """
        doc_id = f"fewshot_{example.id}"
        doc = f"问题: {example.question}\nSQL: {example.sql}"
        if example.description:
            doc += f"\n说明: {example.description}"

        embedding = await self._embed.embed_text(doc)

        self._store.add_fewshots(
            ids=[doc_id],
            documents=[doc],
            embeddings=[embedding],
            metadatas=[{
                "datasource_id": str(example.datasource_id),
                "question": example.question,
                "sql": example.sql,
                "tags": example.tags or "",
                "type": "fewshot",
            }],
        )
        logger.info("Indexed few-shot example id=%d", example.id)

    # ------------------------------------------------------------------
    # Bulk re-index
    # ------------------------------------------------------------------

    async def index_all(
        self,
        datasource_id: int,
        tables: list,
        columns_by_table: Dict[str, list],
        fewshot_examples: list,
    ) -> Dict[str, int]:
        """Re-index all schemas and few-shot examples for a data source.

        First purges existing entries, then indexes the provided data.

        Args:
            datasource_id: The data source ID.
            tables: List of ``TableMetadata`` ORM objects.
            columns_by_table: Dict ``table_name`` → list of ``ColumnMetadata``.
            fewshot_examples: List of ``FewShotExample`` ORM objects.

        Returns:
            Dict with ``schemas`` and ``fewshots`` counts.
        """
        # Purge existing
        self._store.delete_by_datasource(datasource_id)

        # Re-index schemas
        schema_count = await self.index_schemas(datasource_id, tables, columns_by_table)

        # Re-index few-shots
        for example in fewshot_examples:
            await self.index_fewshot(example)

        logger.info(
            "Full re-index for datasource %d: %d schemas, %d few-shots",
            datasource_id, schema_count, len(fewshot_examples),
        )
        return {"schemas": schema_count, "fewshots": len(fewshot_examples)}
