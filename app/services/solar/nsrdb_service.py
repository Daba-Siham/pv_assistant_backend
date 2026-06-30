from __future__ import annotations

import json
from io import StringIO
from urllib.parse import urlencode

import pandas as pd
import requests
from fastapi import HTTPException, status

from app.config import settings
from app.schemas.solar import SolarMapDataResponse


class NSRDBSolarService:
    def __init__(self) -> None:
        self.base_url = settings.NSRDB_BASE_URL
        self.api_key = settings.NSRDB_API_KEY
        self.default_year = settings.DEFAULT_NSRDB_YEAR
        self.timeout_seconds = settings.NSRDB_TIMEOUT_SECONDS
        self.interval_minutes = settings.NSRDB_INTERVAL_MINUTES

    def get_solar_data(self, latitude: float, longitude: float, year: int | None = None) -> SolarMapDataResponse:
        self._validate_coordinates(latitude, longitude)
        if not self.api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="NSRDB_API_KEY is not configured.",
            )

        target_year = year or self.default_year
        response_text = self._download_csv(latitude=latitude, longitude=longitude, year=target_year)
        frame = self._parse_csv(response_text)

        if frame.empty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="NSRDB returned no data for the requested location.",
            )

        normalized = {self._normalize_column(col): col for col in frame.columns}

        ghi_column = self._find_column(normalized, ["ghi"])
        dni_column = self._find_column(normalized, ["dni"])
        dhi_column = self._find_column(normalized, ["dhi"])
        temp_column = self._find_column(normalized, ["air_temperature", "temperature", "temp"])

        if ghi_column is None or dni_column is None or dhi_column is None:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="NSRDB response is missing required solar columns.",
            )

        numeric = frame.copy()
        for column in [ghi_column, dni_column, dhi_column, temp_column]:
            if column and column in numeric.columns:
                numeric[column] = pd.to_numeric(numeric[column], errors="coerce")

        numeric = numeric.dropna(subset=[ghi_column, dni_column, dhi_column], how="all")
        if numeric.empty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="NSRDB returned no usable solar readings for this location.",
            )

        # NSRDB time-series values are treated as average irradiance per interval (W/m²).
        # We convert them to annual energy by multiplying by the interval duration in hours.
        interval_hours = max(self.interval_minutes, 1) / 60.0

        annual_ghi = self._aggregate_annual(numeric[ghi_column], interval_hours)
        annual_dni = self._aggregate_annual(numeric[dni_column], interval_hours)
        annual_dhi = self._aggregate_annual(numeric[dhi_column], interval_hours)

        average_temperature = None
        if temp_column and temp_column in numeric.columns:
            temp_series = pd.to_numeric(numeric[temp_column], errors="coerce").dropna()
            if not temp_series.empty:
                average_temperature = round(float(temp_series.mean()), 1)

        potential_level, potential_label, color, recommendation = self._classify(annual_ghi)

        return SolarMapDataResponse(
            latitude=latitude,
            longitude=longitude,
            annual_ghi=annual_ghi,
            annual_dni=annual_dni,
            annual_dhi=annual_dhi,
            average_temperature=average_temperature,
            potential_level=potential_level,
            potential_label=potential_label,
            color=color,
            recommendation=recommendation,
            year=target_year,
            source="nsrdb",
        )

    def _download_csv(self, latitude: float, longitude: float, year: int) -> str:
        unavailable_message = "Unable to retrieve NSRDB data for this location."
        params = {
            "api_key": self.api_key,
            "wkt": f"POINT({longitude} {latitude})",
            "names": str(year),
            "attributes": "ghi,dni,dhi,air_temperature",
            "leap_day": "false",
            "utc": "false",
            "interval": "60",
            "full_name": "SolarAI",
            "email": "admin@solarai.local",
            "affiliation": "SolarAI",
            "reason": "solar_map",
            "mailing_list": "false",
        }
        logged_params = {**params, "api_key": "***"}
        print(f"NSRDB request URL: {self.base_url}?{urlencode(logged_params)}")

        try:
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout_seconds,
            )
        except requests.Timeout as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"{unavailable_message} NSRDB request timed out.",
            ) from exc
        except requests.RequestException as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"{unavailable_message} NSRDB service is unreachable.",
            ) from exc

        if not response.ok:
            message = self._extract_error_message(response.text)
            if self._looks_like_no_data(response.text, response.status_code):
                message = (
                    "Unable to retrieve NSRDB data for this location. "
                    "The current NSRDB dataset may not cover Morocco or North Africa."
                )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message or "NSRDB request failed.",
            )

        text = response.text.strip()
        if not text:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="NSRDB returned an empty response.",
            )

        return text

    def _parse_csv(self, text: str) -> pd.DataFrame:
        lines = [line for line in text.splitlines() if line.strip()]
        header_index = None

        for index, line in enumerate(lines):
            normalized = line.lower()
            if normalized.startswith("year,") or "ghi" in normalized and "dni" in normalized and "dhi" in normalized:
                header_index = index
                break

        if header_index is None:
            if self._looks_like_no_data(text, 404):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=(
                        "Unable to retrieve NSRDB data for this location. "
                        "The current NSRDB dataset may not cover Morocco or North Africa."
                    ),
                )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Malformed NSRDB response.",
            )

        try:
            csv_text = "\n".join(lines[header_index:])
            frame = pd.read_csv(StringIO(csv_text))
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Malformed NSRDB CSV payload.",
            ) from exc

        if frame.empty:
            return frame

        frame.columns = [str(column).strip() for column in frame.columns]
        return frame

    def _validate_coordinates(self, latitude: float, longitude: float) -> None:
        if latitude < -90 or latitude > 90 or longitude < -180 or longitude > 180:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid latitude or longitude.",
            )

    def _aggregate_annual(self, series: pd.Series, interval_hours: float) -> float:
        total_wh_per_m2 = float(series.dropna().sum()) * interval_hours
        return round(total_wh_per_m2 / 1000.0, 1)

    def _classify(self, annual_ghi: float) -> tuple[str, str, str, str]:
        if annual_ghi >= 2200:
            return (
                "excellent",
                "Excellent potentiel solaire",
                "#ef4444",
                "Cette zone est très favorable à l'installation de panneaux photovoltaïques.",
            )
        if annual_ghi >= 2000:
            return (
                "very_good",
                "Très bon potentiel solaire",
                "#f97316",
                "Cette zone offre de très bonnes conditions pour un projet photovoltaïque.",
            )
        if annual_ghi >= 1800:
            return (
                "good",
                "Bon potentiel solaire",
                "#eab308",
                "Cette zone est adaptée à une installation solaire bien dimensionnée.",
            )
        if annual_ghi >= 1600:
            return (
                "medium",
                "Potentiel solaire moyen",
                "#22c55e",
                "Cette zone reste exploitable avec une conception photovoltaïque optimisée.",
            )
        return (
            "low",
            "Potentiel solaire faible",
            "#3b82f6",
            "Cette zone peut fonctionner, mais la production solaire sera plus limitée.",
        )

    def _find_column(self, normalized_map: dict[str, str], candidates: list[str]) -> str | None:
        for candidate in candidates:
            if candidate in normalized_map:
                return normalized_map[candidate]
        return None

    def _normalize_column(self, column: str) -> str:
        return str(column).strip().lower().replace(" ", "_")

    def _extract_error_message(self, text: str) -> str | None:
        cleaned = text.strip()
        if not cleaned:
            return None
        if cleaned.startswith("{"):
            try:
                payload = json.loads(cleaned)
                if isinstance(payload, dict):
                    return payload.get("message") or payload.get("detail") or payload.get("error")
            except Exception:
                return cleaned[:240]
        return cleaned[:240]

    def _looks_like_no_data(self, text: str, status_code: int) -> bool:
        if status_code in {400, 404, 422}:
            return True

        lowered = (text or "").lower()
        return any(
            marker in lowered
            for marker in [
                "no data",
                "not available",
                "outside of coverage",
                "coverage",
                "unsupported",
                "invalid location",
                "not found",
            ]
        )
