from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, status

from app.core.security import get_user_id_from_token
from app.dependencies import AuthToken, DBSession
from app.models.notification import Notification, NotificationPreference, PushSubscription
from app.schemas.notification import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    NotificationResponse,
    PushSubscriptionCreate,
    PushSubscriptionDelete,
)
from app.services.notification_service import get_or_create_preferences, send_notification

router = APIRouter()


def _current_user_id(token: AuthToken) -> int:
    if token is None:
        raise HTTPException(status_code=401, detail="Token requis.")
    user_id = get_user_id_from_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token invalide.")
    return user_id


@router.get("/preferences", response_model=NotificationPreferenceResponse)
def get_preferences(token: AuthToken, db: DBSession):
    user_id = _current_user_id(token)
    return get_or_create_preferences(db, user_id)


@router.put("/preferences", response_model=NotificationPreferenceResponse)
def update_preferences(
    request: NotificationPreferenceUpdate,
    token: AuthToken,
    db: DBSession,
):
    user_id = _current_user_id(token)
    preference = get_or_create_preferences(db, user_id)
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(preference, field, value)
    preference.updated_at = datetime.utcnow()
    db.add(preference)
    db.commit()
    db.refresh(preference)
    return preference


@router.post("/subscribe", response_model=NotificationPreferenceResponse, status_code=status.HTTP_200_OK)
def subscribe(
    request: PushSubscriptionCreate,
    http_request: Request,
    token: AuthToken,
    db: DBSession,
):
    user_id = _current_user_id(token)
    subscription = (
        db.query(PushSubscription)
        .filter(PushSubscription.endpoint == request.endpoint)
        .first()
    )
    user_agent = request.user_agent or http_request.headers.get("user-agent")
    if subscription:
        subscription.user_id = user_id
        subscription.p256dh = request.keys.p256dh
        subscription.auth = request.keys.auth
        subscription.user_agent = user_agent
        subscription.is_active = True
        subscription.updated_at = datetime.utcnow()
    else:
        subscription = PushSubscription(
            user_id=user_id,
            endpoint=request.endpoint,
            p256dh=request.keys.p256dh,
            auth=request.keys.auth,
            user_agent=user_agent,
            is_active=True,
        )
    db.add(subscription)

    preference = get_or_create_preferences(db, user_id)
    preference.web_push_enabled = True
    preference.updated_at = datetime.utcnow()
    db.add(preference)
    db.commit()
    db.refresh(preference)
    return preference


@router.post("/unsubscribe", response_model=NotificationPreferenceResponse)
def unsubscribe(
    request: PushSubscriptionDelete,
    token: AuthToken,
    db: DBSession,
):
    user_id = _current_user_id(token)
    subscription = (
        db.query(PushSubscription)
        .filter(
            PushSubscription.user_id == user_id,
            PushSubscription.endpoint == request.endpoint,
        )
        .first()
    )
    if subscription:
        subscription.is_active = False
        subscription.updated_at = datetime.utcnow()
        db.add(subscription)

    active_count = (
        db.query(PushSubscription)
        .filter(
            PushSubscription.user_id == user_id,
            PushSubscription.is_active.is_(True),
            PushSubscription.endpoint != request.endpoint,
        )
        .count()
    )
    preference = get_or_create_preferences(db, user_id)
    if active_count == 0:
        preference.web_push_enabled = False
    preference.updated_at = datetime.utcnow()
    db.add(preference)
    db.commit()
    db.refresh(preference)
    return preference


@router.get("", response_model=list[NotificationResponse])
def list_notifications(token: AuthToken, db: DBSession):
    user_id = _current_user_id(token)
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_as_read(notification_id: int, token: AuthToken, db: DBSession):
    user_id = _current_user_id(token)
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification introuvable.")
    notification.is_read = True
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


@router.post("/test", response_model=NotificationResponse)
def test_notification(token: AuthToken, db: DBSession):
    user_id = _current_user_id(token)
    return send_notification(
        db=db,
        user_id=user_id,
        title="SolarAI",
        message="Notification de test SolarAI.",
        notification_type="test",
        payload={"url": "/monitoring"},
    )

