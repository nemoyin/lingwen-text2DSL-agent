"""Skill template CRUD service and default seed."""

import logging

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import SkillTemplate

logger = logging.getLogger(__name__)

# Default "智能问数" prompt template
_DEFAULT_SKILL_PROMPT = (
    "你是一个专业的 SQL 查询助手。请根据以下信息生成准确的 SQL 查询：\n"
    "\n"
    "相关表结构：\n"
    "{schema_context}\n"
    "\n"
    "参考示例：\n"
    "{fewshot_context}\n"
    "\n"
    "用户问题：{question}\n"
    "\n"
    "请先分析问题的数据需求，然后生成 SQL。只返回 SELECT 语句。"
)

_DEFAULT_SKILL_NAME = "智能问数"


async def create(db: AsyncSession, data: dict) -> SkillTemplate:
    """Create a new skill template.

    Args:
        db: The database session.
        data: Dict with ``name``, ``prompt_template``, and optional
            ``description``, ``rag_config``, ``security_policy``, ``is_active``.

    Returns:
        The newly created :class:`SkillTemplate` ORM object.

    Raises:
        HTTPException(409): If a skill with the same name already exists.
    """
    # Uniqueness check
    result = await db.execute(
        select(SkillTemplate).where(SkillTemplate.name == data["name"])
    )
    if result.scalars().first() is not None:
        raise HTTPException(status_code=409, detail="Skill 名称已存在")

    skill = SkillTemplate(**data)
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    logger.info("SkillTemplate created: id=%d name=%s", skill.id, skill.name)
    return skill


async def update(db: AsyncSession, skill_id: int, data: dict) -> SkillTemplate:
    """Update an existing skill template.

    Args:
        db: The database session.
        skill_id: Primary key of the skill.
        data: Dict with fields to update.

    Returns:
        The updated :class:`SkillTemplate` ORM object.

    Raises:
        HTTPException(404): If not found.
    """
    result = await db.execute(
        select(SkillTemplate).where(SkillTemplate.id == skill_id)
    )
    skill = result.scalars().first()
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill 模板不存在")

    for field, value in data.items():
        if hasattr(skill, field) and value is not None:
            setattr(skill, field, value)

    await db.commit()
    await db.refresh(skill)
    logger.info("SkillTemplate updated: id=%d", skill_id)
    return skill


async def delete(db: AsyncSession, skill_id: int) -> None:
    """Delete a skill template.

    Args:
        db: The database session.
        skill_id: Primary key of the skill.

    Raises:
        HTTPException(404): If not found.
    """
    result = await db.execute(
        select(SkillTemplate).where(SkillTemplate.id == skill_id)
    )
    skill = result.scalars().first()
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill 模板不存在")

    await db.delete(skill)
    await db.commit()
    logger.info("SkillTemplate deleted: id=%d", skill_id)


async def get_all(db: AsyncSession) -> list[SkillTemplate]:
    """List all skill templates.

    Args:
        db: The database session.

    Returns:
        A list of :class:`SkillTemplate` ORM objects.
    """
    result = await db.execute(
        select(SkillTemplate).order_by(SkillTemplate.id)
    )
    return list(result.scalars().all())


async def get_active(db: AsyncSession) -> SkillTemplate | None:
    """Return the first active skill template.

    Args:
        db: The database session.

    Returns:
        An active :class:`SkillTemplate` or ``None``.
    """
    result = await db.execute(
        select(SkillTemplate)
        .where(SkillTemplate.is_active == True)
        .order_by(SkillTemplate.id)
        .limit(1)
    )
    return result.scalars().first()


async def seed_default_skill(db: AsyncSession) -> SkillTemplate:
    """Ensure the default "智能问数" skill template exists.

    If a skill with the name already exists it is left untouched.

    Args:
        db: The database session.

    Returns:
        The existing or newly created default skill.
    """
    result = await db.execute(
        select(SkillTemplate).where(SkillTemplate.name == _DEFAULT_SKILL_NAME)
    )
    existing = result.scalars().first()
    if existing is not None:
        logger.debug("Default skill already exists: id=%d", existing.id)
        return existing

    skill = SkillTemplate(
        name=_DEFAULT_SKILL_NAME,
        description="通用智能问数 Skill，支持 Schema + Few-shot RAG 增强的 Text2SQL",
        prompt_template=_DEFAULT_SKILL_PROMPT,
        rag_config={
            "schema_top_k": 5,
            "fewshot_top_k": 3,
            "use_hybrid_search": True,
        },
        security_policy={
            "max_rows": 1000,
            "readonly": True,
            "block_dangerous": True,
        },
        is_active=True,
    )
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    logger.info("Default skill seeded: id=%d name=%s", skill.id, skill.name)
    return skill
