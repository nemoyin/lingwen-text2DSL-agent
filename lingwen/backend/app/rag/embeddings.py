"""Embedding client wrapping OpenAI-compatible embeddings APIs (DeepSeek, Qwen3, etc.)."""

import logging
from typing import List

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Default embedding endpoint (DeepSeek)
_DEFAULT_EMBED_URL = "https://api.deepseek.com/v1/embeddings"


class EmbeddingClient:
    """Async client for generating text embeddings via OpenAI-compatible API.

    Supports configurable base URL and API key — defaults to DeepSeek if not
    explicitly configured.

    Usage::

        client = EmbeddingClient()
        vec = await client.embed_text("hello")
        vecs = await client.embed_documents(["hello", "world"])
    """

    def __init__(self) -> None:
        # API key: use dedicated embed_api_key if set, otherwise fall back to llm_api_key
        self._api_key: str = settings.embed_api_key or settings.llm_api_key
        self._model: str = settings.llm_embed_model
        # Base URL: use dedicated embed_base_url if set, otherwise default to DeepSeek
        _base = (settings.embed_base_url or "").rstrip("/")
        self._embed_url: str = f"{_base}/embeddings" if _base else _DEFAULT_EMBED_URL
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazy-initialise and return a shared httpx AsyncClient."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def embed_text(self, text: str) -> List[float]:
        """Embed a single text string.

        Args:
            text: The text to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        results = await self.embed_documents([text])
        return results[0]

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of text strings.

        Args:
            texts: A list of texts to embed (max ~100 per batch).

        Returns:
            A list of embedding vectors, one per input text.
        """
        if not texts:
            return []

        client = await self._get_client()
        payload = {
            "model": self._model,
            "input": texts,
        }

        try:
            resp = await client.post(self._embed_url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            # Sort by index to preserve input order
            items = sorted(data["data"], key=lambda x: x["index"])
            embeddings = [item["embedding"] for item in items]
            logger.debug("Embedded %d documents (dim=%d)", len(texts), len(embeddings[0]) if embeddings else 0)
            return embeddings
        except httpx.HTTPStatusError as exc:
            logger.error("Embedding API error: %s %s", exc.response.status_code, exc.response.text[:200])
            raise
        except Exception as exc:
            logger.error("Embedding request failed: %s", exc)
            raise

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
