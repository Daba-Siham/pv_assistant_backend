from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_estimate_panels():
    payload = {
        "daily_consumption_kwh": 8,
        "panel_power_w": 450,
        "peak_sun_hours": 5.5,
        "performance_ratio": 0.75,
        "shade_factor": 1.0,
        "available_area_m2": 30,
        "panel_area_m2": 2.0
    }

    response = client.post("/api/v1/calculation/panels", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["panel_count"] > 0
    assert data["total_power_kwp"] > 0
    assert data["estimated_daily_production_kwh"] > 0
    assert "is_area_sufficient" in data


def test_estimate_batteries():
    payload = {
        "daily_consumption_kwh": 8,
        "autonomy_days": 1,
        "battery_voltage": 48,
        "dod": 0.8,
        "battery_efficiency": 0.9,
        "installation_type": "hybride"
    }

    response = client.post("/api/v1/calculation/batteries", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["required_capacity_kwh"] > 0
    assert data["required_capacity_ah"] > 0
    assert data["battery_needed"] is True


def test_estimate_inverter():
    payload = {
        "total_panel_power_kwp": 3.0,
        "max_load_kw": 2.5,
        "margin": 1.25
    }

    response = client.post("/api/v1/calculation/inverter", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["recommended_power_kw"] >= data["minimum_power_kw"]
    assert data["inverter_margin"] == 1.25


def test_estimate_cost():
    payload = {
        "panel_count": 6,
        "panel_unit_price": 1500,
        "battery_count": 2,
        "battery_unit_price": 3000,
        "inverter_count": 1,
        "inverter_unit_price": 5000,
        "installation_cost": 3000,
        "cable_cost": 800,
        "maintenance_cost": 0
    }

    response = client.post("/api/v1/calculation/cost", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["panels_cost"] == 9000
    assert data["batteries_cost"] == 6000
    assert data["inverter_cost"] == 5000
    assert data["total_cost"] > 0


def test_calculate_roi():
    payload = {
        "total_cost": 25000,
        "annual_production_kwh": 3000,
        "electricity_price": 1.5,
        "annual_maintenance_cost": 300
    }

    response = client.post("/api/v1/calculation/roi", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["annual_saving"] > 0
    assert data["net_annual_saving"] > 0
    assert data["roi_years"] > 0
    assert "profitability_message" in data