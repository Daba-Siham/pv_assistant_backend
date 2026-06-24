from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, status

from app.core.security import get_user_id_from_token
from app.dependencies import AuthToken, DBSession
from app.models.notification import Notification
from app.models.simulation_result import SimulationResult
from app.schemas.monitoring import (
    AlertResponse,
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
    EnergyPredictionRequest,
    EnergyPredictionResponse,
    MonitoringConfirmRequest,
    MonitoringCurrentAlertRequest,
    MonitoringSimulationRequest,
    MonitoringSimulationResponse,
    MonitoringStatusResponse,
)
from app.services.monitoring.monitoring_service import MonitoringService
from app.services.monitoring.user_simulation_service import UserSimulationService
from app.services.notification_service import send_notification

router = APIRouter()


def notify_monitoring_alerts_once(db, user_id: int, alerts: list, has_battery: bool):
    print("NOTIFY ALERTS CALLED user_id=", user_id, "alerts_count=", len(alerts or []))
    for alert in alerts or []:
        if isinstance(alert, dict):
            alert_type = alert.get("alert_type", "")
            message = alert.get("message", "")
            severity = alert.get("severity", "warning")
        else:
            alert_type = getattr(alert, "alert_type", "")
            message = getattr(alert, "message", "")
            severity = getattr(alert, "severity", "warning")

        if not message:
            continue

        print("ALERT TO NOTIFY =", alert_type, severity, message)

        text = f"{alert_type} {message}".lower()
        is_battery_alert = "battery" in text or "batterie" in text

        if is_battery_alert and not has_battery:
            print("SKIP BATTERY ALERT WITHOUT BATTERY =", message)
            continue

        existing = (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.notification_type == "monitoring_alert",
                Notification.message == message,
                Notification.created_at >= datetime.utcnow() - timedelta(hours=6),
            )
            .first()
        )

        if existing:
            print("SKIP DUPLICATE ALERT =", message)
            continue

        print("SEND MONITORING NOTIFICATION =", message)
        send_notification(
            db=db,
            user_id=user_id,
            title="Alerte monitoring",
            message=message,
            notification_type="monitoring_alert",
            severity=severity,
            payload={
                "url": "/monitoring",
                "alert_type": alert_type,
            },
        )
        print("MONITORING NOTIFICATION CREATED")


@router.post("/simulate", response_model=MonitoringSimulationResponse, status_code=status.HTTP_200_OK)
def simulate_monitoring(request: MonitoringSimulationRequest, db: DBSession, token: AuthToken):
    monitoring_service = MonitoringService(db=db)
    return monitoring_service.simulate_system(request=request, token=token)


@router.get("/status/{simulation_id}", response_model=MonitoringStatusResponse, status_code=status.HTTP_200_OK)
def get_system_status(simulation_id: int, db: DBSession, token: AuthToken):
    monitoring_service = MonitoringService(db=db)
    return monitoring_service.get_system_status(simulation_id=simulation_id, token=token)


@router.post("/detect-anomalies", response_model=AnomalyDetectionResponse, status_code=status.HTTP_200_OK)
def detect_anomalies(request: AnomalyDetectionRequest, db: DBSession, token: AuthToken):
    if token is None:
        raise HTTPException(status_code=401, detail="Token requis.")

    user_id = get_user_id_from_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token invalide.")

    monitoring_service = MonitoringService(db=db)
    response = monitoring_service.detect_anomalies(request=request, token=token)

    notify_monitoring_alerts_once(
        db=db,
        user_id=user_id,
        alerts=response.alerts or [],
        has_battery=request.battery_level_percent is not None,
    )

    return response


@router.post("/notify-current-alert")
def notify_current_alert(request: MonitoringCurrentAlertRequest, db: DBSession, token: AuthToken):
    if token is None:
        raise HTTPException(status_code=401, detail="Token requis.")

    user_id = get_user_id_from_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token invalide.")

    existing = (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.notification_type == "monitoring_alert",
            Notification.message == request.message,
            Notification.created_at >= datetime.utcnow() - timedelta(hours=6),
        )
        .order_by(Notification.created_at.desc())
        .first()
    )

    if existing and existing.sent_at is not None:
        return {
            "success": True,
            "status": "already_sent",
            "notification_id": existing.id,
        }

    if existing and existing.sent_at is None:
        from app.services.notification_service import send_web_push_to_user

        push_sent = send_web_push_to_user(
            db=db,
            user_id=user_id,
            title=existing.title,
            message=existing.message,
            payload=existing.payload or {
                "url": "/monitoring",
                "alert_type": request.alert_type,
            },
        )

        if push_sent:
            existing.sent_at = datetime.utcnow()
            db.add(existing)
            db.commit()
            db.refresh(existing)

        return {
            "success": True,
            "status": "resent" if push_sent else "created_not_sent",
            "notification_id": existing.id,
        }

    notification = send_notification(
        db=db,
        user_id=user_id,
        title="Alerte monitoring",
        message=request.message,
        notification_type="monitoring_alert",
        severity=request.severity,
        payload={
            "url": "/monitoring",
            "alert_type": request.alert_type,
        },
    )

    return {
        "success": True,
        "status": "created",
        "notification_id": notification.id,
        "sent": notification.sent_at is not None,
    }


@router.get("/alerts", response_model=list[AlertResponse], status_code=status.HTTP_200_OK)
def get_alerts(db: DBSession, token: AuthToken):
    monitoring_service = MonitoringService(db=db)
    return monitoring_service.get_alerts(token=token)


@router.post("/predict", response_model=EnergyPredictionResponse, status_code=status.HTTP_200_OK)
def predict_energy(request: EnergyPredictionRequest, db: DBSession, token: AuthToken):
    monitoring_service = MonitoringService(db=db)
    return monitoring_service.predict_energy(request=request, token=token)


@router.get("/my-simulation")
def get_my_simulation(token: AuthToken, db: DBSession):
    if token is None:
        raise HTTPException(status_code=401, detail="Token requis.")

    user_id = get_user_id_from_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token invalide.")

    service = UserSimulationService()
    simulation = service.get_simulation_by_user_id(user_id)

    if simulation is None:
        return {
            "user_id": user_id,
            "data": [],
            "alerts": [],
            "summary": {},
            "system_config": {},
            "message": "Aucune simulation disponible."
        }

    # Cherche UNIQUEMENT les rapports confirmés
    report = (
        db.query(SimulationResult)
        .filter(
            SimulationResult.user_id == user_id,
            SimulationResult.simulation_type == "confirmed"
        )
        .order_by(SimulationResult.created_at.desc())
        .first()
    )

    report_data = None
    has_battery = False
    if report:
        installation_type = report.installation_type or ""
        battery_capacity = report.battery_capacity_kwh or 0
        normalized_type = installation_type.lower().replace("_", "-")
        has_battery = (
            "hybride" in normalized_type
            or "hybrid" in normalized_type
            or "off-grid" in normalized_type
            or battery_capacity > 0
        )

        report_data = {
            "panels": report.panels_result or {},
            "battery": report.battery_result or {},
            "inverter": report.inverter_result or {},
            "installation": {
                "orientation": report.orientation,
                "tilt_angle": report.tilt_angle,
                "installation_type": report.installation_type,
            },
            "solar_data": report.solar_data or {},
            "cost": report.cost_result or {},
            "roi": report.roi_result or {},
            "location": report.city or "",
            "project_status": report.status or "",
            "recommendations": report.recommendations or [],
        }

    merged = service.merge_with_report(simulation, report_data)
    print("MONITORING MERGED ALERTS =", merged.get("alerts", []))
    print("MONITORING USER ID =", user_id)
    print("MONITORING HAS BATTERY =", has_battery)

    return {
        "user_id": user_id,
        "has_report": report is not None,
        **merged
    }


@router.post("/confirm")
def confirm_monitoring(
    request: MonitoringConfirmRequest,
    token: AuthToken,
    db: DBSession
):
    if token is None:
        raise HTTPException(status_code=401, detail="Token requis.")

    user_id = get_user_id_from_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token invalide.")

    # Supprimer ancien rapport confirmé si existe
    old = (
        db.query(SimulationResult)
        .filter(
            SimulationResult.user_id == user_id,
            SimulationResult.simulation_type == "confirmed"
        )
        .first()
    )
    if old:
        db.delete(old)
        db.commit()

    panels_result = request.panels_result or {}
    if request.panel_model is not None:
        panels_result = {**panels_result, "panel_model": request.panel_model}

    inverter_result = request.inverter_result or {}
    if request.inverter_model is not None:
        inverter_result = {**inverter_result, "inverter_model": request.inverter_model}

    battery_result = request.battery_result or {}
    battery_capacity = request.battery_capacity_kwh or 0
    if battery_capacity > 0:
        battery_result = {
            **battery_result,
            "required_capacity_kwh": battery_capacity,
            "battery_capacity_kwh": battery_capacity,
            "battery_count": battery_result.get("battery_count") or 1,
            "battery_type": (
                battery_result.get("battery_type")
                or request.battery_model
                or battery_result.get("battery_model")
                or "Batterie lithium LiFePO4"
            ),
            "battery_model": (
                request.battery_model
                or battery_result.get("battery_model")
                or battery_result.get("battery_type")
                or "Batterie lithium LiFePO4"
            ),
        }
    else:
        battery_result = {}

    # Sauvegarder nouveau rapport confirmé
    simulation = SimulationResult(
        user_id=user_id,
        simulation_type="confirmed",
        city=request.city,
        installation_type=request.installation_type,
        orientation=request.orientation,
        tilt_angle=request.tilt_angle,
        daily_consumption_kwh=request.daily_consumption_kwh,
        panel_count=request.panel_count,
        total_power_kwp=request.total_power_kwp,
        battery_capacity_kwh=request.battery_capacity_kwh,
        inverter_power_kw=request.inverter_power_kw,
        total_cost=request.total_cost,
        roi_years=request.roi_years,
        annual_saving=request.annual_saving,
        panels_result=panels_result,
        battery_result=battery_result,
        inverter_result=inverter_result,
        cost_result=request.cost_result,
        roi_result=request.roi_result,
        solar_data=request.solar_data,
        recommendations=request.recommendations,
        status="confirmed"
    )

    db.add(simulation)
    db.commit()
    db.refresh(simulation)

    try:
        send_notification(
            db=db,
            user_id=user_id,
            title="Simulation confirmée",
            message="Votre monitoring photovoltaïque est maintenant actif.",
            notification_type="simulation_confirmed",
            payload={"url": "/monitoring", "simulation_id": simulation.id},
        )
    except Exception as exc:
        print("MONITORING NOTIFICATION ERROR =", repr(exc))

    return {
        "success": True,
        "simulation_id": simulation.id,
        "user_id": user_id,
        "message": "Système confirmé et sauvegardé."
    }
