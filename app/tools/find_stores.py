from app.schemas.store import StoreSearchRequest
from app.services.calculation.store_recommendation_service import StoreRecommendationService


def find_stores_tool(parameters: dict) -> dict:
    service = StoreRecommendationService()

    request = StoreSearchRequest(**parameters)
    result = service.find_nearby_stores(request)

    return result.model_dump()


TOOL_DEFINITION = {
    "name": "find_stores",
    "description": "Recherche des magasins ou fournisseurs proches selon la localisation.",
    "required_parameters": [
        "latitude",
        "longitude"
    ],
    "optional_parameters": [
        "max_distance_km",
        "product_type"
    ],
    "function": find_stores_tool
}