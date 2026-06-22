from app.schemas.calculation import PanelEstimationRequest
from app.services.calculation.panel_service import PanelService


def estimate_panels_tool(parameters: dict) -> dict:
    service = PanelService()

    request = PanelEstimationRequest(**parameters)
    result = service.estimate_panels(request)

    return result.model_dump()


TOOL_DEFINITION = {
    "name": "estimate_panels",
    "description": "Calcule le nombre de panneaux nécessaires selon la consommation, l'irradiation et la surface disponible.",
    "required_parameters": [
        "daily_consumption_kwh",
        "peak_sun_hours"
    ],
    "optional_parameters": [
        "panel_power_w",
        "performance_ratio",
        "shade_factor",
        "available_area_m2",
        "panel_area_m2"
    ],
    "function": estimate_panels_tool
}