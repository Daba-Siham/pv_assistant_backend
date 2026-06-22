from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, status
from fastapi.responses import FileResponse

from app.dependencies import DBSession
from app.schemas.recommendation import PVRecommendationRequest, PVRecommendationResponse
from app.services.recommendation import PVRecommendationService
from pdf.generator import generate_recommendation_pdf_report

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parents[3]


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

    return FileResponse(
        path=str(filepath),
        media_type="application/pdf",
        filename=filename,
    )
