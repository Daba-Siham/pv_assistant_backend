from fastapi import APIRouter, status
from fastapi.responses import FileResponse
from pathlib import Path
from datetime import datetime

from app.dependencies import DBSession, AuthToken
from app.core.security import get_user_id_from_token
from app.models.user import User
from app.schemas.calculation import (
    CalculationRequest,
    CalculationResponse,
    PanelEstimationRequest,
    PanelEstimationResponse,
    BatteryEstimationRequest,
    BatteryEstimationResponse,
    InverterEstimationRequest,
    InverterEstimationResponse,
    CostEstimationRequest,
    CostEstimationResponse,
    ROIRequest,
    ROIResponse,
)
from app.services.calculation.calculation_service import CalculationService, calculate_system
from pdf.generator import generate_pdf_report

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]


def _resolve_client_name(db, token: AuthToken) -> str:
    fallback = "Client non renseigné"
    if token is None:
        return fallback

    user_id = get_user_id_from_token(token)
    if user_id is None:
        return fallback

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return fallback

    full_name = str(getattr(user, "full_name", "") or "").strip()
    if full_name:
        return full_name

    name = str(getattr(user, "name", "") or "").strip()
    if name:
        return name

    email = str(getattr(user, "email", "") or "").strip()
    if email:
        return email

    return fallback


@router.post("/", status_code=status.HTTP_200_OK)
def calculate_pv_system(request: CalculationRequest, db: DBSession, token: AuthToken):
    calculation_service = CalculationService(db=db)
    return calculation_service.calculate_complete_system(request=request, token=token)


@router.post("/pdf")
def generate_pdf(request: CalculationRequest, db: DBSession, token: AuthToken):
    data = calculate_system(request)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"rapport_solaire_{timestamp}.pdf"
    filepath = BASE_DIR / "generated_reports" / filename
    client_name = _resolve_client_name(db, token)
    generate_pdf_report(
        filename=str(filepath),
        user_data={
            "city": request.city,
            "installation_type": request.installation_type,
            "daily_consumption_kwh": request.daily_consumption_kwh,
            "orientation": request.orientation,
            "client_name": client_name,
        },
        results=data,
        client_name=client_name,
    )
    return FileResponse(
        path=str(filepath),
        media_type="application/pdf",
        filename=filename
    )


@router.post("/panels", response_model=PanelEstimationResponse, status_code=status.HTTP_200_OK)
def estimate_panels(request: PanelEstimationRequest):
    return CalculationService().estimate_panels(request)


@router.post("/batteries", response_model=BatteryEstimationResponse, status_code=status.HTTP_200_OK)
def estimate_batteries(request: BatteryEstimationRequest):
    return CalculationService().estimate_batteries(request)


@router.post("/inverter", response_model=InverterEstimationResponse, status_code=status.HTTP_200_OK)
def estimate_inverter(request: InverterEstimationRequest):
    return CalculationService().estimate_inverter(request)


@router.post("/cost", response_model=CostEstimationResponse, status_code=status.HTTP_200_OK)
def estimate_cost(request: CostEstimationRequest):
    return CalculationService().estimate_cost(request)


@router.post("/roi", response_model=ROIResponse, status_code=status.HTTP_200_OK)
def calculate_roi(request: ROIRequest):
    return CalculationService().calculate_roi(request)
