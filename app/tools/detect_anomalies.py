from app.schemas.monitoring import AnomalyDetectionRequest
from app.services.monitoring.anomaly_detection_service import AnomalyDetectionService


def detect_anomalies_tool(parameters: dict) -> dict:
    service = AnomalyDetectionService()

    request = AnomalyDetectionRequest(**parameters)
    result = service.detect(request)

    return result.model_dump()


TOOL_DEFINITION = {
    "name": "detect_anomalies",
    "description": "Détecte les anomalies de production, consommation, batterie ou température.",
    "required_parameters": [
        "production_kwh",
        "expected_production_kwh",
        "consumption_kwh"
    ],
    "optional_parameters": [
        "battery_level_percent",
        "temperature"
    ],
    "function": detect_anomalies_tool
}