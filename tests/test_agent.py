from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_list_agent_tools():
    response = client.get("/api/v1/agent/tools")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) > 0

    tool_names = [tool["name"] for tool in data]

    assert "get_solar_data" in tool_names
    assert "estimate_panels" in tool_names
    assert "simulate_system" in tool_names


def test_execute_solar_tool():
    payload = {
        "tool_name": "get_solar_data",
        "parameters": {
            "city": "Nador"
        }
    }

    response = client.post("/api/v1/agent/execute-tool", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["tool_name"] == "get_solar_data"
    assert data["result"]["ghi"] > 0


def test_run_agent_dimensioning_missing_params():
    payload = {
        "user_message": "Je veux dimensionner une installation solaire",
        "session_id": "test-session",
        "user_inputs": {}
    }

    response = client.post("/api/v1/agent/run", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is False
    assert data["action"] == "calculate_pv_system"
    assert len(data["recommendations"]) > 0


def test_run_agent_dimensioning_success():
    payload = {
        "user_message": "Je veux dimensionner une installation photovoltaïque pour ma maison",
        "session_id": "test-session",
        "user_inputs": {
            "daily_consumption_kwh": 8,
            "city": "Nador",
            "latitude": 35.1688,
            "longitude": -2.9335,
            "available_area_m2": 30,
            "budget": 30000,
            "autonomy_days": 1,
            "installation_type": "hybride",
            "orientation": "sud",
            "tilt_angle": 30,
            "shade_factor": 0.9,
            "roof_type": "terrasse",
            "distance_to_load_m": 15
        }
    }

    response = client.post("/api/v1/agent/run", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["action"] == "calculate_pv_system"
    assert "calculate_pv_system" in data["tools_used"]
    assert data["result"]["panels"]["panel_count"] > 0