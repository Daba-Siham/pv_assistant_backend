from app.schemas.calculation import InverterEstimationRequest
from app.services.calculation.inverter_service import InverterService


def estimate_inverter_tool(parameters: dict) -> dict:
    service = InverterService()

    request = InverterEstimationRequest(**parameters)
    result = service.estimate_inverter(request)

    return result.model_dump()


TOOL_DEFINITION = {
    "name": "estimate_inverter",
    "description": "Estime la puissance recommandée de l'onduleur.",
    "required_parameters": [
        "total_panel_power_kwp"
    ],
    "optional_parameters": [
        "max_load_kw",
        "margin"
    ],
    "function": estimate_inverter_tool
}