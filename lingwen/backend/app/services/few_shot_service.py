"""Few-shot example CRUD service."""

import logging

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.few_shot import FewShotExample

logger = logging.getLogger(__name__)


async def create(
    db: AsyncSession,
    data: dict,
) -> FewShotExample:
    """Create a new few-shot example.

    Args:
        db: The database session.
        data: Dict with ``datasource_id``, ``question``, ``sql``, and
            optional ``description`` and ``tags``.

    Returns:
        The newly created :class:`FewShotExample` ORM object.
    """
    example = FewShotExample(**data)
    db.add(example)
    await db.commit()
    await db.refresh(example)
    logger.info("FewShotExample created: id=%d", example.id)
    return example


async def update(
    db: AsyncSession,
    example_id: int,
    data: dict,
) -> FewShotExample:
    """Update an existing few-shot example.

    Args:
        db: The database session.
        example_id: Primary key of the example.
        data: Dict with fields to update.

    Returns:
        The updated :class:`FewShotExample` ORM object.

    Raises:
        HTTPException(404): If not found.
    """
    result = await db.execute(
        select(FewShotExample).where(FewShotExample.id == example_id)
    )
    example = result.scalars().first()
    if example is None:
        raise HTTPException(status_code=404, detail="Few-shot 示例不存在")

    for field, value in data.items():
        if hasattr(example, field) and value is not None:
            setattr(example, field, value)

    await db.commit()
    await db.refresh(example)
    logger.info("FewShotExample updated: id=%d", example_id)
    return example


async def delete(db: AsyncSession, example_id: int) -> None:
    """Delete a few-shot example.

    Args:
        db: The database session.
        example_id: Primary key of the example.

    Raises:
        HTTPException(404): If not found.
    """
    result = await db.execute(
        select(FewShotExample).where(FewShotExample.id == example_id)
    )
    example = result.scalars().first()
    if example is None:
        raise HTTPException(status_code=404, detail="Few-shot 示例不存在")

    await db.delete(example)
    await db.commit()
    logger.info("FewShotExample deleted: id=%d", example_id)


async def get_all(
    db: AsyncSession,
    datasource_id: int,
) -> list[FewShotExample]:
    """List all few-shot examples for a data source.

    Args:
        db: The database session.
        datasource_id: The data source to filter by.

    Returns:
        A list of :class:`FewShotExample` ORM objects.
    """
    result = await db.execute(
        select(FewShotExample)
        .where(FewShotExample.datasource_id == datasource_id)
        .order_by(FewShotExample.id)
    )
    return list(result.scalars().all())
