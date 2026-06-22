from app.schemas.solar import SolarDataRequest
from app.services.calculation.solar_service import SolarService


def get_solar_data_tool(parameters: dict) -> dict:
    service = SolarService()

    request = SolarDataRequest(**parameters)
    result = service.get_solar_data(request)

    return result.model_dump()


TOOL_DEFINITION = {
    "name": "get_solar_data",
    "description": "Récupère les données solaires d'une ville ou de coordonnées GPS.",
    "required_parameters": [],
    "optional_parameters": ["city", "latitude", "longitude"],
    "function": get_solar_data_tool
}