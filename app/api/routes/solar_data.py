from fastapi import APIRouter, Query, status

from app.schemas.solar import SolarMapDataResponse
from app.services.solar import PVGISSolarService


router = APIRouter()


@router.get("", response_model=SolarMapDataResponse, status_code=status.HTTP_200_OK)
def get_solar_data(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    service = PVGISSolarService()
    return service.get_solar_data(latitude=lat, longitude=lon)
