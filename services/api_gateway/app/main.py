"""API Gateway - FastAPI Reverse Proxy with Auth, Rate Limiting, and Org Scoping."""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Optional

import httpx
import redis.asyncio as redis
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic_settings import BaseSettings

from shared.auth import verify_token

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("api_gateway")


class GatewaySettings(BaseSettings):
    jwt_public_key: str = ""
    jwt_algorithm: str = "RS256"
    jwt_public_key_path: str = "/app/keys/public.pem"

    auth_service_url: str = "http://auth_service:8001"
    org_service_url: str = "http://org_service:8002"
    project_service_url: str = "http://project_service:8003"
    task_service_url: str = "http://task_service:8004"
    notification_service_url: str = "http://notification_service:8005"
    file_service_url: str = "http://file_service:8006"

    redis_url: str = "redis://redis:6379/0"
    rate_limit_per_minute: int = 120
    rate_limit_burst: int = 30

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def public_key(self) -> str:
        if self.jwt_public_key:
            return self.jwt_public_key
        try:
            with open(self.jwt_public_key_path) as f:
                return f.read()
        except FileNotFoundError:
            logger.warning("Public key not found, auth will not work")
            return ""


@lru_cache()
def get_settings() -> GatewaySettings:
    return GatewaySettings()


# ---- Service Route Map ----

ROUTE_MAP: list[tuple[str, str]] = [
    # (path_prefix, settings_attribute)
    ("/api/v1/auth", "auth_service_url"),
    ("/api/v1/organizations", "org_service_url"),
    ("/api/v1/projects", "project_service_url"),
    ("/api/v1/tasks", "task_service_url"),
    ("/api/v1/notifications", "notification_service_url"),
    ("/api/v1/files", "file_service_url"),
]

# Routes that don't require authentication
PUBLIC_PATHS = {
    "/api/v1/auth/register",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/health",
}

_http_client: httpx.AsyncClient | None = None
_redis_client: redis.Redis | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _http_client, _redis_client
    _http_client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    settings = get_settings()
    try:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    except Exception:
        logger.warning("Redis not available, rate limiting disabled")

    logger.info("API Gateway started")
    yield

    if _http_client:
        await _http_client.aclose()
    if _redis_client:
        await _redis_client.aclose()


app = FastAPI(
    title="TaskPM API Gateway",
    description="Unified API Gateway for all TaskPM microservices",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Rate Limiting ----

async def check_rate_limit(request: Request) -> None:
    """Sliding window rate limiter using Redis."""
    if _redis_client is None:
        return

    settings = get_settings()
    # Use IP or authenticated user_id as key
    client_id = request.client.host if request.client else "unknown"

    key = f"rate_limit:{client_id}"
    now = int(time.time())
    window_start = now - 60

    pipe = _redis_client.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)
    pipe.zadd(key, {str(now * 1000 + id(request) % 1000): now})
    pipe.zcard(key)
    pipe.expire(key, 120)
    results = await pipe.execute()

    count = results[2]
    if count > settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": "60"},
        )


# ---- JWT Auth Middleware ----

def resolve_service_url(path: str) -> Optional[tuple[str, str]]:
    """Find the target service URL for a given request path."""
    settings = get_settings()
    for prefix, attr in ROUTE_MAP:
        if path.startswith(prefix):
            base_url = getattr(settings, attr)
            # Strip /api/v1 prefix - forward the remainder
            downstream_path = path[len("/api/v1"):]
            return base_url, downstream_path
    return None


# ---- Proxy Handler ----

@app.api_route(
    "/api/v1/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def proxy(request: Request, path: str):
    """Reverse proxy all /api/v1/* requests to the appropriate microservice."""
    full_path = f"/api/v1/{path}"

    # Rate limiting
    await check_rate_limit(request)

    settings = get_settings()

    # Authenticate if not a public route
    user_claims: dict = {}
    is_public = any(full_path.startswith(p) for p in PUBLIC_PATHS)

    if not is_public:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(401, "Missing or invalid authorization header")

        token = auth_header.split(" ", 1)[1]
        try:
            user_claims = verify_token(token, settings.public_key, settings.jwt_algorithm)
        except Exception as e:
            raise HTTPException(401, f"Invalid token: {str(e)}")

    # Resolve destination service
    route = resolve_service_url(full_path)
    if not route:
        raise HTTPException(404, "Service not found for this path")

    base_url, downstream_path = route

    # Build downstream URL
    url = f"{base_url}{downstream_path}"
    if request.url.query:
        url = f"{url}?{request.url.query}"

    # Build headers to forward
    headers = dict(request.headers)
    headers.pop("host", None)

    # Inject org context
    if user_claims.get("org_id"):
        headers["X-Org-Id"] = str(user_claims["org_id"])
    if user_claims.get("sub"):
        headers["X-User-Id"] = str(user_claims["sub"])

    # Forward the request
    body = await request.body()

    try:
        response = await _http_client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
        )
    except httpx.ConnectError:
        raise HTTPException(503, "Service unavailable")
    except httpx.TimeoutException:
        raise HTTPException(504, "Service timeout")

    # Forward response
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
    )


# ---- Health Check ----

@app.get("/health")
async def health_check():
    return {"service": "api_gateway", "status": "healthy"}


@app.get("/health/services")
async def services_health():
    """Check health of all downstream services."""
    settings = get_settings()
    results = {}

    for prefix, attr in ROUTE_MAP:
        service_name = attr.replace("_url", "")
        base_url = getattr(settings, attr)
        try:
            resp = await _http_client.get(f"{base_url}/health", timeout=5.0)
            results[service_name] = {
                "status": "healthy" if resp.status_code == 200 else "degraded",
                "response_time_ms": resp.elapsed.total_seconds() * 1000,
            }
        except Exception:
            results[service_name] = {"status": "unreachable"}

    return {"services": results}
