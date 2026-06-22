from datetime import datetime

from sqlalchemy.orm import Session

from app.models.monitoring_event import MonitoringEvent
from app.schemas.monitoring import AlertResponse


class AlertService:
    def __init__(self, db: Session | None = None):
        self.db = db

    def create_alert(
        self,
        severity: str,
        alert_type: str,
        message: str,
        probable_cause: str | None = None,
        recommended_action: str | None = None,
        user_id: int | None = None,
        simulation_id: int | None = None
    ) -> AlertResponse:
        alert = AlertResponse(
            id=None,
            severity=severity,
            alert_type=alert_type,
            message=message,
            probable_cause=probable_cause,
            recommended_action=recommended_action,
            created_at=datetime.utcnow()
        )

        if self.db is not None:
            monitoring_event = MonitoringEvent(
                user_id=user_id,
                simulation_id=simulation_id,
                event_type="alert",
                timestamp=datetime.utcnow(),
                system_status="alert",
                alert_type=alert_type,
                severity=severity,
                message=message,
                probable_cause=probable_cause,
                recommended_action=recommended_action
            )

            self.db.add(monitoring_event)
            self.db.commit()
            self.db.refresh(monitoring_event)

            alert.id = monitoring_event.id
            alert.created_at = monitoring_event.created_at

        return alert

    def save_alerts(
        self,
        alerts: list[AlertResponse],
        user_id: int | None = None,
        simulation_id: int | None = None
    ) -> list[AlertResponse]:
        saved_alerts = []

        for alert in alerts:
            saved_alert = self.create_alert(
                severity=alert.severity,
                alert_type=alert.alert_type,
                message=alert.message,
                probable_cause=alert.probable_cause,
                recommended_action=alert.recommended_action,
                user_id=user_id,
                simulation_id=simulation_id
            )
            saved_alerts.append(saved_alert)

        return saved_alerts

    def get_alerts(self, limit: int = 50, user_id: int | None = None) -> list[AlertResponse]:
        if self.db is None:
            return []

        query = self.db.query(MonitoringEvent).filter(MonitoringEvent.event_type == "alert")

        if user_id is not None:
            query = query.filter(MonitoringEvent.user_id == user_id)

        events = query.order_by(MonitoringEvent.created_at.desc()).limit(limit).all()

        return [
            AlertResponse(
                id=event.id,
                severity=event.severity or "info",
                alert_type=event.alert_type or "unknown",
                message=event.message or "",
                probable_cause=event.probable_cause,
                recommended_action=event.recommended_action,
                created_at=event.created_at
            )
            for event in events
        ]