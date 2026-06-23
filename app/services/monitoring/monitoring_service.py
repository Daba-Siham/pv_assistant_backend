from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_user_id_from_token
from app.models.monitoring_event import MonitoringEvent
from app.models.simulation_result import SimulationResult
from app.schemas.monitoring import (
    AlertResponse,
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
    EnergyPredictionRequest,
    EnergyPredictionResponse,
    MonitoringSimulationRequest,
    MonitoringSimulationResponse,
    MonitoringStatusResponse,
)
from app.services.monitoring.alert_service import AlertService
from app.services.monitoring.anomaly_detection_service import AnomalyDetectionService
from app.services.monitoring.prediction_service import PredictionService
from app.services.monitoring.simulation_service import SimulationService


class MonitoringService:
    def __init__(self, db: Session | None = None):
        self.db = db
        self.simulation_service = SimulationService()
        self.anomaly_service = AnomalyDetectionService()
        self.prediction_service = PredictionService()
        self.alert_service = AlertService(db=db)

    def simulate_system(
        self,
        request: MonitoringSimulationRequest,
        token: str | None = None
    ) -> MonitoringSimulationResponse:
        user_id = get_user_id_from_token(token) if token else None

        response = self.simulation_service.simulate(request)
        simulation_id = self._save_monitoring_simulation(request, response, user_id=user_id)

        if simulation_id is not None:
            response.simulation_id = simulation_id

        return response

    def get_system_status(
        self,
        simulation_id: int,
        token: str | None = None
    ) -> MonitoringStatusResponse:
        if self.db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Base de données non disponible."
            )

        user_id = get_user_id_from_token(token) if token else None

        query = self.db.query(MonitoringEvent).filter(MonitoringEvent.simulation_id == simulation_id)
        if user_id is not None:
            query = query.filter(MonitoringEvent.user_id == user_id)

        events = query.order_by(MonitoringEvent.timestamp.desc()).all()

        if not events:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Simulation introuvable."
            )

        last_event = events[0]
        alerts_count = len([event for event in events if event.event_type == "alert"])

        return MonitoringStatusResponse(
            simulation_id=simulation_id,
            current_status=last_event.system_status,
            battery_level_percent=last_event.battery_level_percent,
            current_production_kwh=last_event.production_kwh or 0,
            current_consumption_kwh=last_event.consumption_kwh or 0,
            last_update=last_event.timestamp,
            alerts_count=alerts_count
        )

    def detect_anomalies(
        self,
        request: AnomalyDetectionRequest,
        token: str | None = None
    ) -> AnomalyDetectionResponse:
        user_id = get_user_id_from_token(token) if token else None

        response = self.anomaly_service.detect(request)

        if response.alerts:
            saved_alerts = self.alert_service.save_alerts(response.alerts, user_id=user_id)
            response.alerts = saved_alerts
            if self.db is not None and user_id is not None:
                try:
                    from app.services.notification_service import send_notification

                    for alert in saved_alerts:
                        alert_type = getattr(alert, "alert_type", "") or ""
                        message = getattr(alert, "message", "") or ""
                        severity = getattr(alert, "severity", None)
                        is_battery_alert = "battery" in alert_type.lower() or "batterie" in message.lower()
                        if is_battery_alert and request.battery_level_percent is None:
                            continue
                        send_notification(
                            db=self.db,
                            user_id=user_id,
                            title="Alerte monitoring",
                            message=message or "Une alerte monitoring a été détectée.",
                            notification_type="monitoring_alert",
                            severity=severity,
                            payload={"url": "/monitoring", "alert_type": alert_type},
                        )
                except Exception:
                    pass

        return response

    def get_alerts(self, token: str | None = None) -> list[AlertResponse]:
        user_id = get_user_id_from_token(token) if token else None
        return self.alert_service.get_alerts(limit=50, user_id=user_id)

    def predict_energy(
        self,
        request: EnergyPredictionRequest,
        token: str | None = None
    ) -> EnergyPredictionResponse:
        return self.prediction_service.predict_energy(request)

    def _save_monitoring_simulation(
        self,
        request: MonitoringSimulationRequest,
        response: MonitoringSimulationResponse,
        user_id: int | None = None
    ) -> int | None:
        if self.db is None:
            return None

        try:
            simulation = SimulationResult(
                user_id=user_id,
                simulation_type="monitoring",
                daily_consumption_kwh=request.daily_consumption_kwh,
                panel_count=request.panel_count,
                total_power_kwp=request.total_power_kwp,
                battery_capacity_kwh=request.battery_capacity_kwh,
                input_data=request.model_dump(),
                recommendations=response.summary,
                status="completed"
            )

            self.db.add(simulation)
            self.db.commit()
            self.db.refresh(simulation)

            for point in response.data:
                event = MonitoringEvent(
                    user_id=user_id,
                    simulation_id=simulation.id,
                    event_type="data_point",
                    timestamp=point.timestamp,
                    production_kwh=point.production_kwh,
                    consumption_kwh=point.consumption_kwh,
                    battery_level_percent=point.battery_level_percent,
                    temperature=point.temperature,
                    system_status=point.system_status,
                    raw_data=point.model_dump()
                )
                self.db.add(event)

            for alert in response.alerts:
                event = MonitoringEvent(
                    user_id=user_id,
                    simulation_id=simulation.id,
                    event_type="alert",
                    timestamp=datetime.utcnow(),
                    system_status="alert",
                    alert_type=alert.get("alert_type"),
                    severity=alert.get("severity"),
                    message=alert.get("message"),
                    raw_data=alert
                )
                self.db.add(event)

            self.db.commit()
            return simulation.id

        except Exception:
            self.db.rollback()
            return None
