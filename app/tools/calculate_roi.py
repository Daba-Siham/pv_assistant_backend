from app.schemas.calculation import ROIRequest
from app.services.calculation.roi_service import ROIService


def calculate_roi_tool(parameters: dict) -> dict:
    service = ROIService()

    request = ROIRequest(**parameters)
    result = service.calculate_roi(request)

    return result.model_dump()


TOOL_DEFINITION = {
    "name": "calculate_roi",
    "description": "Calcule le retour sur investissement d'une installation solaire.",
    "required_parameters": [
        "total_cost",
        "annual_production_kwh"
    ],
    "optional_parameters": [
        "electricity_price",
        "annual_maintenance_cost"
    ],
    "function": calculate_roi_tool
}