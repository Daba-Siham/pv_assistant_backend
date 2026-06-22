from fastapi import APIRouter, status

from app.schemas.solar import SolarDataRequest, SolarDataResponse, SolarCityResponse
from app.services.calculation.solar_service import SolarService

router = APIRouter()


@router.post("/data", response_model=SolarDataResponse, status_code=status.HTTP_200_OK)
def get_solar_data(request: SolarDataRequest):
    solar_service = SolarService()
    return solar_service.get_solar_data(request)


@router.get("/cities", response_model=list[SolarCityResponse], status_code=status.HTTP_200_OK)
def get_available_cities():
    solar_service = SolarService()
    return solar_service.get_available_cities()


@router.get("/city/{city_name}", response_model=SolarDataResponse, status_code=status.HTTP_200_OK)
def get_solar_data_by_city(city_name: str):
    solar_service = SolarService()
    return solar_service.get_solar_data_by_city(city_name)