from fastapi import APIRouter, Query, status

from app.schemas.solar import SolarStoresResponse
from app.services.solar.overpass_stores_service import GeoapifyStoresService


router = APIRouter()


@router.get("", response_model=SolarStoresResponse, status_code=status.HTTP_200_OK)
def get_nearby_solar_stores(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(15, gt=0, le=50),
):
    service = GeoapifyStoresService()
    return service.get_nearby_stores(latitude=lat, longitude=lon, radius_km=radius_km)
