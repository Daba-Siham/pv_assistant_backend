from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import case

from app.core.security import get_user_id_from_token
from app.dependencies import AuthToken, DBSession
from app.models.simulation_result import SimulationResult
from pdf.generator import generate_pdf_report

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parents[3]
REPORTS_DIR = BASE_DIR / "generated_reports"


def _normalize_city(city: str | None) -> str:
    value = str(city or "").strip()
    return value or "Unknown city"


def _get_report_type(simulation_type: str | None) -> str:
    normalized = str(simulation_type or "").strip().lower()
    if normalized == "confirmed":
        return "monitoring"
    if normalized == "dimensioning":
        return "dimensioning"
    return "simulation"


def _get_report_title(simulation_type: str | None, city: str | None) -> str:
    report_type = _get_report_type(simulation_type)
    safe_city = _normalize_city(city)

    if report_type == "monitoring":
        return f"Monitoring Report - {safe_city}"
    if report_type == "dimensioning":
        return f"Dimensioning Report - {safe_city}"
    return f"Simulation Report - {safe_city}"


def _safe_filename_part(value: str | None, default: str = "unknown") -> str:
    text = str(value or "").strip().lower()
    if not text:
        return default
    cleaned = []
    for char in text:
        if char.isalnum() or char in {"-", "_"}:
            cleaned.append(char)
        else:
            cleaned.append("_")
    return "".join(cleaned).strip("_") or default


def _get_report_file_path(user_id: int, report_type: str, report_id: int) -> Path:
    user_dir = REPORTS_DIR / f"user_{user_id}"
    user_dir.mkdir(parents=True, exist_ok=True)
    filename = f"solarai_user_{user_id}_{_safe_filename_part(report_type)}_report_{report_id}.pdf"
    return user_dir / filename


def _build_pdf_payload_from_report(report: SimulationResult) -> dict:
    return {
        "input_data": report.input_data or {},
        "solar_data": report.solar_data or {},
        "panels_result": report.panels_result or {},
        "battery_result": report.battery_result or {},
        "inverter_result": report.inverter_result or {},
        "cost_result": report.cost_result or {},
        "roi_result": report.roi_result or {},
        "cable_result": report.cable_result or {},
        "stores_result": report.stores_result or {},
        "recommendations": report.recommendations or {},
        "assumptions": report.assumptions or {},
        "city": report.city,
        "installation_type": report.installation_type,
        "panel_count": report.panel_count,
        "total_power_kwp": report.total_power_kwp,
        "battery_capacity_kwh": report.battery_capacity_kwh,
        "inverter_power_kw": report.inverter_power_kw,
        "total_cost": report.total_cost,
        "roi_years": report.roi_years,
        "created_at": report.created_at.isoformat() if report.created_at else None,
    }


def _build_pdf_user_data(report: SimulationResult) -> dict:
    return {
        "city": report.city or "Unknown city",
        "installation_type": report.installation_type or "-",
        "daily_consumption_kwh": report.daily_consumption_kwh or 0,
        "orientation": report.orientation or "-",
        "client_name": f"User {report.user_id}" if report.user_id is not None else "Client",
    }


def _build_pdf_results_from_report(report: SimulationResult) -> dict:
    panels_result = report.panels_result or {}
    battery_result = report.battery_result or {}
    inverter_result = report.inverter_result or {}
    cost_result = report.cost_result or {}
    roi_result = report.roi_result or {}

    return {
        "panels": {
            "panel_count": report.panel_count or panels_result.get("panel_count", 0),
            "panel_power_w": report.panel_power_w or panels_result.get("panel_power_w", 0),
            "total_power_kwp": report.total_power_kwp or panels_result.get("total_power_kwp", 0),
            "estimated_daily_production_kwh": panels_result.get(
                "estimated_daily_production_kwh",
                report.estimated_daily_production_kwh or 0,
            ),
            "panel_model": panels_result.get("panel_model", "-"),
            "panel_brand": panels_result.get("panel_brand", "-"),
        },
        "battery": {
            "battery_count": battery_result.get("battery_count", 0),
            "battery_type": battery_result.get("battery_type", "-"),
            "battery_model": battery_result.get("battery_model", "-"),
            "required_capacity_kwh": report.battery_capacity_kwh or battery_result.get("required_capacity_kwh", 0),
            "battery_capacity_kwh": report.battery_capacity_kwh or battery_result.get("battery_capacity_kwh", 0),
        },
        "inverter": {
            "inverter_model": inverter_result.get("inverter_model", "-"),
            "recommended_power_kw": report.inverter_power_kw or inverter_result.get("recommended_power_kw", 0),
            "inverter_type": inverter_result.get("inverter_type", report.installation_type or "-"),
            "description": inverter_result.get("description", "-"),
        },
        "cost": {
            "total_cost": report.total_cost or cost_result.get("total_cost", 0),
            "panels_cost": cost_result.get("panels_cost", 0),
            "battery_cost": cost_result.get("battery_cost", 0),
            "inverter_cost": cost_result.get("inverter_cost", 0),
            "installation_cost": cost_result.get("installation_cost", 0),
            "panel_unit_price": cost_result.get("panel_unit_price", 0),
            "battery_unit_price": cost_result.get("battery_unit_price", 0),
            "inverter_unit_price": cost_result.get("inverter_unit_price", 0),
            "installation_cost_per_kw": cost_result.get("installation_cost_per_kw", 0),
        },
        "roi": {
            "roi_years": report.roi_years or roi_result.get("roi_years", 0),
            "yearly_savings": roi_result.get("yearly_savings", roi_result.get("annual_saving", report.annual_saving or 0)),
            "annual_saving": roi_result.get("annual_saving", report.annual_saving or 0),
        },
        "installation": {
            "orientation": report.orientation or "-",
            "tilt_angle": report.tilt_angle or 0,
        },
        "solar_data": report.solar_data or {},
        "recommendations": report.recommendations or [],
        "ai_analysis": {},
        "environment": {},
        "performance": {},
        "project_status": report.status or "-",
    }


def _generate_report_pdf(report: SimulationResult, output_path: Path) -> None:
    generate_pdf_report(
        filename=str(output_path),
        user_data=_build_pdf_user_data(report),
        results=_build_pdf_results_from_report(report),
    )


def _serialize_report(report: SimulationResult, include_extras: bool = False) -> dict:
    report_type = _get_report_type(report.simulation_type)
    city = _normalize_city(report.city)

    payload = {
        "id": report.id,
        "user_id": report.user_id,
        "simulation_type": report.simulation_type,
        "report_type": report_type,
        "title": _get_report_title(report.simulation_type, report.city),
        "city": city,
        "installation_type": report.installation_type,
        "panel_count": report.panel_count,
        "total_power_kwp": report.total_power_kwp,
        "battery_capacity_kwh": report.battery_capacity_kwh,
        "inverter_power_kw": report.inverter_power_kw,
        "total_cost": report.total_cost,
        "roi_years": report.roi_years,
        "status": report.status,
        "created_at": report.created_at,
        "pdf_url": f"/api/v1/reports/{report.id}/pdf",
    }

    if include_extras:
        # Keep the detail route broad so future UI work can reuse it without another backend change.
        payload.update(
            {
                "latitude": report.latitude,
                "longitude": report.longitude,
                "daily_consumption_kwh": report.daily_consumption_kwh,
                "available_area_m2": report.available_area_m2,
                "budget": report.budget,
                "autonomy_days": report.autonomy_days,
                "orientation": report.orientation,
                "tilt_angle": report.tilt_angle,
                "shade_factor": report.shade_factor,
                "roof_type": report.roof_type,
                "distance_to_load_m": report.distance_to_load_m,
                "ghi": report.ghi,
                "dni": report.dni,
                "temperature_avg": report.temperature_avg,
                "peak_sun_hours": report.peak_sun_hours,
                "panel_power_w": report.panel_power_w,
                "estimated_daily_production_kwh": report.estimated_daily_production_kwh,
                "required_area_m2": report.required_area_m2,
                "battery_capacity_ah": report.battery_capacity_ah,
                "battery_needed": report.battery_needed,
                "cable_section_mm2": report.cable_section_mm2,
                "input_data": report.input_data or {},
                "solar_data": report.solar_data or {},
                "panels_result": report.panels_result or {},
                "battery_result": report.battery_result or {},
                "inverter_result": report.inverter_result or {},
                "cost_result": report.cost_result or {},
                "roi_result": report.roi_result or {},
                "cable_result": report.cable_result or {},
                "stores_result": report.stores_result or {},
                "recommendations": report.recommendations or {},
                "assumptions": report.assumptions or {},
                "error_message": report.error_message,
            }
        )

    return payload


def _get_connected_user_id(token: str | None) -> int:
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requis.")

    user_id = get_user_id_from_token(token)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide.")

    return user_id


def _get_owned_report(db, report_id: int, user_id: int) -> SimulationResult:
    report = (
        db.query(SimulationResult)
        .filter(
            SimulationResult.id == report_id,
            SimulationResult.user_id == user_id,
        )
        .first()
    )

    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rapport introuvable.")

    return report


@router.get("/my-reports", status_code=status.HTTP_200_OK)
def list_my_reports(db: DBSession, token: AuthToken):
    user_id = _get_connected_user_id(token)

    reports = (
        db.query(SimulationResult)
        .filter(SimulationResult.user_id == user_id)
        .order_by(
            case((SimulationResult.simulation_type == "confirmed", 0), else_=1),
            SimulationResult.created_at.desc(),
        )
        .all()
    )

    return [_serialize_report(report) for report in reports]


@router.get("/{report_id}", status_code=status.HTTP_200_OK)
def get_report(report_id: int, db: DBSession, token: AuthToken):
    user_id = _get_connected_user_id(token)
    report = _get_owned_report(db=db, report_id=report_id, user_id=user_id)
    return _serialize_report(report, include_extras=True)


@router.get("/{report_id}/pdf", status_code=status.HTTP_200_OK)
def get_report_pdf(report_id: int, db: DBSession, token: AuthToken):
    user_id = _get_connected_user_id(token)
    report = _get_owned_report(db=db, report_id=report_id, user_id=user_id)
    report_type = _get_report_type(report.simulation_type)
    output_path = _get_report_file_path(user_id=user_id, report_type=report_type, report_id=report.id)

    if not output_path.exists():
        _generate_report_pdf(report=report, output_path=output_path)

    return FileResponse(
        path=str(output_path),
        media_type="application/pdf",
        filename=output_path.name,
    )
