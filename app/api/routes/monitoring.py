from fastapi import APIRouter, status

from app.dependencies import DBSession, AuthToken
from app.schemas.monitoring import (
    MonitoringSimulationRequest,
    MonitoringSimulationResponse,
    MonitoringStatusResponse,
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
    AlertResponse,
    EnergyPredictionRequest,
    EnergyPredictionResponse,
    MonitoringConfirmRequest, 
)
from app.services.monitoring.monitoring_service import MonitoringService
from app.services.monitoring.user_simulation_service import UserSimulationService
from app.core.security import get_user_id_from_token

router = APIRouter()


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
    monitoring_service = MonitoringService(db=db)
    return monitoring_service.detect_anomalies(request=request, token=token)


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
    from fastapi import HTTPException
    from app.models.simulation_result import SimulationResult

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
    if report:
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
    from fastapi import HTTPException
    from app.models.simulation_result import SimulationResult

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
    if request.battery_model is not None:
        battery_result = {**battery_result, "battery_model": request.battery_model}

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
        from app.services.notification_service import send_notification

        send_notification(
            db=db,
            user_id=user_id,
            title="Simulation confirmée",
            message="Votre monitoring photovoltaïque est maintenant actif.",
            notification_type="simulation_confirmed",
            payload={"url": "/monitoring", "simulation_id": simulation.id},
        )
    except Exception:
        pass

    return {
        "success": True,
        "simulation_id": simulation.id,
        "user_id": user_id,
        "message": "Système confirmé et sauvegardé."
    }
