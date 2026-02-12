"""Notification Service - FastAPI Application with WebSocket and Kafka Consumer."""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import APIRouter, Depends, FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from shared.auth import TokenData, get_current_user as _get_current_user_factory, verify_token
from shared.database import db_manager
from shared.events import TOPICS, TASK_ASSIGNED, TASK_STATUS_CHANGED, COMMENT_ADDED
from shared.events.consumer import EventConsumer
from shared.models import HealthResponse

from app.config import get_settings
from app.schemas import (
    NotificationPreferenceResponse, NotificationResponse,
    UpdatePreferencesRequest,
)
from app.services import (
    NotificationService, handle_comment_added,
    handle_task_assigned, handle_task_status_changed,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("notification_service")

settings = get_settings()

# Redis client
_redis_client: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


async def get_db():
    async for session in db_manager.get_session():
        yield session


get_current_user = _get_current_user_factory(settings.jwt_public_key, settings.jwt_algorithm)


async def get_notification_service(
    db=Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
) -> NotificationService:
    return NotificationService(db, redis_client)


# Kafka consumer for incoming events
event_consumer = EventConsumer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Notification Service on port %s", settings.service_port)

    db_manager.init(settings.database_url)
    from shared.database import Base
    from app.models import Notification, NotificationPreference  # noqa
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    redis_client = await get_redis()

    # Register Kafka event handlers
    session_factory = db_manager.session_factory

    event_consumer.on(TASK_ASSIGNED, lambda e: handle_task_assigned(e, session_factory, redis_client))
    event_consumer.on(COMMENT_ADDED, lambda e: handle_comment_added(e, session_factory, redis_client))
    event_consumer.on(TASK_STATUS_CHANGED, lambda e: handle_task_status_changed(e, session_factory, redis_client))

    # Start Kafka consumer in background
    try:
        await event_consumer.start(
            settings.kafka_bootstrap_servers,
            topics=[TOPICS["tasks"], TOPICS["comments"]],
            group_id="notification_service",
        )
        consumer_task = asyncio.create_task(event_consumer.consume())
    except Exception:
        logger.warning("Kafka not available, running without event consumption")
        consumer_task = None

    yield

    if consumer_task:
        consumer_task.cancel()
        await event_consumer.stop()
    await db_manager.close()


app = FastAPI(
    title="TaskPM Notification Service",
    description="Notifications, preferences, and real-time WebSocket updates",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    unread_only: bool = Query(default=False),
    current_user: TokenData = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
) -> list[NotificationResponse]:
    return await svc.list_notifications(current_user.user_id, unread_only)


@router.get("/unread-count")
async def unread_count(
    current_user: TokenData = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
) -> dict:
    count = await svc.get_unread_count(current_user.user_id)
    return {"count": count}


@router.put("/{notification_id}/read", status_code=204)
async def mark_read(
    notification_id: str,
    current_user: TokenData = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
) -> None:
    import uuid
    await svc.mark_read(uuid.UUID(notification_id), current_user.user_id)


@router.put("/read-all", status_code=204)
async def mark_all_read(
    current_user: TokenData = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
) -> None:
    await svc.mark_all_read(current_user.user_id)


@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_preferences(
    current_user: TokenData = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
) -> NotificationPreferenceResponse:
    return await svc.get_preferences(current_user.user_id)


@router.put("/preferences", response_model=NotificationPreferenceResponse)
async def update_preferences(
    data: UpdatePreferencesRequest,
    current_user: TokenData = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
) -> NotificationPreferenceResponse:
    return await svc.update_preferences(current_user.user_id, data)


app.include_router(router)


# ---- WebSocket for real-time notifications ----

@app.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    """WebSocket endpoint for real-time notification delivery via Redis Pub/Sub."""
    await websocket.accept()

    # Authenticate via query param token
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    try:
        payload = verify_token(token, settings.jwt_public_key, settings.jwt_algorithm)
        user_id = payload["sub"]
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    redis_client = await get_redis()
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"notifications:{user_id}")

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message["type"] == "message":
                await websocket.send_text(message["data"])
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(f"notifications:{user_id}")


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(service="notification_service")
