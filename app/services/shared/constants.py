INSTALLATION_TYPES = ["on-grid", "off-grid", "hybride"]

ORIENTATIONS = [
    "sud",
    "nord",
    "est",
    "ouest",
    "sud-est",
    "sud-ouest",
    "nord-est",
    "nord-ouest"
]

MONITORING_SCENARIOS = [
    "normal",
    "panne",
    "surcharge",
    "meteo_defavorable",
    "ombrage"
]

ALERT_SEVERITIES = [
    "info",
    "warning",
    "important",
    "critical"
]

DEFAULT_PANEL_POWER_W = 450
DEFAULT_PANEL_AREA_M2 = 2.0

DEFAULT_PERFORMANCE_RATIO = 0.75
DEFAULT_SHADE_FACTOR = 1.0

DEFAULT_BATTERY_VOLTAGE = 48
DEFAULT_BATTERY_DOD = 0.8
DEFAULT_BATTERY_EFFICIENCY = 0.9
DEFAULT_BATTERY_CAPACITY_KWH = 2.4

DEFAULT_INVERTER_MARGIN = 1.25

DEFAULT_ELECTRICITY_PRICE = 1.5
DEFAULT_ANNUAL_MAINTENANCE_COST = 300

DEFAULT_INSTALLATION_COST = 3000
DEFAULT_CABLE_COST = 500
DEFAULT_PANEL_UNIT_PRICE = 1500
DEFAULT_BATTERY_UNIT_PRICE = 3000
DEFAULT_INVERTER_UNIT_PRICE = 5000

DEFAULT_PEAK_SUN_HOURS = 5.5
DEFAULT_TEMPERATURE_AVG = 25

STANDARD_CABLE_SECTIONS_MM2 = [
    1.5,
    2.5,
    4,
    6,
    10,
    16,
    25,
    35,
    50,
    70,
    95,
    120
]

MOROCCO_DEFAULT_CITIES = {
    "casablanca": {
        "latitude": 33.5731,
        "longitude": -7.5898,
        "ghi": 5.3,
        "temperature_avg": 22,
        "peak_sun_hours": 5.3
    },
    "rabat": {
        "latitude": 34.0209,
        "longitude": -6.8416,
        "ghi": 5.4,
        "temperature_avg": 21,
        "peak_sun_hours": 5.4
    },
    "marrakech": {
        "latitude": 31.6295,
        "longitude": -7.9811,
        "ghi": 6.1,
        "temperature_avg": 27,
        "peak_sun_hours": 6.1
    },
    "nador": {
        "latitude": 35.1688,
        "longitude": -2.9335,
        "ghi": 5.6,
        "temperature_avg": 23,
        "peak_sun_hours": 5.6
    },
    "tanger": {
        "latitude": 35.7595,
        "longitude": -5.8340,
        "ghi": 5.1,
        "temperature_avg": 20,
        "peak_sun_hours": 5.1
    },
    "agadir": {
        "latitude": 30.4278,
        "longitude": -9.5981,
        "ghi": 5.9,
        "temperature_avg": 24,
        "peak_sun_hours": 5.9
    }
}