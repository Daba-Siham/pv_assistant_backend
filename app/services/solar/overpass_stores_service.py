from __future__ import annotations

import logging
import time
from typing import Any

import requests
from fastapi import HTTPException, status

from app.config import settings
from app.schemas.solar import SolarStoreResponse, SolarStoresResponse


logger = logging.getLogger(__name__)

GEOAPIFY_BASE_URL = "https://api.geoapify.com/v2/places"
GEOAPIFY_TIMEOUT_SECONDS = 25
CACHE_TTL_SECONDS = 600
MAX_RADIUS_KM = 50
REQUEST_HEADERS = {
    "Accept": "application/json",
}

NAME_KEYWORDS = [
    "solar",
    "solaire",
    "photovoltaic",
    "photovolta\u00efque",
    "photovoltaique",
    "pv",
    "energy",
    "energie",
    "\u00e9nergie",
    "renewable",
    "renouvelable",
    "electric",
    "\u00e9lectrique",
    "electrique",
    "\u00e9lectricit\u00e9",
    "electricit\u00e9",
    "panneaux",
    "onduleur",
    "batterie",
]

SUPPORT_KEYWORDS = [
    "commercial",
    "office.company",
    "building.commercial",
    "shop",
    "electrical",
    "electronics",
    "hardware",
]


class GeoapifyStoresService:
    _cache: dict[str, tuple[float, SolarStoresResponse]] = {}

    def __init__(self) -> None:
        self.timeout_seconds = GEOAPIFY_TIMEOUT_SECONDS

    def get_nearby_stores(self, latitude: float, longitude: float, radius_km: float = 15) -> SolarStoresResponse:
        self._validate_coordinates(latitude, longitude)
        self._validate_radius(radius_km)

        if not settings.GEOAPIFY_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Geoapify API key is not configured.",
            )

        cache_key = self._cache_key(latitude, longitude, radius_km)
        cached = self._get_cached_response(cache_key)
        if cached is not None:
            logger.info("solar_stores provider=geoapify cache_hit key=%s stores=%s", cache_key, len(cached.stores))
            return cached

        radius_m = int(round(radius_km * 1000))
        logger.info(
            "solar_stores provider=geoapify lat=%s lon=%s radius_m=%s",
            latitude,
            longitude,
            radius_m,
        )

        params = {
            "categories": "commercial,building.commercial,office.company",
            "filter": f"circle:{longitude},{latitude},{radius_m}",
            "bias": f"proximity:{longitude},{latitude}",
            "limit": 50,
            "lang": "fr",
            "apiKey": settings.GEOAPIFY_API_KEY,
        }

        response = self._download_geoapify(params)
        features = response.get("features", []) if isinstance(response, dict) else []
        raw_count = len(features) if isinstance(features, list) else 0
        logger.info("geoapify raw_count=%s", raw_count)

        stores = self._normalize_features(features, latitude, longitude)
        stores.sort(key=lambda item: item.distance_km)
        logger.info("geoapify filtered_count=%s", len(stores))

        result = SolarStoresResponse(
            success=True,
            provider="geoapify",
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            stores=stores,
            message="No solar equipment stores found within this radius." if not stores else None,
        )
        self._set_cache(cache_key, result)
        return result

    def _download_geoapify(self, params: dict[str, Any]) -> dict[str, Any]:
        try:
            response = requests.get(
                GEOAPIFY_BASE_URL,
                params=params,
                headers=REQUEST_HEADERS,
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            logger.warning("geoapify exception=%s: %s", exc.__class__.__name__, str(exc))
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unable to retrieve nearby stores from Geoapify.",
            ) from exc

        body_preview = response.text[:500]
        logger.info("geoapify status=%s body_preview=%s", response.status_code, body_preview)

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unable to retrieve nearby stores from Geoapify.",
            )

        try:
            payload = response.json()
        except ValueError as exc:
            logger.warning("geoapify json_decode_error=%s: %s", exc.__class__.__name__, str(exc))
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unable to retrieve nearby stores from Geoapify.",
            ) from exc

        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unable to retrieve nearby stores from Geoapify.",
            )

        return payload

    def _normalize_features(self, features: Any, latitude: float, longitude: float) -> list[SolarStoreResponse]:
        if not isinstance(features, list):
            return []

        stores: list[SolarStoreResponse] = []
        for feature in features:
            if not isinstance(feature, dict):
                continue

            properties = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
            geometry = feature.get("geometry") if isinstance(feature.get("geometry"), dict) else {}
            coordinates = geometry.get("coordinates") if isinstance(geometry.get("coordinates"), list) else None
            if not coordinates or len(coordinates) < 2:
                continue

            lon = self._to_float(coordinates[0])
            lat = self._to_float(coordinates[1])
            if lat is None or lon is None:
                continue

            raw_tags = {}
            datasource = properties.get("datasource")
            if isinstance(datasource, dict):
                raw = datasource.get("raw")
                if isinstance(raw, dict):
                    raw_tags = raw

            name = self._clean_text(properties.get("name")) or "Solar equipment store"
            address = self._clean_text(properties.get("formatted"))
            city = self._clean_text(properties.get("city")) or self._clean_text(properties.get("county"))
            phone = self._pick_first(
                [
                    properties.get("contact", {}).get("phone") if isinstance(properties.get("contact"), dict) else None,
                    raw_tags.get("phone"),
                    raw_tags.get("contact:phone"),
                ]
            )
            website = self._pick_first(
                [
                    properties.get("website"),
                    properties.get("contact", {}).get("website") if isinstance(properties.get("contact"), dict) else None,
                    raw_tags.get("website"),
                    raw_tags.get("contact:website"),
                ]
            )

            if self._is_relevant_store(name, properties, raw_tags):
                stores.append(
                    SolarStoreResponse(
                        id=str(
                            properties.get("place_id")
                            or raw_tags.get("osm_id")
                            or raw_tags.get("id")
                            or f"{lat}:{lon}"
                        ),
                        osm_type="node",
                        name=name,
                        latitude=lat,
                        longitude=lon,
                        address=address,
                        city=city,
                        phone=phone,
                        website=website,
                        tags=raw_tags,
                        products=self._infer_products(name, properties, raw_tags),
                        distance_km=round(self._haversine_distance(latitude, longitude, lat, lon), 2),
                    )
                )

        return stores

    def _is_relevant_store(self, name: str, properties: dict[str, Any], raw_tags: dict[str, Any]) -> bool:
        haystack_parts = [name]
        haystack_parts.extend(str(value) for value in properties.values() if value is not None)
        haystack_parts.extend(f"{key}:{value}" for key, value in raw_tags.items() if value is not None)
        haystack = " ".join(haystack_parts).lower()

        if any(keyword in haystack for keyword in NAME_KEYWORDS):
            return True
        if any(keyword in haystack for keyword in SUPPORT_KEYWORDS):
            return True
        return False

    def _infer_products(self, name: str, properties: dict[str, Any], raw_tags: dict[str, Any]) -> list[str]:
        haystack = " ".join([name, str(properties), str(raw_tags)]).lower()

        products: list[str] = []
        if any(keyword in haystack for keyword in ["solar", "solaire", "photovoltaic", "photovolta\u00efque", "photovoltaique", "pv", "panneaux"]):
            products.append("Panels")
        if any(keyword in haystack for keyword in ["battery", "batterie"]):
            products.append("Battery")
        if any(keyword in haystack for keyword in ["inverter", "onduleur"]):
            products.append("Inverter")
        if any(keyword in haystack for keyword in ["electric", "electrical", "\u00e9lectrique", "electrique", "\u00e9lectricit\u00e9", "electricit\u00e9"]):
            products.append("Electrical equipment")

        return products or ["Solar / electrical equipment"]

    def _pick_first(self, values: list[Any]) -> str | None:
        for value in values:
            text = self._clean_text(value)
            if text:
                return text
        return None

    def _clean_text(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _validate_coordinates(self, latitude: float, longitude: float) -> None:
        if latitude < -90 or latitude > 90 or longitude < -180 or longitude > 180:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid latitude or longitude.",
            )

    def _validate_radius(self, radius_km: float) -> None:
        if radius_km <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="radius_km must be greater than 0.",
            )
        if radius_km > MAX_RADIUS_KM:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"radius_km must not exceed {MAX_RADIUS_KM}.",
            )

    def _cache_key(self, latitude: float, longitude: float, radius_km: float) -> str:
        return f"{round(latitude, 3)}:{round(longitude, 3)}:{round(radius_km, 1)}"

    def _get_cached_response(self, key: str) -> SolarStoresResponse | None:
        cached = self._cache.get(key)
        if not cached:
            return None

        created_at, response = cached
        if time.time() - created_at > CACHE_TTL_SECONDS:
            self._cache.pop(key, None)
            return None

        return response

    def _set_cache(self, key: str, response: SolarStoresResponse) -> None:
        self._cache[key] = (time.time(), response)

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        from math import asin, cos, radians, sin, sqrt

        earth_radius_km = 6371.0
        d_lat = radians(lat2 - lat1)
        d_lon = radians(lon2 - lon1)
        a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
        return 2 * earth_radius_km * asin(sqrt(a))

    def _to_float(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
