from app.schemas.calculation import CostEstimationRequest
from app.services.calculation.pricing_service import PricingService


def estimate_cost_tool(parameters: dict) -> dict:
    service = PricingService()

    request = CostEstimationRequest(**parameters)
    result = service.estimate_cost(request)

    return result.model_dump()


TOOL_DEFINITION = {
    "name": "estimate_cost",
    "description": "Estime le coût total d'une installation photovoltaïque.",
    "required_parameters": [
        "panel_count"
    ],
    "optional_parameters": [
        "panel_unit_price",
        "battery_count",
        "battery_unit_price",
        "inverter_count",
        "inverter_unit_price",
        "installation_cost",
        "cable_cost",
        "maintenance_cost"
    ],
    "function": estimate_cost_tool
}