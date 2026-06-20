"""Model service — load active default model from database for LLM construction."""
import logging
from typing import Any, Dict, Optional

from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def build_llm(config: Dict[str, Any]):
    """Build a LangChain ChatModel from a model_configs row dict.

    Supported providers:
        - deepseek  → ChatDeepSeek
        - openai / kimi / glm / minimax → ChatOpenAI (OpenAI-compatible)
    """
    provider = config.get("provider", "deepseek")
    model = config.get("model_name", "deepseek-chat")
    api_key = config.get("api_key", "")
    api_base = config.get("api_base", "")

    logger.info("Building LLM: provider=%s model=%s base=%s", provider, model, api_base[:40])

    if provider == "deepseek":
        return ChatDeepSeek(
            model=model,
            api_key=api_key,
            api_base=api_base or "https://api.deepseek.com/v1",
            temperature=0.1,
        )
    else:
        # openai, kimi, glm, minimax — all OpenAI-compatible
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=api_base,
            temperature=0.1,
        )


class ModelService:
    """Resolves the active default model from the model_configs table."""

    @staticmethod
    async def get_default(db: AsyncSession) -> Optional[dict]:
        result = await db.execute(text(
            "SELECT * FROM model_configs WHERE is_active=1 AND is_default=1 LIMIT 1"
        ))
        row = result.fetchone()
        if not row:
            # Fallback to first active model
            result = await db.execute(text(
                "SELECT * FROM model_configs WHERE is_active=1 ORDER BY id LIMIT 1"
            ))
            row = result.fetchone()
        if row:
            return dict(row._mapping)
        return None
