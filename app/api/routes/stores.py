from fastapi import APIRouter, status

from app.schemas.store import StoreSearchRequest, StoreSearchResponse, StoreResponse
from app.services.calculation.store_recommendation_service import StoreRecommendationService

router = APIRouter()


@router.post("/nearby", response_model=StoreSearchResponse, status_code=status.HTTP_200_OK)
def find_nearby_stores(request: StoreSearchRequest):
    store_service = StoreRecommendationService()
    return store_service.find_nearby_stores(request)


@router.get("/", response_model=list[StoreResponse], status_code=status.HTTP_200_OK)
def get_all_stores():
    store_service = StoreRecommendationService()
    return store_service.get_all_stores()


@router.get("/{store_id}", response_model=StoreResponse, status_code=status.HTTP_200_OK)
def get_store_by_id(store_id: int):
    store_service = StoreRecommendationService()
    return store_service.get_store_by_id(store_id)