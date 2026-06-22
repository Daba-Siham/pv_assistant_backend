from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_simulate_monitoring():
    payload = {
        "daily_consumption_kwh": 8,
        "panel_count": 6,
        "total_power_kwp": 2.7,
        "battery_capacity_kwh": 5,
        "scenario": "normal",
        "duration_hours": 24
    }

    response = client.post("/api/v1/monitoring/simulate", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["scenario"] == "normal"
    assert data["duration_hours"] == 24
    assert len(data["data"]) == 24
    assert "summary" in data


def test_detect_anomalies():
    payload = {
        "production_kwh": 1.2,
        "expected_production_kwh": 5.5,
        "consumption_kwh": 4.5,
        "battery_level_percent": 18,
        "temperature": 42
    }

    response = client.post("/api/v1/monitoring/detect-anomalies", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["has_anomaly"] is True
    assert len(data["alerts"]) > 0
    assert len(data["recommendations"]) > 0


def test_predict_energy():
    payload = {
        "city": "Nador",
        "latitude": 35.1688,
        "longitude": -2.9335,
        "total_power_kwp": 2.7,
        "prediction_days": 3,
        "temperature_avg": 32,
        "weather_condition": "ensoleillé"
    }

    response = client.post("/api/v1/monitoring/predict", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["prediction_days"] == 3
    assert data["estimated_production_kwh"] > 0
    assert "recommendations" in data