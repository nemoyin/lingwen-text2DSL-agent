"""SQLAlchemy async engine and session configuration."""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.config import settings

logger = logging.getLogger(__name__)

# Async engine for MySQL via aiomysql
engine = create_async_engine(
    settings.async_db_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=False,  # disabled: aiomysql async ping() incompatible with SQLAlchemy do_ping
    pool_recycle=3600,
)

# Async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Declarative base for all ORM models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session with automatic cleanup.

    Usage:
        async for session in get_db():
            yield session
    """
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
