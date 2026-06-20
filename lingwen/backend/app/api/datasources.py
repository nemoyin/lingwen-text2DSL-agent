"""Data source CRUD routes."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.datasource import (
    DataSourceCreate,
    DataSourceResponse,
    DataSourceUpdate,
)
from app.schemas.common import ApiResponse
from app.services import datasource_service
from app.utils.response import success

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=dict)
async def list_datasources(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List all registered data sources (passwords omitted).

    Args:
        db: The database session (injected).

    Returns:
        A list of DataSourceResponse objects.
    """
    items = await datasource_service.get_all(db)
    result = [DataSourceResponse.model_validate(ds).model_dump() for ds in items]
    return success(data=result)


@router.post("/", response_model=dict)
async def create_datasource(
    payload: DataSourceCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Register a new data source.

    Args:
        payload: Connection details (password will be encrypted server-side).
        db: The database session (injected).

    Returns:
        The created DataSourceResponse.
    """
    try:
        ds = await datasource_service.create(db, payload)
    except HTTPException:
        raise
    result = DataSourceResponse.model_validate(ds).model_dump()
    return success(data=result)


@router.get("/{datasource_id}", response_model=dict)
async def get_datasource(
    datasource_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Retrieve a single data source by ID.

    Args:
        datasource_id: The primary key of the data source.
        db: The database session (injected).

    Returns:
        The DataSourceResponse.
    """
    try:
        ds = await datasource_service.get(db, datasource_id)
    except HTTPException:
        raise
    result = DataSourceResponse.model_validate(ds).model_dump()
    return success(data=result)


@router.put("/{datasource_id}", response_model=dict)
async def update_datasource(
    datasource_id: int,
    payload: DataSourceUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update an existing data source.

    Args:
        datasource_id: The primary key of the data source.
        payload: The fields to update.
        db: The database session (injected).

    Returns:
        The updated DataSourceResponse.
    """
    try:
        ds = await datasource_service.update(db, datasource_id, payload)
    except HTTPException:
        raise
    result = DataSourceResponse.model_validate(ds).model_dump()
    return success(data=result)


@router.delete("/{datasource_id}", response_model=dict)
async def delete_datasource(
    datasource_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a data source record.

    Args:
        datasource_id: The primary key of the data source.
        db: The database session (injected).

    Returns:
        A confirmation message.
    """
    try:
        await datasource_service.delete(db, datasource_id)
    except HTTPException:
        raise
    return success(data=None, message="数据源已删除")


@router.post("/{datasource_id}/test", response_model=dict)
async def test_connection(
    datasource_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Test connectivity to a data source.

    Args:
        datasource_id: The primary key of the data source.
        db: The database session (injected).

    Returns:
        ``{"success": true/false, "message": "..."}``.
    """
    try:
        ok = await datasource_service.test_connection(db, datasource_id)
        return success(data={
            "success": ok,
            "message": "连接成功" if ok else "连接失败，请检查配置",
        })
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Connection test error: %s", exc)
        return success(data={
            "success": False,
            "message": f"连接异常: {str(exc)}",
        })
