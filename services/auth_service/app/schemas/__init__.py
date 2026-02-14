"""Auth Service Pydantic Schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# Request Schemas


class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    org_name: Optional[str] = Field(
        default=None, max_length=255,
        description="Organization name. If provided, creates a new org and assigns user as OrgAdmin."
    )


class BatchUserRequest(BaseModel):
    user_ids: list[uuid.UUID]


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class UpdateProfileRequest(BaseModel):
    """Update user profile."""
    full_name: Optional[str] = Field(default=None, max_length=255)


# Response Schemas


class UserResponse(BaseModel):
    """Public user representation."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    created_at: datetime


class AuthResponse(BaseModel):
    """Authentication response with tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenResponse(BaseModel):
    """Token-only response (for refresh)."""
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str
