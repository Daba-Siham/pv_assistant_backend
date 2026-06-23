from datetime import datetime
from pydantic import BaseModel, Field


class MonitoringSimulationRequest(BaseModel):
    system_id: int | None = None
    daily_consumption_kwh: float = Field(..., gt=0)
    panel_count: int = Field(..., gt=0)
    total_power_kwp: float = Field(..., gt=0)
    battery_capacity_kwh: float | None = Field(default=None, ge=0)
    scenario: str = Field(default="normal")
    duration_hours: int = Field(default=24, ge=1, le=168)


class MonitoringDataPoint(BaseModel):
    timestamp: datetime
    production_kwh: float
    consumption_kwh: float
    battery_level_percent: float | None = None
    temperature: float | None = None
    irradiance_w_m2: float | None = None
    panel_temperature_c: float | None = None
    performance_ratio_percent: float | None = None
    energy_balance_kwh: float | None = None
    grid_import_kwh: float | None = None
    grid_export_kwh: float | None = None
    system_status: str = "normal"


class MonitoringSimulationResponse(BaseModel):
    simulation_id: int | None = None
    scenario: str
    duration_hours: int
    data: list[MonitoringDataPoint]
    alerts: list[dict] = []
    summary: dict


class MonitoringStatusResponse(BaseModel):
    simulation_id: int
    current_status: str
    battery_level_percent: float | None = None
    current_production_kwh: float
    current_consumption_kwh: float
    last_update: datetime
    alerts_count: int


class AnomalyDetectionRequest(BaseModel):
    production_kwh: float = Field(..., ge=0)
    expected_production_kwh: float = Field(..., ge=0)
    consumption_kwh: float = Field(..., ge=0)
    battery_level_percent: float | None = Field(default=None, ge=0, le=100)
    temperature: float | None = None


class AlertResponse(BaseModel):
    id: int | None = None
    severity: str
    alert_type: str
    message: str
    probable_cause: str | None = None
    recommended_action: str | None = None
    created_at: datetime | None = None


class AnomalyDetectionResponse(BaseModel):
    has_anomaly: bool
    anomaly_type: str | None = None
    severity: str | None = None
    alerts: list[AlertResponse] = []
    recommendations: list[str] = []


class EnergyPredictionRequest(BaseModel):
    city: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    total_power_kwp: float = Field(..., gt=0)
    prediction_days: int = Field(default=1, ge=1, le=7)
    temperature_avg: float | None = None
    weather_condition: str | None = None


class EnergyPredictionResponse(BaseModel):
    prediction_days: int
    estimated_production_kwh: float
    estimated_consumption_kwh: float | None = None
    battery_risk: str | None = None
    recommendations: list[str] = []

class MonitoringConfirmRequest(BaseModel):
    panel_count: int
    total_power_kwp: float
    battery_capacity_kwh: float | None = None
    inverter_power_kw: float | None = None
    city: str | None = None
    installation_type: str | None = None
    orientation: str | None = None
    tilt_angle: float | None = None
    daily_consumption_kwh: float | None = None
    total_cost: float | None = None
    roi_years: float | None = None
    annual_saving: float | None = None
    panel_model: str | None = None
    inverter_model: str | None = None
    battery_model: str | None = None
    panels_result: dict | None = None
    battery_result: dict | None = None
    inverter_result: dict | None = None
    cost_result: dict | None = None
    roi_result: dict | None = None
    solar_data: dict | None = None
    recommendations: list | None = None
