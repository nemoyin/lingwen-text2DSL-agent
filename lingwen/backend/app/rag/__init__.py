"""RAG (Retrieval-Augmented Generation) layer for the Lingwen agent.

Exports the embedding client, vector store, retrievers, and indexer
that together power schema-aware and few-shot retrieval.
"""

from app.rag.embeddings import EmbeddingClient
from app.rag.vector_store import VectorStore
from app.rag.retriever import SchemaRetriever, FewShotRetriever
from app.rag.indexer import Indexer

__all__ = [
    "EmbeddingClient",
    "VectorStore",
    "SchemaRetriever",
    "FewShotRetriever",
    "Indexer",
]
