import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.models.notification import Notification, NotificationPreference, PushSubscription


def get_or_create_preferences(db: Session, user_id: int) -> NotificationPreference:
    preference = (
        db.query(NotificationPreference)
        .filter(NotificationPreference.user_id == user_id)
        .first()
    )
    if preference:
        return preference

    preference = NotificationPreference(user_id=user_id)
    db.add(preference)
    db.commit()
    db.refresh(preference)
    return preference


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notification_type: str,
    severity: str | None = None,
    payload: dict[str, Any] | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        severity=severity,
        payload=payload,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def _webpush_available() -> bool:
    return bool(
        settings.WEB_PUSH_VAPID_PRIVATE_KEY
        and settings.WEB_PUSH_VAPID_PUBLIC_KEY
        and settings.WEB_PUSH_VAPID_EMAIL
    )


def send_web_push_to_user(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    payload: dict[str, Any] | None = None,
) -> bool:
    print("WAAAAAAAAAAAAAAAAAAAAAAAAAAA : ")
    preference = get_or_create_preferences(db, user_id)
    if not preference.web_push_enabled or not _webpush_available():
        print("WEEEEEEEEEEEEEEEEEEEEEE : ")
        return False
    print("7SELTINIIIII : ")
    try:
        from pywebpush import WebPushException, webpush
        print("BIBLIOOOOOOOO : ")
    except ImportError:
        print("SIHAM MSKINAAAAAAAA : ")
        return False

    subscriptions = (
        db.query(PushSubscription)
        .filter(
            PushSubscription.user_id == user_id,
            PushSubscription.is_active.is_(True),
        )
        .all()
    )
    print("🔥 SUBSCRIPTIONS FOUND:", len(subscriptions))
    print("🔥 SUBSCRIPTIONS:", subscriptions)
    if not subscriptions:
        return False

    sent = False
    data = json.dumps({
        "title": title,
        "message": message,
        "payload": payload or {},
    })

    for subscription in subscriptions:
        print("📤 Sending push to:", subscription.endpoint)
        subscription_info = {
            "endpoint": subscription.endpoint,
            "keys": {
                "p256dh": subscription.p256dh,
                "auth": subscription.auth,
            },
        }
        try:
            print("📦 Payload:", data)
            webpush(
                subscription_info=subscription_info,
                data=data,
                vapid_private_key=settings.WEB_PUSH_VAPID_PRIVATE_KEY,
                vapid_claims={"sub": f"mailto:{settings.WEB_PUSH_VAPID_EMAIL}"},
            )
            sent = True
        except WebPushException as exc:
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            if status_code in (404, 410):
                subscription.is_active = False
                subscription.updated_at = datetime.utcnow()
                db.add(subscription)
        except Exception as e:
            import traceback
            print("❌ WEBPUSH FAILED:", e)
            print(traceback.format_exc())

    db.commit()
    return sent


def send_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notification_type: str,
    severity: str | None = None,
    payload: dict[str, Any] | None = None,
) -> Notification:
    notification = create_notification(
        db=db,
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        severity=severity,
        payload=payload,
    )

    preference = get_or_create_preferences(db, user_id)
    should_send = preference.web_push_enabled
    if notification_type == "monitoring_alert":
        should_send = should_send and preference.monitoring_alerts_enabled
    elif notification_type == "maintenance_reminder":
        should_send = should_send and preference.maintenance_alerts_enabled
    elif notification_type == "simulation_confirmed":
        should_send = should_send and preference.simulation_alerts_enabled
    if should_send and send_web_push_to_user(db, user_id, title, message, payload):
        notification.sent_at = datetime.utcnow()
        db.add(notification)
        db.commit()
        db.refresh(notification)

    return notification
