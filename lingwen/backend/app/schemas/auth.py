"""Authentication schemas: request and response models."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Credentials submitted by the user to obtain a JWT token."""

    username: str = Field(..., min_length=1, max_length=100, description="登录用户名")
    password: str = Field(..., min_length=1, description="登录密码")


class TokenResponse(BaseModel):
    """JWT token returned after successful authentication."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Seconds until token expires")

    model_config = {"from_attributes": True}
