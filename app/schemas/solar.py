from typing import Literal

from pydantic import BaseModel, Field


class SolarDataRequest(BaseModel):
    city: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class SolarDataResponse(BaseModel):
    city: str | None = None
    latitude: float
    longitude: float
    ghi: float
    dni: float | None = None
    temperature_avg: float
    peak_sun_hours: float
    source: str = "dataset"


class SolarCityResponse(BaseModel):
    city: str
    latitude: float
    longitude: float
    ghi: float
    temperature_avg: float
    peak_sun_hours: float


class SolarMapDataResponse(BaseModel):
    success: bool = True
    provider: Literal["pvgis"] = "pvgis"
    latitude: float
    longitude: float
    annual_pv_yield: float
    annual_ghi: float | None = None
    annual_dni: float | None = None
    annual_dhi: float | None = None
    average_temperature: float | None = None
    potential_level: Literal["excellent", "very_good", "good", "medium", "low"]
    potential_label: str
    color: str
    recommendation: str
    year: int | None = None
    source: str = "pvgis"
