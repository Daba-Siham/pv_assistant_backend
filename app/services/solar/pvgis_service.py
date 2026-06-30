from __future__ import annotations

import logging
from typing import Any

import requests
from fastapi import HTTPException, status

from app.config import settings
from app.schemas.solar import SolarMapDataResponse


logger = logging.getLogger(__name__)


class PVGISSolarService:
    def __init__(self) -> None:
        self.base_url = settings.PVGIS_BASE_URL
        self.timeout_seconds = settings.PVGIS_TIMEOUT_SECONDS

    def get_solar_data(self, latitude: float, longitude: float, year: int | None = None) -> SolarMapDataResponse:
        self._validate_coordinates(latitude, longitude)

        payload = self._download_pvgis(latitude=latitude, longitude=longitude)
        annual_pv_yield = self._to_float(self._extract_nested_value(payload, ["outputs", "totals", "fixed", "E_y"]))

        if annual_pv_yield is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PVGIS data is not available for this location.",
            )

        annual_ghi = self._extract_irradiation(payload)
        potential_level, potential_label, color, recommendation = self._classify(annual_pv_yield)

        return SolarMapDataResponse(
            success=True,
            provider="pvgis",
            latitude=latitude,
            longitude=longitude,
            annual_pv_yield=round(annual_pv_yield, 1),
            annual_ghi=self._round_optional(annual_ghi),
            annual_dni=None,
            annual_dhi=None,
            average_temperature=None,
            potential_level=potential_level,
            potential_label=potential_label,
            color=color,
            recommendation=recommendation,
            year=year,
            source="pvgis",
        )

    def _download_pvgis(self, latitude: float, longitude: float) -> dict[str, Any]:
        params = {
            "lat": latitude,
            "lon": longitude,
            "peakpower": 1,
            "loss": 14,
            "outputformat": "json",
        }

        try:
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout_seconds,
            )
        except requests.Timeout as exc:
            logger.warning("Solar data provider=%s status=timeout", "pvgis")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="PVGIS data is not available for this location.",
            ) from exc
        except requests.RequestException as exc:
            logger.warning("Solar data provider=%s status=unreachable", "pvgis")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="PVGIS data is not available for this location.",
            ) from exc

        logger.info("Solar data provider=%s status=%s", "pvgis", response.status_code)

        if not response.ok:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PVGIS data is not available for this location.",
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="PVGIS data is not available for this location.",
            ) from exc

        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="PVGIS data is not available for this location.",
            )

        errors = payload.get("errors")
        if errors:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PVGIS data is not available for this location.",
            )

        return payload

    def _extract_nested_value(self, payload: Any, path: list[str]) -> Any:
        current = payload
        for key in path:
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        return current

    def _extract_irradiation(self, payload: dict[str, Any]) -> float | None:
        totals = payload.get("outputs", {}).get("totals", {})
        fixed = totals.get("fixed", {})
        if not isinstance(fixed, dict):
            return None

        preferred_keys = [
            "H(i)_y",
            "H(i)",
            "G(i)_y",
            "G(i)",
            "H(i)_opt",
            "G(i)_opt",
        ]

        for key in preferred_keys:
            value = self._to_float(fixed.get(key))
            if value is not None:
                return value

        for key, value in fixed.items():
            normalized_key = str(key).strip().lower().replace(" ", "")
            if (
                (normalized_key.startswith("h(i)") or normalized_key.startswith("g(i)"))
                and normalized_key.endswith("_y")
            ):
                numeric = self._to_float(value)
                if numeric is not None:
                    return numeric

        return None

    def _classify(self, annual_pv_yield: float) -> tuple[str, str, str, str]:
        if annual_pv_yield >= 1800:
            return (
                "excellent",
                "Excellent potentiel solaire",
                "#ef4444",
                "Cette zone est excellente pour une installation photovoltaïque. Le rendement attendu est très élevé.",
            )
        if annual_pv_yield >= 1650:
            return (
                "very_good",
                "Très bon potentiel solaire",
                "#f97316",
                "Cette zone est très favorable à l'installation de panneaux photovoltaïques.",
            )
        if annual_pv_yield >= 1500:
            return (
                "good",
                "Bon potentiel solaire",
                "#eab308",
                "Cette zone présente un bon potentiel solaire pour un projet résidentiel ou commercial.",
            )
        if annual_pv_yield >= 1300:
            return (
                "medium",
                "Potentiel solaire moyen",
                "#22c55e",
                "Cette zone reste exploitable, mais le dimensionnement doit être optimisé.",
            )
        return (
            "low",
            "Faible potentiel solaire",
            "#3b82f6",
            "Cette zone a un potentiel plus faible. Une étude détaillée est recommandée avant installation.",
        )

    def _validate_coordinates(self, latitude: float, longitude: float) -> None:
        if latitude < -90 or latitude > 90 or longitude < -180 or longitude > 180:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid latitude or longitude.",
            )

    def _to_float(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _round_optional(self, value: float | None) -> float | None:
        if value is None:
            return None
        return round(value, 1)
