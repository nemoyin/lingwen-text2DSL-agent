"""Skill template routes — CRUD for agent skill configuration."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.skill import SkillCreate, SkillResponse, SkillUpdate
from app.services import skill_service
from app.utils.response import success

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=dict)
async def list_skills(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List all skill templates.

    Args:
        db: The database session (injected).

    Returns:
        A list of SkillResponse objects.
    """
    items = await skill_service.get_all(db)
    result = [SkillResponse.model_validate(s).model_dump() for s in items]
    return success(data=result)


@router.post("/", response_model=dict)
async def create_skill(
    payload: SkillCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new skill template.

    Args:
        payload: Skill configuration (name, prompt_template, etc.).
        db: The database session (injected).

    Returns:
        The created SkillResponse.
    """
    try:
        skill = await skill_service.create(db, payload.model_dump())
    except HTTPException:
        raise
    result = SkillResponse.model_validate(skill).model_dump()
    return success(data=result)


@router.get("/{skill_id}", response_model=dict)
async def get_skill(
    skill_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Retrieve a single skill template by ID.

    Args:
        skill_id: The primary key of the skill.
        db: The database session (injected).

    Returns:
        The SkillResponse.
    """
    items = await skill_service.get_all(db)
    found = None
    for item in items:
        if item.id == skill_id:
            found = item
            break
    if found is None:
        raise HTTPException(status_code=404, detail="Skill 模板不存在")
    result = SkillResponse.model_validate(found).model_dump()
    return success(data=result)


@router.put("/{skill_id}", response_model=dict)
async def update_skill(
    skill_id: int,
    payload: SkillUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update an existing skill template.

    Args:
        skill_id: The primary key of the skill.
        payload: Fields to update.
        db: The database session (injected).

    Returns:
        The updated SkillResponse.
    """
    try:
        skill = await skill_service.update(
            db, skill_id, payload.model_dump(exclude_unset=True)
        )
    except HTTPException:
        raise
    result = SkillResponse.model_validate(skill).model_dump()
    return success(data=result)


@router.delete("/{skill_id}", response_model=dict)
async def delete_skill(
    skill_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a skill template.

    Args:
        skill_id: The primary key of the skill.
        db: The database session (injected).

    Returns:
        A confirmation message.
    """
    try:
        await skill_service.delete(db, skill_id)
    except HTTPException:
        raise
    return success(data=None, message="Skill 模板已删除")
