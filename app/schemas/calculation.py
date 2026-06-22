from pydantic import BaseModel, Field


class CalculationRequest(BaseModel):
    daily_consumption_kwh: float = Field(..., gt=0)
    city: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    available_area_m2: float = Field(..., gt=0)
    budget: float | None = Field(default=None, ge=0)

    autonomy_days: float = Field(default=1, ge=0)
    installation_type: str = Field(default="hybride")

    orientation: str = Field(default="sud")
    tilt_angle: float = Field(default=30, ge=0, le=90)
    shade_factor: float = Field(default=1.0, gt=0, le=1)

    roof_type: str | None = None
    distance_to_load_m: float | None = Field(default=None, ge=0)


class PanelEstimationRequest(BaseModel):
    daily_consumption_kwh: float = Field(..., gt=0)
    panel_power_w: float = Field(default=450, gt=0)
    peak_sun_hours: float = Field(..., gt=0)
    performance_ratio: float = Field(default=0.75, gt=0, le=1)
    shade_factor: float = Field(default=1.0, gt=0, le=1)
    available_area_m2: float | None = Field(default=None, gt=0)
    panel_area_m2: float = Field(default=2.0, gt=0)


class PanelEstimationResponse(BaseModel):
    panel_count: int
    panel_power_w: float
    total_power_kwp: float
    estimated_daily_production_kwh: float
    required_area_m2: float
    is_area_sufficient: bool


class BatteryEstimationRequest(BaseModel):
    daily_consumption_kwh: float = Field(..., gt=0)
    autonomy_days: float = Field(default=1, ge=0)
    battery_voltage: float = Field(default=48, gt=0)
    dod: float = Field(default=0.8, gt=0, le=1)
    battery_efficiency: float = Field(default=0.9, gt=0, le=1)
    installation_type: str = Field(default="hybride")


class BatteryEstimationResponse(BaseModel):
    required_capacity_kwh: float
    required_capacity_ah: float
    autonomy_days: float
    battery_voltage: float
    battery_needed: bool


class InverterEstimationRequest(BaseModel):
    total_panel_power_kwp: float = Field(..., gt=0)
    max_load_kw: float | None = Field(default=None, gt=0)
    margin: float = Field(default=1.25, gt=1)


class InverterEstimationResponse(BaseModel):
    recommended_power_kw: float
    minimum_power_kw: float
    inverter_margin: float


class CostEstimationRequest(BaseModel):
    panel_count: int = Field(..., ge=0)
    panel_unit_price: float = Field(default=1500, ge=0)

    battery_count: int = Field(default=0, ge=0)
    battery_unit_price: float = Field(default=3000, ge=0)

    inverter_count: int = Field(default=1, ge=0)
    inverter_unit_price: float = Field(default=5000, ge=0)

    installation_cost: float = Field(default=3000, ge=0)
    cable_cost: float = Field(default=500, ge=0)
    maintenance_cost: float = Field(default=0, ge=0)


class CostEstimationResponse(BaseModel):
    panels_cost: float
    batteries_cost: float
    inverter_cost: float
    installation_cost: float
    cable_cost: float
    maintenance_cost: float
    total_cost: float


class ROIRequest(BaseModel):
    total_cost: float = Field(..., gt=0)
    annual_production_kwh: float = Field(..., gt=0)
    electricity_price: float = Field(default=1.5, gt=0)
    annual_maintenance_cost: float = Field(default=0, ge=0)


class ROIResponse(BaseModel):
    annual_saving: float
    net_annual_saving: float
    roi_years: float
    profitability_message: str


class CableSizingRequest(BaseModel):
    length_m: float = Field(..., gt=0)
    current_a: float = Field(..., gt=0)
    voltage_drop_v: float = Field(..., gt=0)
    conductivity: float = Field(default=56, gt=0)


class CableSizingResponse(BaseModel):
    cable_section_mm2: float
    recommended_standard_section_mm2: float


class CalculationResponse(BaseModel):
    success: bool
    message: str

    solar_data: dict
    panels: PanelEstimationResponse
    battery: BatteryEstimationResponse
    inverter: InverterEstimationResponse
    cost: CostEstimationResponse
    roi: ROIResponse

    cable: CableSizingResponse | None = None
    stores: list[dict] = []
    recommendations: list[str] = []
    assumptions: list[str] = []