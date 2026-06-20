"""Authentication service: JWT tokens, password hashing, user management."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from jose import JWTError, jwt
import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)

# JWT configuration
_ALGORITHM: str = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(user_id: int, username: str) -> str:
    """Create a signed JWT access token.

    Args:
        user_id: The user's primary key.
        username: The user's login name.

    Returns:
        An encoded JWT string.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_expire_minutes
    )
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=_ALGORITHM)


def verify_token(token: str) -> dict:
    """Decode and verify a JWT token.

    Args:
        token: The encoded JWT string (without "Bearer " prefix).

    Returns:
        A dict with ``user_id`` and ``username`` keys.

    Raises:
        HTTPException(401): If the token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[_ALGORITHM])
        user_id_str: Optional[str] = payload.get("sub")
        username: Optional[str] = payload.get("username")
        if user_id_str is None or username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return {"user_id": int(user_id_str), "username": username}
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Token invalid or expired") from exc


async def create_user(
    db: AsyncSession,
    username: str,
    password: str,
    role: str = "user",
) -> User:
    """Create a new user with a hashed password.

    Args:
        db: The database session.
        username: Unique login name.
        password: Plain-text password (will be bcrypt-hashed).
        role: User role string.

    Returns:
        The newly created User ORM object.

    Raises:
        HTTPException(409): If the username is already taken.
    """
    # Check uniqueness
    result = await db.execute(select(User).where(User.username == username))
    if result.scalars().first() is not None:
        raise HTTPException(status_code=409, detail="用户名已存在")

    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("User created: id=%d username=%s", user.id, username)
    return user


async def authenticate(
    db: AsyncSession,
    username: str,
    password: str,
) -> User:
    """Authenticate a user by username and password.

    Args:
        db: The database session.
        username: Login name.
        password: Plain-text password.

    Returns:
        The authenticated User object.

    Raises:
        HTTPException(401): If credentials are invalid.
    """
    result = await db.execute(
        select(User).where(User.username == username, User.is_active == True)
    )
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return user
