from app.schemas.calculation import BatteryEstimationRequest
from app.services.calculation.battery_service import BatteryService


def estimate_batteries_tool(parameters: dict) -> dict:
    service = BatteryService()

    request = BatteryEstimationRequest(**parameters)
    result = service.estimate_battery(request)

    return result.model_dump()


TOOL_DEFINITION = {
    "name": "estimate_batteries",
    "description": "Calcule la capacité batterie nécessaire selon la consommation et l'autonomie souhaitée.",
    "required_parameters": [
        "daily_consumption_kwh"
    ],
    "optional_parameters": [
        "autonomy_days",
        "battery_voltage",
        "dod",
        "battery_efficiency",
        "installation_type"
    ],
    "function": estimate_batteries_tool
}