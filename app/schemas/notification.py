from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class NotificationPreferenceResponse(BaseModel):
    web_push_enabled: bool = False
    monitoring_alerts_enabled: bool = True
    maintenance_alerts_enabled: bool = True
    simulation_alerts_enabled: bool = True

    class Config:
        from_attributes = True


class NotificationPreferenceUpdate(BaseModel):
    web_push_enabled: bool | None = None
    monitoring_alerts_enabled: bool | None = None
    maintenance_alerts_enabled: bool | None = None
    simulation_alerts_enabled: bool | None = None


class PushSubscriptionKeys(BaseModel):
    p256dh: str = Field(..., min_length=1)
    auth: str = Field(..., min_length=1)


class PushSubscriptionCreate(BaseModel):
    endpoint: str = Field(..., min_length=1)
    keys: PushSubscriptionKeys
    user_agent: str | None = None


class PushSubscriptionDelete(BaseModel):
    endpoint: str = Field(..., min_length=1)


class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    notification_type: str
    severity: str | None = None
    payload: dict[str, Any] | None = None
    is_read: bool = False
    sent_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True
