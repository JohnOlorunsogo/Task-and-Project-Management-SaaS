"""JWT creation and verification utilities (RS256)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

security_scheme = HTTPBearer()


class TokenData(BaseModel):
    """Decoded JWT payload."""
    user_id: str
    email: str
    org_id: Optional[str] = None
    org_role: Optional[str] = None


class TokenPair(BaseModel):
    """Access + refresh token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def create_access_token(
    data: dict[str, Any],
    private_key: str,
    algorithm: str = "RS256",
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "type": "access"})
    return jwt.encode(to_encode, private_key, algorithm=algorithm)


def create_refresh_token(
    data: dict[str, Any],
    private_key: str,
    algorithm: str = "RS256",
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=7))
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    })
    return jwt.encode(to_encode, private_key, algorithm=algorithm)


def verify_token(token: str, public_key: str, algorithm: str = "RS256") -> dict[str, Any]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, public_key, algorithms=[algorithm])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(public_key: str, algorithm: str = "RS256"):
    """Factory that returns a FastAPI dependency for extracting the current user from JWT."""

    async def _dependency(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    ) -> TokenData:
        payload = verify_token(credentials.credentials, public_key, algorithm)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        # org_id priority: JWT claim > X-Org-Id header (sent by frontend)
        org_id = payload.get("org_id") or request.headers.get("x-org-id")

        return TokenData(
            user_id=payload["sub"],
            email=payload.get("email", ""),
            org_id=org_id,
            org_role=payload.get("org_role"),
        )

    return _dependency

