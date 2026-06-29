from pathlib import Path
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import case

from app.core.security import get_user_id_from_token
from app.dependencies import AuthToken, DBSession
from app.models.simulation_result import SimulationResult

router = APIRouter()


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
                "report_pdf_path": report.report_pdf_path,
                "report_pdf_filename": report.report_pdf_filename,
                "has_pdf": bool(report.report_pdf_path),
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


def _find_report_pdf_by_filename(filename: str | None) -> Path | None:
    if not filename:
        return None

    reports_dir = Path(__file__).resolve().parents[3] / "generated_reports"
    if not reports_dir.exists():
        return None

    direct_path = reports_dir / filename
    if direct_path.exists():
        return direct_path

    matches = [path for path in reports_dir.rglob(filename) if path.is_file()]
    if not matches:
        return None

    return sorted(matches, key=lambda path: str(path))[0]


def _parse_report_pdf_timestamp(pdf_path: Path) -> datetime | None:
    stem = pdf_path.stem
    prefix = "rapport_recommandation_pv_"
    if not stem.startswith(prefix):
        return None

    timestamp_text = stem[len(prefix):]
    try:
        return datetime.strptime(timestamp_text, "%Y%m%d_%H%M%S")
    except ValueError:
        return None


def _find_report_pdf_by_created_at(report: SimulationResult) -> Path | None:
    reports_dir = Path(__file__).resolve().parents[3] / "generated_reports"
    if not reports_dir.exists():
        return None

    created_at = report.created_at
    if created_at is None:
        return None

    matches: list[tuple[float, Path]] = []
    for pdf_path in reports_dir.rglob("rapport_recommandation_pv_*.pdf"):
        if not pdf_path.is_file():
            continue
        pdf_timestamp = _parse_report_pdf_timestamp(pdf_path)
        if pdf_timestamp is None:
            continue
        delta = abs((pdf_timestamp - created_at).total_seconds())
        if delta <= timedelta(minutes=10).total_seconds():
            matches.append((delta, pdf_path))

    if len(matches) != 1:
        return None

    return matches[0][1]


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
    print("OPEN REPORT ID =", report_id)
    print("OPEN REPORT PDF PATH =", report.report_pdf_path)
    print("OPEN REPORT PDF FILENAME =", report.report_pdf_filename)

    pdf_path = Path(report.report_pdf_path) if report.report_pdf_path else None
    if not pdf_path or not pdf_path.exists():
        fallback_path = _find_report_pdf_by_filename(report.report_pdf_filename)
        if fallback_path is None:
            fallback_path = _find_report_pdf_by_created_at(report)
        if fallback_path:
            pdf_path = fallback_path
            report.report_pdf_path = str(pdf_path)
            report.report_pdf_filename = pdf_path.name
            db.commit()
            db.refresh(report)

    if pdf_path is None or not pdf_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF report is not linked to this saved report. Generate a new report or relink existing PDF.",
        )

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=report.report_pdf_filename or pdf_path.name,
    )
