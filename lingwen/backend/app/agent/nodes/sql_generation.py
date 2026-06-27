"""SQL generation node — CoT reasoning + LLM-powered Text2SQL with retry support."""

import logging
import re
import time
from typing import Dict

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import AgentState
from app.models.database import async_session
from app.models.table_metadata import TableMetadata
from app.models.column_metadata import ColumnMetadata
from app.models.datasource import DataSource
from app.services import skill_service
from app.adapters import get_adapter
from sqlalchemy import select

logger = logging.getLogger(__name__)

# Regex to extract SQL from the 【SQL】 block
_SQL_EXTRACT_RE = re.compile(r"【SQL】\s*(SELECT[\s\S]*?)$", re.IGNORECASE)

# Default prompt when no skill template is configured
_DEFAULT_PROMPT = (
    "你是一个专业的 SQL 查询助手。请根据以下信息生成准确的 SQL 查询：\n"
    "\n"
    "相关表结构：\n"
    "{schema_context}\n"
    "\n"
    "参考示例：\n"
    "{fewshot_context}\n"
    "\n"
    "{history_context}"
    "用户问题：{question}\n"
    "\n"
    "请先分析用户意图和查询逻辑，再生成SQL。严格按以下格式输出：\n"
    "【分析】\n"
    "简要说明：1)用户想查什么 2)涉及哪些表和字段 3)用什么聚合/关联逻辑\n"
    "【SQL】\n"
    "SELECT ..."
)


def _format_schema_context(schemas: list[dict]) -> str:
    """Turn retrieved schema documents into a readable text block."""
    if not schemas:
        return ""
    parts: list[str] = []
    for s in schemas:
        parts.append(s.get("content", ""))
    return "\n\n".join(parts)


async def _fetch_schema_fallback(datasource_id: int) -> str:
    """Fallback: query metadata tables directly when RAG returns nothing."""
    try:
        async with async_session() as db:
            result = await db.execute(
                select(TableMetadata).where(TableMetadata.datasource_id == datasource_id)
            )
            tables = result.scalars().all()
            if not tables:
                return ""
            parts: list[str] = []
            for table in tables:
                col_result = await db.execute(
                    select(ColumnMetadata).where(ColumnMetadata.table_id == table.id)
                )
                columns = col_result.scalars().all()
                col_lines = []
                for c in columns:
                    desc = f"({c.data_type})" 
                    if c.display_name: desc += f" 含义:{c.display_name}"
                    if c.business_description: desc += f" {c.business_description}"
                    col_lines.append(f"  - {c.column_name} {desc}")
                name = table.display_name or table.table_name
                desc = table.business_description or ""
                parts.append(f"表 {table.table_name} ({name}): {desc}\n" + "\n".join(col_lines))
            return "\n\n".join(parts)
    except Exception:
        return ""


def _format_fewshot_context(examples: list[dict]) -> str:
    """Turn retrieved few-shot examples into a readable text block."""
    if not examples:
        return "无相关示例。"
    parts: list[str] = []
    for i, ex in enumerate(examples, 1):
        parts.append(f"示例{i}：\n{ex.get('content', '')}")
    return "\n\n".join(parts)


def _format_history_context(history: list[dict]) -> str:
    """Format multi-turn conversation history for prompt injection.

    Each element is ``{"question": "...", "answer": "..."}``.
    Returns an empty string if history is empty so the prompt remains clean.
    """
    if not history:
        return ""
    parts = ["对话历史："]
    for i, turn in enumerate(history, 1):
        q = turn.get("question", "")
        a = turn.get("answer", "")[:200]  # Truncate long answers
        parts.append(f"第{i}轮 - 问: {q}")
        parts.append(f"第{i}轮 - 答: {a}")
    parts.append("")  # trailing newline before the current question
    return "\n".join(parts) + "\n"


def _extract_sql(text: str) -> str:
    """Extract the SQL statement from the LLM response.

    Args:
        text: The raw LLM output containing 【分析】 and 【SQL】 blocks.

    Returns:
        The extracted SQL, or the cleaned raw text if extraction fails.
    """
    match = _SQL_EXTRACT_RE.search(text)
    if match:
        sql = match.group(1).strip()
        # Remove trailing 【 if any (from incomplete format)
        sql = sql.rstrip("】").strip()
        logger.debug("Extracted SQL: %s", sql[:200])
        return sql

    # Fallback: try to find any SELECT statement
    select_match = re.search(r"(SELECT\s+[\s\S]*?)(?:;|\s*$)", text, re.IGNORECASE)
    if select_match:
        logger.warning("【SQL】 block not found, falling back to SELECT extraction")
        return select_match.group(1).strip()

    logger.error("No SQL could be extracted from LLM response")
    return text.strip()


class SQLGenerationNode:
    """Generates SQL via LLM with Chain-of-Thought reasoning.

    Supports retry: when ``error_info`` is present in the state the prompt
    includes the previous error so the LLM can self-correct.
    """

    def __init__(self, llm) -> None:
        """Args:
            llm: A ``ChatDeepSeek`` (or compatible) chat model instance.
        """
        self._llm = llm

    async def __call__(self, state: AgentState) -> Dict:
        """Generate SQL from the question and retrieved context.

        Args:
            state: Agent state with ``question``, ``retrieved_schemas``,
                ``retrieved_examples``, and optionally ``error_info`` and
                ``retry_count``.

        Returns:
            Partial state with ``cot_reasoning``, ``generated_sql``, and
            incremented ``retry_count``.
        """
        question: str = state["question"]
        schemas: list[dict] = state.get("retrieved_schemas", [])
        examples: list[dict] = state.get("retrieved_examples", [])
        error_info: str | None = state.get("error_info")
        retry_count: int = state.get("retry_count", 0)
        datasource_id: int = state["datasource_id"]
        t0 = time.time()

        is_retry = error_info is not None and retry_count > 0
        if is_retry:
            logger.info("[Pipeline|SQL生成] 重试#%d, datasource_id=%d error=%s", retry_count, datasource_id, error_info[:80])
        else:
            logger.info("[Pipeline|SQL生成] 开始, datasource_id=%d question=%s", datasource_id, question[:60])

        # Build context strings
        schema_context = _format_schema_context(schemas)
        # Fallback to DB metadata when RAG is empty
        if not schema_context:
            logger.info("[Pipeline|SQL生成] RAG为空, 使用元数据回退 ds_id=%d", datasource_id)
            schema_context = await _fetch_schema_fallback(datasource_id)
        fewshot_context = _format_fewshot_context(examples)

        logger.info("[Pipeline|SQL生成] 上下文: schema=%dchars fewshot=%dchars history=%d turns retry=%d",
                    len(schema_context), len(fewshot_context), len(state.get("history", [])), retry_count)

        # Get prompt template from active skill AND datasource dialect hint
        dialect_hint = ""
        try:
            async with async_session() as db:
                skill = await skill_service.get_active(db)
                prompt_template = (
                    skill.prompt_template if skill else _DEFAULT_PROMPT
                )
                # Look up datasource db_type → adapter → dialect hint
                ds_result = await db.execute(
                    select(DataSource.db_type).where(DataSource.id == datasource_id)
                )
                ds_db_type = ds_result.scalars().first()
                if ds_db_type:
                    adapter = get_adapter(ds_db_type)
                    dialect_hint = adapter.get_dialect_hint()
                    logger.info("[Pipeline|SQL生成] 使用方言提示, db_type=%s", ds_db_type)
        except Exception as exc:
            # Fallback: if DB query fails, use MySQL as safe default
            logger.warning("[Pipeline|SQL生成] 获取方言提示失败: %s, 回退到MySQL", exc)
            prompt_template = _DEFAULT_PROMPT
            dialect_hint = "MySQL SQL 查询。注意使用反引号标识符，LIMIT 分页。"

        # Fill template
        prompt = prompt_template.format(
            schema_context=schema_context,
            fewshot_context=fewshot_context,
            history_context=_format_history_context(state.get("history", [])),
            question=question,
        )

        # Append retry hint if applicable
        if error_info:
            prompt += (
                f"\n\n【重要】上次生成的 SQL 执行出错：{error_info}\n"
                "请仔细分析错误原因，修正 SQL 后重新生成。只返回修正后的内容。"
            )
            logger.info("SQL generation retry #%d: %s", retry_count + 1, error_info)

        # Build messages with dialect-aware system prompt
        if not dialect_hint:
            dialect_hint = "MySQL SQL 查询。注意使用反引号标识符，LIMIT 分页。"
        system_content = (
            f"你是一个专业的 SQL 查询助手，擅长将自然语言问题转换为准确、高效的 SQL 查询。\n\n"
            f"当前数据库类型与语法规范：{dialect_hint}\n\n"
            "请严格按照【分析】和【SQL】的格式输出。"
        )
        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=prompt),
        ]

        # Call LLM
        logger.info("[Pipeline|SQL生成] 调用LLM, model=%s", getattr(self._llm, 'model_name', 'unknown'))
        response = await self._llm.ainvoke(messages)
        full_text: str = response.content if hasattr(response, "content") else str(response)
        llm_elapsed = round((time.time() - t0) * 1000)

        # Extract native reasoning_content (DeepSeek R1 / V4 reasoning tokens)
        native_reasoning = ""
        if hasattr(response, "additional_kwargs"):
            native_reasoning = response.additional_kwargs.get("reasoning_content", "") or ""
        if not native_reasoning and hasattr(response, "response_metadata"):
            native_reasoning = str(response.response_metadata.get("reasoning_content", ""))
        logger.debug("Native reasoning: %d chars", len(native_reasoning))

        logger.debug("LLM response: %s", full_text[:500])

        # Extract parts
        sql = _extract_sql(full_text)

        logger.info("[Pipeline|SQL生成] 完成, sql=%dchars elapsed=%dms",
                    len(sql), llm_elapsed)

        # Extract CoT reasoning (everything before 【SQL】)
        cot_match = re.split(r"【SQL】", full_text, flags=re.IGNORECASE)
        cot_reasoning = cot_match[0].strip() if cot_match else full_text.strip()
        # Remove the 【分析】 tag if present
        cot_reasoning = cot_reasoning.replace("【分析】", "").strip()

        new_retry = retry_count + 1 if error_info else retry_count

        return {
            "cot_reasoning": cot_reasoning,
            "generated_sql": sql,
            "retry_count": new_retry,
            "native_reasoning": native_reasoning,
        }
