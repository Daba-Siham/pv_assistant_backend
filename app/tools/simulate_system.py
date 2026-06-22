from app.schemas.monitoring import MonitoringSimulationRequest
from app.services.monitoring.simulation_service import SimulationService


def simulate_system_tool(parameters: dict) -> dict:
    service = SimulationService()

    request = MonitoringSimulationRequest(**parameters)
    result = service.simulate(request)

    return result.model_dump()


TOOL_DEFINITION = {
    "name": "simulate_system",
    "description": "Simule le fonctionnement d'un système photovoltaïque sur une durée donnée.",
    "required_parameters": [
        "daily_consumption_kwh",
        "panel_count",
        "total_power_kwp"
    ],
    "optional_parameters": [
        "system_id",
        "battery_capacity_kwh",
        "scenario",
        "duration_hours"
    ],
    "function": simulate_system_tool
}