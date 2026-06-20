"""Auth routes — login and token management."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.config import settings
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.common import ApiResponse
from app.services import auth_service
from app.utils.response import success

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)) -> dict:
    """Return current authenticated user info."""
    return success(data=user)


@router.post("/login", response_model=dict)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Authenticate a user and return a JWT access token.

    Args:
        payload: Username and password credentials.
        db: The database session (injected).

    Returns:
        An ApiResponse-wrapped TokenResponse.
    """
    try:
        user = await auth_service.authenticate(db, payload.username, payload.password)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Authentication error: %s", exc)
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token: str = auth_service.create_access_token(user.id, user.username)
    expires_in: int = settings.jwt_expire_minutes * 60

    token_data = TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
    )
    return success(data=token_data.model_dump())
