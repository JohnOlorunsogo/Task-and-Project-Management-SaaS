"""Notification Service - Business Logic & Kafka Event Handlers."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any, Optional

import redis.asyncio as redis
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from shared.events import (
    COMMENT_ADDED, TASK_ASSIGNED, TASK_CREATED,
    TASK_STATUS_CHANGED, PROJECT_MEMBER_ADDED,
)

from app.models import Notification, NotificationPreference
from app.schemas import NotificationPreferenceResponse, NotificationResponse, UpdatePreferencesRequest

logger = logging.getLogger("notification_service")


class NotificationService:
    """Notification business logic."""

    def __init__(self, db: AsyncSession, redis_client: redis.Redis) -> None:
        self.db = db
        self.redis = redis_client

    async def list_notifications(
        self, user_id: str, unread_only: bool = False, limit: int = 50
    ) -> list[NotificationResponse]:
        stmt = select(Notification).where(
            Notification.user_id == uuid.UUID(user_id)
        )
        if unread_only:
            stmt = stmt.where(Notification.is_read == False)  # noqa
        stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)

        result = await self.db.execute(stmt)
        return [NotificationResponse.model_validate(n) for n in result.scalars().all()]

    async def mark_read(self, notification_id: uuid.UUID, user_id: str) -> None:
        stmt = (
            update(Notification)
            .where(
                Notification.id == notification_id,
                Notification.user_id == uuid.UUID(user_id),
            )
            .values(is_read=True)
        )
        await self.db.execute(stmt)
        await self.db.flush()

    async def mark_all_read(self, user_id: str) -> None:
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == uuid.UUID(user_id),
                Notification.is_read == False,  # noqa
            )
            .values(is_read=True)
        )
        await self.db.execute(stmt)
        await self.db.flush()

    async def get_unread_count(self, user_id: str) -> int:
        from sqlalchemy import func as sqlfunc
        stmt = select(sqlfunc.count()).select_from(Notification).where(
            Notification.user_id == uuid.UUID(user_id),
            Notification.is_read == False,  # noqa
        )
        return await self.db.scalar(stmt) or 0

    async def get_preferences(self, user_id: str) -> NotificationPreferenceResponse:
        stmt = select(NotificationPreference).where(
            NotificationPreference.user_id == uuid.UUID(user_id)
        )
        result = await self.db.execute(stmt)
        pref = result.scalar_one_or_none()
        if not pref:
            pref = NotificationPreference(user_id=uuid.UUID(user_id))
            self.db.add(pref)
            await self.db.flush()
        return NotificationPreferenceResponse.model_validate(pref)

    async def update_preferences(
        self, user_id: str, data: UpdatePreferencesRequest
    ) -> NotificationPreferenceResponse:
        stmt = select(NotificationPreference).where(
            NotificationPreference.user_id == uuid.UUID(user_id)
        )
        result = await self.db.execute(stmt)
        pref = result.scalar_one_or_none()
        if not pref:
            pref = NotificationPreference(user_id=uuid.UUID(user_id))
            self.db.add(pref)
            await self.db.flush()

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(pref, field, value)
        await self.db.flush()

        return NotificationPreferenceResponse.model_validate(pref)

    async def create_notification(
        self, user_id: str, org_id: str, type_: str, title: str, message: str,
        data: Optional[dict] = None,
    ) -> None:
        notif = Notification(
            user_id=uuid.UUID(user_id),
            org_id=uuid.UUID(org_id),
            type=type_,
            title=title,
            message=message,
            data=data,
        )
        self.db.add(notif)
        await self.db.flush()

        # Publish to Redis for real-time WebSocket delivery
        await self.redis.publish(
            f"notifications:{user_id}",
            json.dumps({
                "id": str(notif.id),
                "type": type_,
                "title": title,
                "message": message,
                "data": data,
            }),
        )


# =============================================================================
# Kafka Event Handlers
# =============================================================================

async def handle_task_assigned(event: dict[str, Any], session_factory, redis_client: redis.Redis) -> None:
    """Create notification when a task is assigned."""
    async with session_factory() as db:
        svc = NotificationService(db, redis_client)
        await svc.create_notification(
            user_id=event["user_id"],
            org_id=event.get("org_id", ""),
            type_=TASK_ASSIGNED,
            title="Task Assigned",
            message=f"You have been assigned to a task",
            data={"task_id": event["task_id"]},
        )
        await db.commit()


async def handle_comment_added(event: dict[str, Any], session_factory, redis_client: redis.Redis) -> None:
    """Create notifications for @mentions in comments."""
    mentions = event.get("mentions", [])
    if not mentions:
        return

    async with session_factory() as db:
        svc = NotificationService(db, redis_client)
        for user_id in mentions:
            await svc.create_notification(
                user_id=user_id,
                org_id=event.get("org_id", ""),
                type_=COMMENT_ADDED,
                title="You were mentioned",
                message=f"You were mentioned in a comment",
                data={"task_id": event["task_id"], "comment_id": event["comment_id"]},
            )
        await db.commit()


async def handle_task_status_changed(event: dict[str, Any], session_factory, redis_client: redis.Redis) -> None:
    """Notify assignees of status changes."""
    async with session_factory() as db:
        svc = NotificationService(db, redis_client)
        await svc.create_notification(
            user_id=event.get("actor_id", ""),
            org_id=event.get("org_id", ""),
            type_=TASK_STATUS_CHANGED,
            title="Task Status Changed",
            message=f"Task status changed from '{event.get('old_status')}' to '{event.get('new_status')}'",
            data={"task_id": event["task_id"]},
        )
        await db.commit()
