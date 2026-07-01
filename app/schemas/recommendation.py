from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.services.shared.utils import is_on_grid, normalize_installation_type


class InstallationType(str, Enum):
    ON_GRID = "on_grid"
    HYBRID = "hybrid"
    OFF_GRID = "off_grid"


class ElectricalPhase(str, Enum):
    SINGLE_PHASE = "single_phase"
    THREE_PHASE = "three_phase"


class PVRecommendationRequest(BaseModel):
    city: str = Field(default="non fournie")
    client_name: str | None = None
    monthly_consumption_kwh: float | None = Field(default=None, gt=0)
    daily_consumption_kwh: float | None = Field(default=None, gt=0)
    installation_type: InstallationType
    available_area_m2: float = Field(..., gt=0)
    budget: float | None = Field(default=None, ge=0)
    autonomy_days: float = Field(default=0, ge=0)
    roof_type: str | None = None
    orientation: str = Field(default="sud")
    tilt_angle: float = Field(default=30, ge=0, le=90)
    shading: str | None = Field(default=None)
    shade_factor: float | None = Field(default=None, gt=0, le=1)
    distance_panels_inverter_m: float | None = Field(default=None, ge=0)
    distance_inverter_house_m: float | None = Field(default=None, ge=0)
    electrical_phase: ElectricalPhase = Field(default=ElectricalPhase.SINGLE_PHASE)
    electricity_tariff: float = Field(default=1.5, gt=0)

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_values(cls, values: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(values, dict):
            return values

        city = values.get("city")
        if city is None or (isinstance(city, str) and not city.strip()):
            values["city"] = "non fournie"

        installation_type = values.get("installation_type")
        if isinstance(installation_type, str):
            normalized_type = normalize_installation_type(installation_type)
            if is_on_grid(normalized_type):
                values["installation_type"] = "on_grid"
            else:
                normalized = normalized_type.replace("-", "_")
                if normalized == "hybride":
                    normalized = "hybrid"
                if normalized in {"off-grid", "offgrid"}:
                    normalized = "off_grid"
                values["installation_type"] = normalized

        orientation = values.get("orientation")
        if isinstance(orientation, str):
            values["orientation"] = orientation.strip().lower()

        phase = values.get("electrical_phase")
        if isinstance(phase, str):
            normalized_phase = phase.strip().lower().replace("-", "_")
            if normalized_phase in {"mono", "monophase", "monophasee"}:
                normalized_phase = "single_phase"
            if normalized_phase in {"tri", "triphase", "triphasee"}:
                normalized_phase = "three_phase"
            values["electrical_phase"] = normalized_phase

        if is_on_grid(values.get("installation_type")):
            values["autonomy_days"] = 0

        return values

    @model_validator(mode="after")
    def require_one_consumption_value(self):
        if self.daily_consumption_kwh is None and self.monthly_consumption_kwh is None:
            raise ValueError("daily_consumption_kwh ou monthly_consumption_kwh est obligatoire")
        return self

    @property
    def normalized_daily_consumption_kwh(self) -> float:
        if self.daily_consumption_kwh is not None:
            return self.daily_consumption_kwh
        return round(self.monthly_consumption_kwh / 30, 3)


class CoherenceCheck(BaseModel):
    code: str
    status: str
    message: str
    expected: Any | None = None
    actual: Any | None = None


class PVRecommendationResponse(BaseModel):
    success: bool
    user_inputs: dict[str, Any]
    formatted_recommendation: dict[str, Any] = Field(default_factory=dict)
    ml_recommendation: dict[str, Any] | None = None
    coherence_checks: list[CoherenceCheck]
    rag_context_used: bool
    response: str


class SaveRecommendationRequest(BaseModel):
    input_data: dict[str, Any]
    result_data: dict[str, Any]
    city: str | None = None
    daily_consumption_kwh: float | None = None
    available_area_m2: float | None = None
    budget: float | None = None
    installation_type: str | None = None
    orientation: str | None = None
    tilt_angle: float | None = None
    roof_type: str | None = None
    panels_result: dict[str, Any] | None = None
    battery_result: dict[str, Any] | None = None
    inverter_result: dict[str, Any] | None = None
    cost_result: dict[str, Any] | None = None
    roi_result: dict[str, Any] | None = None
    recommendations: Any | None = None
    assumptions: dict[str, Any] | None = None
    report_pdf_path: str | None = None
    report_pdf_filename: str | None = None
