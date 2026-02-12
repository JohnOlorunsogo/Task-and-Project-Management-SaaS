"""Auth Service API Routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import TokenData

from app.dependencies import get_auth_service, get_current_user
from app.schemas import (
    AuthResponse,
    ChangePasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    data: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """Register a new user account. Optionally creates an organization."""
    return await auth_service.register(data)


@router.post("/login", response_model=AuthResponse)
async def login(
    data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """Authenticate with email and password."""
    return await auth_service.login(data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Refresh an access token using a valid refresh token."""
    return await auth_service.refresh_token(data.refresh_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    data: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """Logout by blacklisting the refresh token."""
    await auth_service.logout(data.refresh_token)
    return MessageResponse(message="Successfully logged out")


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: TokenData = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Get the current user's profile."""
    return await auth_service.get_user(current_user.user_id)


@router.put("/password", response_model=MessageResponse)
async def change_password(
    data: ChangePasswordRequest,
    current_user: TokenData = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """Change the current user's password."""
    await auth_service.change_password(current_user.user_id, data)
    return MessageResponse(message="Password changed successfully")
