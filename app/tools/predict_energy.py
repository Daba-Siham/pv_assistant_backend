from app.schemas.monitoring import EnergyPredictionRequest
from app.services.monitoring.prediction_service import PredictionService


def predict_energy_tool(parameters: dict) -> dict:
    service = PredictionService()

    request = EnergyPredictionRequest(**parameters)
    result = service.predict_energy(request)

    return result.model_dump()


TOOL_DEFINITION = {
    "name": "predict_energy",
    "description": "Prédit la production énergétique future d'un système photovoltaïque.",
    "required_parameters": [
        "total_power_kwp"
    ],
    "optional_parameters": [
        "city",
        "latitude",
        "longitude",
        "prediction_days",
        "temperature_avg",
        "weather_condition"
    ],
    "function": predict_energy_tool
}