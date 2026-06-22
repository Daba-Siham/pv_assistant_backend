import math
from pathlib import Path

import pandas as pd
from fastapi import HTTPException, status

from app.config import settings
from app.schemas.solar import SolarDataRequest, SolarDataResponse, SolarCityResponse


class SolarService:
    def __init__(self):
        self.solar_file = settings.SOLAR_DATA_DIR / "solar_irradiation_reference.csv"

    def get_solar_data(self, request: SolarDataRequest) -> SolarDataResponse:
        if request.city:
            return self.get_solar_data_by_city(request.city)

        if request.latitude is not None and request.longitude is not None:
            return self.get_solar_data_by_coordinates(
                latitude=request.latitude,
                longitude=request.longitude
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Veuillez fournir soit une ville, soit latitude et longitude."
        )

    def get_solar_data_by_city(self, city_name: str) -> SolarDataResponse:
        df = self._load_solar_dataset()

        if df.empty:
            return self._default_solar_data(city=city_name)

        df["city_normalized"] = df["city"].astype(str).str.lower().str.strip()
        city_normalized = city_name.lower().strip()

        result = df[df["city_normalized"] == city_normalized]

        if result.empty:
            return self._default_solar_data(city=city_name)

        row = result.iloc[0]

        return SolarDataResponse(
            city=str(row.get("city", city_name)),
            latitude=float(row.get("latitude", 0)),
            longitude=float(row.get("longitude", 0)),
            ghi=float(row.get("ghi", 5.5)),
            dni=float(row.get("dni", 0)) if "dni" in row else None,
            temperature_avg=float(row.get("temperature_avg", 25)),
            peak_sun_hours=float(row.get("peak_sun_hours", row.get("ghi", 5.5))),
            source="dataset"
        )

    def get_solar_data_by_coordinates(self, latitude: float, longitude: float) -> SolarDataResponse:
        df = self._load_solar_dataset()

        if df.empty:
            return self._default_solar_data(
                city="Coordonnées utilisateur",
                latitude=latitude,
                longitude=longitude
            )

        df["distance"] = df.apply(
            lambda row: self._haversine_distance(
                latitude,
                longitude,
                float(row["latitude"]),
                float(row["longitude"])
            ),
            axis=1
        )

        nearest = df.sort_values("distance").iloc[0]

        return SolarDataResponse(
            city=str(nearest.get("city", "Ville proche")),
            latitude=latitude,
            longitude=longitude,
            ghi=float(nearest.get("ghi", 5.5)),
            dni=float(nearest.get("dni", 0)) if "dni" in nearest else None,
            temperature_avg=float(nearest.get("temperature_avg", 25)),
            peak_sun_hours=float(nearest.get("peak_sun_hours", nearest.get("ghi", 5.5))),
            source="nearest_dataset_point"
        )

    def get_available_cities(self) -> list[SolarCityResponse]:
        df = self._load_solar_dataset()

        if df.empty:
            return []

        cities = []

        for _, row in df.iterrows():
            cities.append(
                SolarCityResponse(
                    city=str(row.get("city")),
                    latitude=float(row.get("latitude", 0)),
                    longitude=float(row.get("longitude", 0)),
                    ghi=float(row.get("ghi", 5.5)),
                    temperature_avg=float(row.get("temperature_avg", 25)),
                    peak_sun_hours=float(row.get("peak_sun_hours", row.get("ghi", 5.5)))
                )
            )

        return cities

    def _load_solar_dataset(self) -> pd.DataFrame:
        if not self.solar_file.exists():
            return pd.DataFrame()

        try:
            return pd.read_csv(self.solar_file)
        except Exception:
            return pd.DataFrame()

    def _default_solar_data(
        self,
        city: str,
        latitude: float = 0,
        longitude: float = 0
    ) -> SolarDataResponse:
        return SolarDataResponse(
            city=city,
            latitude=latitude,
            longitude=longitude,
            ghi=5.5,
            dni=None,
            temperature_avg=25,
            peak_sun_hours=5.5,
            source="default_estimation"
        )

    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        radius = 6371

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return radius * c