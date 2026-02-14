"""Auth Service - Business Logic."""

from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Optional

import redis.asyncio as redis
from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import (
    TokenData,
    TokenPair,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from shared.events import TOPICS, USER_REGISTERED
from shared.events.producer import event_producer

from app.models import User
from app.schemas import (
    AuthResponse,
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")


class AuthService:
    """Handles user authentication business logic."""

    def __init__(
        self,
        db: AsyncSession,
        redis_client: redis.Redis,
        private_key: str,
        public_key: str,
        algorithm: str,
        access_expire_minutes: int,
        refresh_expire_days: int,
    ) -> None:
        self.db = db
        self.redis = redis_client
        self.private_key = private_key
        self.public_key = public_key
        self.algorithm = algorithm
        self.access_expire = timedelta(minutes=access_expire_minutes)
        self.refresh_expire = timedelta(days=refresh_expire_days)

    async def register(self, data: RegisterRequest) -> AuthResponse:
        """Register a new user and optionally create an organization."""
        # Check if email already exists
        stmt = select(User).where(User.email == data.email)
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        # Create user
        user = User(
            id=uuid.uuid4(),
            email=data.email,
            hashed_password=pwd_context.hash(data.password),
            full_name=data.full_name,
        )
        self.db.add(user)
        await self.db.flush()

        # Generate tokens
        token_data = {
            "sub": str(user.id),
            "email": user.email,
        }

        # If org_name provided, include org info in token
        # The org_service will handle actual org creation via event
        org_id = None
        if data.org_name:
            org_id = str(uuid.uuid4())
            token_data["org_id"] = org_id
            token_data["org_role"] = "org_admin"

        tokens = self._create_tokens(token_data)

        # Publish event
        await event_producer.publish(
            TOPICS["users"],
            {
                "event_type": USER_REGISTERED,
                "user_id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "org_id": org_id,
                "org_name": data.org_name,
            },
            key=str(user.id),
        )

        return AuthResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            user=UserResponse.model_validate(user),
        )

    async def login(self, data: LoginRequest) -> AuthResponse:
        """Authenticate user and return tokens."""
        stmt = select(User).where(User.email == data.email)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Verify password and update hash if needed (migration from bcrypt to bcrypt_sha256)
        verified, updated_hash = pwd_context.verify_and_update(data.password, user.hashed_password)
        if not verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if updated_hash:
            user.hashed_password = updated_hash
            await self.db.flush()

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled",
            )

        # Look up org membership
        token_data = {
            "sub": str(user.id),
            "email": user.email,
        }

        # Query org_service for memberships via HTTP
        # Shared DB access is not possible due to isolation
        import httpx
        from app.config import get_settings
        settings = get_settings()
        
        # We assume org_service is reachable internal URL
        # We perform a fire-and-forget style fetch or wait? we need it for token.
        try:
             async with httpx.AsyncClient() as client:
                # org_service_url is http://org_service:8002
                url = f"{settings.org_service_url}/organizations/memberships"
                resp = await client.get(url, params={"user_id": str(user.id)})
                if resp.status_code == 200:
                    memberships = resp.json()
                    if memberships:
                        # Pick the first one as default context
                        # In the future, user might select which org to login to
                        first_org = memberships[0]
                        token_data["org_id"] = first_org["org_id"]
                        token_data["org_role"] = first_org["role"]
        except Exception as e:
            # Fallback: Login succeeds but without org context (user might be new or service down)
            # Log error in production
            print(f"Failed to fetch org memberships: {e}")
            pass

        tokens = self._create_tokens(token_data)

        return AuthResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            user=UserResponse.model_validate(user),
        )

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh an access token using a valid refresh token."""
        # Check if token is blacklisted
        is_blacklisted = await self.redis.get(f"blacklist:{refresh_token}")
        if is_blacklisted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
            )

        payload = verify_token(refresh_token, self.public_key, self.algorithm)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        # Create new access token
        token_data = {
            "sub": payload["sub"],
            "email": payload.get("email", ""),
        }
        if "org_id" in payload:
            token_data["org_id"] = payload["org_id"]
        if "org_role" in payload:
            token_data["org_role"] = payload["org_role"]

        access_token = create_access_token(
            token_data, self.private_key, self.algorithm, self.access_expire
        )

        return TokenResponse(access_token=access_token)

    async def logout(self, refresh_token: str) -> None:
        """Blacklist a refresh token."""
        payload = verify_token(refresh_token, self.public_key, self.algorithm)
        jti = payload.get("jti", refresh_token)
        # Blacklist for the remaining TTL of the token
        ttl = int(self.refresh_expire.total_seconds())
        await self.redis.setex(f"blacklist:{jti}", ttl, "1")

    async def change_password(
        self, user_id: str, data: ChangePasswordRequest
    ) -> None:
        """Change user password."""
        stmt = select(User).where(User.id == uuid.UUID(user_id))
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Verify current password and update hash if needed
        verified, updated_hash = pwd_context.verify_and_update(data.current_password, user.hashed_password)
        if not verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        if updated_hash:
            # Hash already updated, but we are about to change it anyway
            pass

        user.hashed_password = pwd_context.hash(data.new_password)
        await self.db.flush()

    async def get_user(self, user_id: str) -> UserResponse:
        """Get user profile."""
        stmt = select(User).where(User.id == uuid.UUID(user_id))
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return UserResponse.model_validate(user)

    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        """Get user by email."""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            return UserResponse.model_validate(user)
        return None

    async def get_users_batch(self, user_ids: list[uuid.UUID]) -> list[UserResponse]:
        """Fetch multiple users by ID."""
        if not user_ids:
            return []
        
        stmt = select(User).where(User.id.in_(user_ids))
        result = await self.db.execute(stmt)
        users = result.scalars().all()
        
        return [UserResponse.model_validate(u) for u in users]

    def _create_tokens(self, token_data: dict) -> TokenPair:
        """Create access + refresh token pair."""
        access_token = create_access_token(
            token_data, self.private_key, self.algorithm, self.access_expire
        )
        refresh_token = create_refresh_token(
            token_data, self.private_key, self.algorithm, self.refresh_expire
        )
        return TokenPair(access_token=access_token, refresh_token=refresh_token)
