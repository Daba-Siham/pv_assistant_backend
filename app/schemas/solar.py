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