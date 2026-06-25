from datetime import datetime
from pathlib import Path
import re

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.core.security import get_user_id_from_token
from app.dependencies import AuthToken, DBSession
from app.models.simulation_result import SimulationResult
from app.schemas.recommendation import (
    PVRecommendationRequest,
    PVRecommendationResponse,
    SaveRecommendationRequest,
)
from app.services.recommendation import PVRecommendationService
from pdf.generator import generate_recommendation_pdf_report

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parents[3]
LAST_GENERATED_PDF = {"path": None, "filename": None}


def get_nested(data: dict, *paths: str, default=None):
    for path in paths:
        current = data
        for key in path.split("."):
            if not isinstance(current, dict):
                current = None
                break
            current = current.get(key)
        if current not in (None, "", []):
            return current
    return default


def parse_numbers(text):
    if text is None:
        return []
    if isinstance(text, (int, float)):
        return [float(text)]

    cleaned = str(text).replace("\u00a0", " ").replace(",", ".")
    matches = re.findall(r"\d+(?:\s?\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?", cleaned)
    values = []
    for match in matches:
        try:
            values.append(float(match.replace(" ", "")))
        except ValueError:
            continue
    return values


def parse_average(text, default=0):
    values = parse_numbers(text)
    if not values:
        return default
    if len(values) >= 2:
        return sum(values[:2]) / 2
    return values[0]


def parse_upper(text, default=0):
    values = parse_numbers(text)
    if not values:
        return default
    return max(values)


def parse_first(text, default=0):
    values = parse_numbers(text)
    if not values:
        return default
    return values[0]


def normalize_installation_type(value) -> str:
    return str(value or "").strip().lower().replace("-", "_")


def get_default_panel_model() -> str:
    return "Panneaux monocristallins performants — Jinko Solar / LONGi / Canadian Solar"


def get_default_inverter_model(installation_type) -> str:
    normalized = normalize_installation_type(installation_type)
    if "hybrid" in normalized or "hybride" in normalized:
        return "Onduleur hybride — Huawei / SMA / Fronius"
    if "off" in normalized:
        return "Onduleur off-grid — Victron Energy / Growatt / SMA"
    return "Onduleur on-grid — Huawei / SMA / Fronius"


def should_suggest_battery(installation_type, autonomy_days) -> bool:
    normalized = normalize_installation_type(installation_type)
    return (
        "hybrid" in normalized
        or "hybride" in normalized
        or "off" in normalized
        or float(autonomy_days or 0) > 0
    )


def get_default_battery_model(installation_type, autonomy_days) -> str:
    if not should_suggest_battery(installation_type, autonomy_days):
        return "Batterie non nécessaire pour ce système"
    return "Batterie lithium LiFePO4 — Pylontech / BYD / Huawei Luna"


@router.post("/pv", response_model=PVRecommendationResponse, status_code=status.HTTP_200_OK)
def generate_pv_recommendation(
    request: PVRecommendationRequest,
    db: DBSession,
):
    service = PVRecommendationService(db=db)
    return service.generate(request)


@router.post("/pdf", status_code=status.HTTP_200_OK)
def generate_pv_recommendation_pdf(
    request: PVRecommendationRequest,
    db: DBSession,
):
    service = PVRecommendationService(db=db)
    result = service.generate(request).model_dump(mode="json")

    reports_dir = BASE_DIR / "generated_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"rapport_recommandation_pv_{timestamp}.pdf"
    filepath = reports_dir / filename

    generate_recommendation_pdf_report(
        filename=str(filepath),
        recommendation_result=result,
    )

    LAST_GENERATED_PDF["path"] = str(filepath)
    LAST_GENERATED_PDF["filename"] = filename

    return FileResponse(
        path=str(filepath),
        media_type="application/pdf",
        filename=filename,
    )


@router.post("/save", status_code=status.HTTP_200_OK)
def save_pv_recommendation(
    request: SaveRecommendationRequest,
    db: DBSession,
    token: AuthToken,
):
    if token is None:
        raise HTTPException(status_code=401, detail="Token requis.")

    user_id = get_user_id_from_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token invalide.")

    result_data = request.result_data or {}
    input_data = request.input_data or {}
    formatted = (
        result_data.get("formatted_recommendation", {})
        .get("user_friendly_recommendation", {})
        or {}
    )
    installation_type = request.installation_type or input_data.get("installation_type")
    autonomy_days = input_data.get("autonomy_days")

    battery_text = formatted.get("battery")

    panel_count = get_nested(
        result_data,
        "panels.panel_count",
        "ml_recommendation.panel_count",
        "ml_recommendation.n_panels",
        "ml_recommendation.number_of_panels",
        default=None,
    )
    if not panel_count:
        panel_count = round(parse_upper(formatted.get("panels"), 0))

    panel_power_w = get_nested(
        result_data,
        "panels.panel_power_w",
        "ml_recommendation.panel_power_w",
        default=575,
    )

    total_power_kwp = get_nested(
        result_data,
        "panels.total_power_kwp",
        "ml_recommendation.total_power_kwp",
        "ml_recommendation.pv_power_kwp",
        default=None,
    )
    if not total_power_kwp:
        total_power_kwp = parse_average(formatted.get("power"), 0)

    estimated_daily_production_kwh = get_nested(
        result_data,
        "panels.estimated_daily_production_kwh",
        "ml_recommendation.estimated_daily_production_kwh",
        "ml_recommendation.daily_production_kwh",
        default=0,
    )
    battery_capacity_kwh = get_nested(
        result_data,
        "battery.required_capacity_kwh",
        "battery.battery_capacity_kwh",
        "ml_recommendation.battery_capacity_kwh",
        "ml_recommendation.required_battery_capacity_kwh",
        default=0,
    )
    inverter_power_kw = get_nested(
        result_data,
        "inverter.recommended_power_kw",
        "inverter.inverter_power_kw",
        "ml_recommendation.inverter_power_kw",
        "ml_recommendation.recommended_inverter_power_kw",
        default=None,
    )
    if not inverter_power_kw:
        inverter_power_kw = parse_average(formatted.get("inverter"), 0)

    total_cost = get_nested(
        result_data,
        "cost.total_cost",
        "ml_recommendation.estimated_total_cost_dh",
        "ml_recommendation.estimated_cost",
        "ml_recommendation.total_cost",
        default=None,
    )
    if not total_cost:
        total_cost = parse_average(formatted.get("budget_estimation"), 0)

    annual_saving = get_nested(
        result_data,
        "roi.yearly_savings",
        "roi.annual_saving",
        "ml_recommendation.annual_saving",
        "ml_recommendation.yearly_savings",
        default=0,
    )
    roi_years = get_nested(
        result_data,
        "roi.roi_years",
        "ml_recommendation.roi_years",
        default=None,
    )
    if not roi_years:
        roi_years = parse_first(formatted.get("roi"), 0)

    panel_model = get_nested(
        result_data,
        "panels.panel_model",
        "ml_recommendation.panel_model",
        default="",
    ) or get_default_panel_model()
    inverter_model = get_nested(
        result_data,
        "inverter.inverter_model",
        "ml_recommendation.inverter_model",
        default="",
    ) or get_default_inverter_model(installation_type)
    battery_model = get_nested(
        result_data,
        "battery.battery_model",
        "ml_recommendation.battery_model",
        default="",
    ) or get_default_battery_model(installation_type, autonomy_days)

    simulation = SimulationResult(
        user_id=user_id,
        simulation_type="dimensioning",
        city=request.city or input_data.get("city") or result_data.get("location"),
        daily_consumption_kwh=request.daily_consumption_kwh or input_data.get("daily_consumption_kwh"),
        available_area_m2=request.available_area_m2 or input_data.get("available_area_m2"),
        budget=request.budget or input_data.get("budget"),
        autonomy_days=autonomy_days,
        installation_type=installation_type,
        orientation=request.orientation or input_data.get("orientation"),
        tilt_angle=request.tilt_angle or input_data.get("tilt_angle"),
        roof_type=request.roof_type or input_data.get("roof_type"),
        panel_count=int(panel_count or 0),
        panel_power_w=float(panel_power_w or 575),
        total_power_kwp=float(total_power_kwp or 0),
        estimated_daily_production_kwh=float(estimated_daily_production_kwh or 0),
        battery_capacity_kwh=float(battery_capacity_kwh or 0),
        inverter_power_kw=float(inverter_power_kw or 0),
        total_cost=float(total_cost or 0),
        annual_saving=float(annual_saving or 0),
        roi_years=float(roi_years or 0),
        input_data=input_data,
        panels_result={
            "panel_count": int(panel_count or 0),
            "panel_power_w": float(panel_power_w or 575),
            "total_power_kwp": float(total_power_kwp or 0),
            "estimated_daily_production_kwh": float(estimated_daily_production_kwh or 0),
            "panel_model": panel_model,
            "display_text": formatted.get("panels"),
            "power_text": formatted.get("power"),
        },
        battery_result={
            "required_capacity_kwh": float(battery_capacity_kwh or 0),
            "battery_capacity_kwh": float(battery_capacity_kwh or 0),
            "battery_model": battery_model,
            "display_text": battery_text,
        },
        inverter_result={
            "recommended_power_kw": float(inverter_power_kw or 0),
            "inverter_power_kw": float(inverter_power_kw or 0),
            "inverter_model": inverter_model,
            "display_text": formatted.get("inverter"),
        },
        cost_result={
            "total_cost": float(total_cost or 0),
            "display_text": formatted.get("budget_estimation"),
        },
        roi_result={
            "roi_years": float(roi_years or 0),
            "yearly_savings": float(annual_saving or 0),
            "annual_saving": float(annual_saving or 0),
            "display_text": formatted.get("roi"),
        },
        recommendations=request.recommendations or result_data.get("formatted_recommendation"),
        assumptions={
            **(request.assumptions or {}),
            "result_data": result_data,
            "formatted_recommendation": formatted,
        },
        status="saved",
    )

    db.add(simulation)
    pdf_path = LAST_GENERATED_PDF.get("path")
    pdf_filename = LAST_GENERATED_PDF.get("filename")
    if pdf_path and pdf_filename:
        simulation.report_pdf_path = pdf_path
        simulation.report_pdf_filename = pdf_filename
    db.commit()
    db.refresh(simulation)

    return {
        "success": True,
        "simulation_id": simulation.id,
        "message": "Simulation sauvegardée avec succès",
    }


@router.get("/latest-saved", status_code=status.HTTP_200_OK)
def get_latest_saved_recommendation(db: DBSession, token: AuthToken):
    if token is None:
        raise HTTPException(status_code=401, detail="Token requis.")

    user_id = get_user_id_from_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token invalide.")

    simulation = (
        db.query(SimulationResult)
        .filter(
            SimulationResult.user_id == user_id,
            SimulationResult.status.in_(["saved", "draft"]),
        )
        .order_by(SimulationResult.created_at.desc())
        .first()
    )

    if not simulation:
        return {"success": False, "message": "Aucune simulation sauvegardée"}

    return {
        "success": True,
        "simulation": {
            "id": simulation.id,
            "city": simulation.city,
            "daily_consumption_kwh": simulation.daily_consumption_kwh,
            "available_area_m2": simulation.available_area_m2,
            "budget": simulation.budget,
            "installation_type": simulation.installation_type,
            "orientation": simulation.orientation,
            "tilt_angle": simulation.tilt_angle,
            "roof_type": simulation.roof_type,
            "panel_count": simulation.panel_count,
            "panel_power_w": simulation.panel_power_w,
            "total_power_kwp": simulation.total_power_kwp,
            "estimated_daily_production_kwh": simulation.estimated_daily_production_kwh,
            "battery_capacity_kwh": simulation.battery_capacity_kwh,
            "inverter_power_kw": simulation.inverter_power_kw,
            "total_cost": simulation.total_cost,
            "annual_saving": simulation.annual_saving,
            "roi_years": simulation.roi_years,
            "input_data": simulation.input_data,
            "panels": simulation.panels_result or {},
            "battery": simulation.battery_result or {},
            "inverter": simulation.inverter_result or {},
            "cost": simulation.cost_result or {},
            "roi": simulation.roi_result or {},
            "recommendations": simulation.recommendations,
            "assumptions": simulation.assumptions,
            "created_at": simulation.created_at,
            "status": simulation.status,
        },
    }
