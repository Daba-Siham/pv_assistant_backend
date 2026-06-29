import math
from pathlib import Path

import pandas as pd


def round_value(value: float | None, digits: int = 2) -> float | None:
    if value is None:
        return None

    return round(float(value), digits)


def safe_divide(value: float, reference: float, default: float = 0) -> float:
    if reference == 0:
        return default

    return value / reference


def load_csv_file(file_path: Path) -> pd.DataFrame:
    if not file_path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(file_path)
    except Exception:
        return pd.DataFrame()


def normalize_text(text: str | None) -> str:
    if text is None:
        return ""

    return text.lower().strip()


def normalize_installation_type(value) -> str:
    return str(value or "").lower().replace("_", "-").strip()


def is_on_grid(value) -> bool:
    normalized = normalize_installation_type(value)
    return (
        normalized in {"on-grid", "ongrid", "connectee-au-reseau", "connectée-au-réseau"}
        or "on-grid" in normalized
        or "réseau" in normalized
        or "reseau" in normalized
    )


def has_battery_system(installation_type, battery_capacity_kwh=0) -> bool:
    normalized = normalize_installation_type(installation_type)

    if "on-grid" in normalized or "reseau" in normalized or "réseau" in normalized:
        return False

    try:
        battery_capacity = float(battery_capacity_kwh or 0)
    except (TypeError, ValueError):
        battery_capacity = 0

    return (
        "hybrid" in normalized
        or "hybride" in normalized
        or "off-grid" in normalized
        or battery_capacity > 0
    )


def haversine_distance(
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


def nearest_standard_value(value: float, standards: list[float]) -> float:
    for standard in standards:
        if standard >= value:
            return standard

    return standards[-1]


def orientation_factor(orientation: str | None) -> float:
    orientation = normalize_text(orientation)

    factors = {
        "sud": 1.0,
        "sud-est": 0.95,
        "sud-ouest": 0.95,
        "est": 0.85,
        "ouest": 0.85,
        "nord-est": 0.65,
        "nord-ouest": 0.65,
        "nord": 0.55
    }

    return factors.get(orientation, 1.0)


def temperature_factor(temperature_avg: float | None) -> float:
    if temperature_avg is None:
        return 1.0

    if temperature_avg <= 25:
        return 1.0

    loss = (temperature_avg - 25) * 0.004

    return max(0.75, 1 - loss)


def installation_requires_battery(installation_type: str | None) -> bool:
    return has_battery_system(installation_type)
