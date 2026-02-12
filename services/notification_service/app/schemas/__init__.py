"""Notification Service Pydantic Schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    org_id: uuid.UUID
    type: str
    title: str
    message: str
    data: Optional[dict[str, Any]]
    is_read: bool
    created_at: datetime


class NotificationPreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    email_on_assignment: bool
    email_on_mention: bool
    email_on_due_date: bool
    email_on_status_change: bool
    in_app_on_assignment: bool
    in_app_on_mention: bool
    in_app_on_due_date: bool
    in_app_on_status_change: bool


class UpdatePreferencesRequest(BaseModel):
    email_on_assignment: Optional[bool] = None
    email_on_mention: Optional[bool] = None
    email_on_due_date: Optional[bool] = None
    email_on_status_change: Optional[bool] = None
    in_app_on_assignment: Optional[bool] = None
    in_app_on_mention: Optional[bool] = None
    in_app_on_due_date: Optional[bool] = None
    in_app_on_status_change: Optional[bool] = None
