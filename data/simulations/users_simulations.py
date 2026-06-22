# app/data/users_simulations.py
# Simulations 24h pré-calculées pour les 7 users
# NE CONTIENT PAS : ville, panneaux, batteries, onduleur, coût, ROI
# CONTIENT UNIQUEMENT : données dynamiques 25min par 25min

import math
import random
from datetime import datetime, timedelta


def _generate_day(
    total_power_kwp: float,
    daily_consumption_kwh: float,
    battery_capacity_kwh: float,
    battery_start: float,
    scenarios_by_hour: dict,
    base_temp: float = 22.0,
    irradiance_factor: float = 1.0,
    interval_minutes: int = 25  # <-- NOUVEAU PARAMÈTRE
    ):
    """
    Génère des points de données pour une journée complète par intervalle de X minutes.
    """
    data = []
    alerts = []
    battery_level = battery_start
    start_time = datetime(2024, 6, 21, 0, 0, 0)

    # Fraction d'heure (ex: 25 min = 0.4167 heure)
    time_fraction = interval_minutes / 60.0
    total_minutes_in_day = 24 * 60

    def get_scenario(hour_float):
        scenario = "normal"
        for h in sorted(scenarios_by_hour.keys()):
            if hour_float >= h:
                scenario = scenarios_by_hour[h]
        return scenario

    # On boucle sur les minutes de la journée par pas de 25
    for minutes in range(0, total_minutes_in_day, interval_minutes):
        timestamp = start_time + timedelta(minutes=minutes)
        
        # On convertit les minutes en heure décimale (ex: 14h25 = 14.4166)
        hour = minutes / 60.0
        scenario = get_scenario(hour)

        # --- 1. Production ---
        if hour < 6 or hour > 18:
            base_prod = 0.0
        else:
            solar_factor = math.sin((hour - 6) / 12 * math.pi)
            # On multiplie par time_fraction car on calcule sur 25 min et non 1 heure
            base_prod = total_power_kwp * solar_factor * time_fraction

        if scenario == "panne":
            base_prod *= 0.15
        elif scenario == "nuages":
            base_prod *= 0.45
        elif scenario == "ombrage":
            base_prod *= 0.65

        production = round(max(base_prod * random.uniform(0.92, 1.08), 0), 3)

        # --- 2. Irradiance ---
        if hour < 6 or hour > 18:
            irradiance = 0.0
        else:
            solar_factor = math.sin((hour - 6) / 12 * math.pi)
            irradiance = 950 * solar_factor * irradiance_factor
            if scenario == "nuages":
                irradiance *= 0.45
            elif scenario == "panne":
                irradiance *= 0.95
        irradiance = round(max(irradiance * random.uniform(0.95, 1.05), 0), 2)

        # --- 3. Consommation ---
        # Répartit la conso journalière sur l'intervalle de 25 minutes
        avg_per_interval = daily_consumption_kwh * (interval_minutes / (24 * 60))
        
        if 7 <= hour <= 9:
            factor = 1.5
        elif 18 <= hour <= 22:
            factor = 1.8
        elif 0 <= hour <= 5:
            factor = 0.5
        else:
            factor = 1.0

        if scenario == "surcharge":
            factor *= 2.2

        consumption = round(max(avg_per_interval * factor * random.uniform(0.88, 1.12), 0), 3)

        # --- 4. Température ---
        temp = base_temp + 8 * math.sin((hour - 6) / 24 * 2 * math.pi) + random.uniform(-1.5, 1.5)
        temp = round(temp, 2)
        panel_temp = round(temp + (irradiance / 1000) * 24, 2)

        # --- 5. Batterie ---
        energy_balance = production - consumption
        variation = (energy_balance / battery_capacity_kwh) * 100
        battery_level = round(min(max(battery_level + variation, 0), 100), 2)

        # --- 6. Performance ratio ---
        if irradiance > 50 and total_power_kwp > 0:
            # Production théorique sur cet intervalle
            theoretical = (total_power_kwp * irradiance / 1000) * time_fraction
            pr = round(min((production / theoretical) * 100, 100), 2) if theoretical > 0 else 0
        else:
            pr = 0

        # --- 7. Balance & Grid ---
        balance = round(production - consumption, 3)
        grid_import = round(max(consumption - production, 0), 3)
        grid_export = round(max(production - consumption, 0), 3)

        # --- 8. Status ---
        # Le seuil de panne doit aussi s'adapter à la fraction de temps
        prod_threshold = 0.2 * time_fraction 
        if scenario == "panne" and production < prod_threshold:
            status = "probable_panel_failure"
        elif scenario == "surcharge":
            status = "overload"
        elif battery_level < 20:
            status = "low_battery"
        elif consumption > production * 3 and production > 0:
            status = "high_consumption"
        else:
            status = "normal"

        # Formatage de l'heure lisible (ex: "14h25")
        time_str = timestamp.strftime("%Hh%M")

        point = {
            "time": time_str, # Nouveau champ pratique pour le frontend
            "hour": hour,     # Heure décimale (utile pour les graphiques)
            "timestamp": timestamp.isoformat(),
            "production_kwh": production,
            "consumption_kwh": consumption,
            "battery_pct": battery_level,
            "battery_level_percent": battery_level,
            "irradiance": irradiance,
            "irradiance_w_m2": irradiance,
            "ambient_temp": temp,
            "temperature": temp,
            "panelTemp": panel_temp,
            "panel_temperature_c": panel_temp,
            "pr": pr,
            "performance_ratio_percent": pr,
            "balance": balance,
            "energy_balance_kwh": balance,
            "grid_import": grid_import,
            "grid_import_kwh": grid_import,
            "grid_export": grid_export,
            "grid_export_kwh": grid_export,
            "system_status": status,
        }

        data.append(point)

        if status != "normal":
            alerts.append({
                "timestamp": timestamp.isoformat(),
                "severity": "critical" if status in ["probable_panel_failure", "overload"] else "important",
                "alert_type": status,
                "message": {
                    "probable_panel_failure": "Baisse anormale de production détectée.",
                    "overload": "Surcharge électrique détectée.",
                    "low_battery": "Niveau de batterie critique.",
                    "high_consumption": "Consommation anormalement élevée.",
                }.get(status, "Anomalie détectée.")
            })

    total_prod = round(sum(d["production_kwh"] for d in data), 2)
    total_conso = round(sum(d["consumption_kwh"] for d in data), 2)
    battery_values = [d["battery_pct"] for d in data]
    avg_battery = round(sum(battery_values) / len(battery_values), 2)
    abnormal = [d for d in data if d["system_status"] != "normal"]

    summary = {
        "total_production_kwh": total_prod,
        "total_consumption_kwh": total_conso,
        "energy_balance_kwh": round(total_prod - total_conso, 2),
        "average_battery_level_percent": avg_battery,
        "abnormal_points_count": len(abnormal),
        "global_status": "normal" if not abnormal else "needs_attention"
    }

    return {"data": data, "alerts": alerts, "summary": summary}


# ============================================================
# 7 SIMULATIONS — une par user_id
# Paramètres : uniquement données dynamiques
# PAS de : ville, marque, modèle, coût, ROI
# ============================================================

random.seed(42)

USERS_SIMULATIONS = {

    # User 1 — Journée normale optimale
    1: _generate_day(
        total_power_kwp=4.8,
        daily_consumption_kwh=10.5,
        battery_capacity_kwh=14.0,
        battery_start=80.0,
        scenarios_by_hour={0: "normal"},
        base_temp=24.0,
        irradiance_factor=1.0,
    ),

    # User 2 — Normal matin, surcharge soirée (18h-22h)
    2: _generate_day(
        total_power_kwp=3.2,
        daily_consumption_kwh=8.0,
        battery_capacity_kwh=7.0,
        battery_start=75.0,
        scenarios_by_hour={0: "normal", 18: "surcharge", 22: "normal"},
        base_temp=22.0,
        irradiance_factor=0.95,
    ),

    # User 3 — Panne panneau 10h-15h
    3: _generate_day(
        total_power_kwp=6.4,
        daily_consumption_kwh=15.0,
        battery_capacity_kwh=21.0,
        battery_start=85.0,
        scenarios_by_hour={0: "normal", 10: "panne", 15: "normal"},
        base_temp=26.0,
        irradiance_factor=1.0,
    ),

    # User 4 — Batterie faible toute la nuit + normal journée
    4: _generate_day(
        total_power_kwp=2.4,
        daily_consumption_kwh=6.0,
        battery_capacity_kwh=5.0,
        battery_start=15.0,  # démarre bas
        scenarios_by_hour={0: "normal"},
        base_temp=20.0,
        irradiance_factor=0.9,
    ),

    # User 5 — Nuages 11h-13h, normal reste
    5: _generate_day(
        total_power_kwp=5.6,
        daily_consumption_kwh=12.0,
        battery_capacity_kwh=17.5,
        battery_start=70.0,
        scenarios_by_hour={0: "normal", 11: "nuages", 13: "normal"},
        base_temp=23.0,
        irradiance_factor=0.85,
    ),

    # User 6 — Surcharge totale journée
    6: _generate_day(
        total_power_kwp=4.0,
        daily_consumption_kwh=20.0,
        battery_capacity_kwh=10.0,
        battery_start=60.0,
        scenarios_by_hour={0: "normal", 8: "surcharge", 23: "normal"},
        base_temp=25.0,
        irradiance_factor=1.0,
    ),

    # User 7 — Journée parfaite, meilleure production
    7: _generate_day(
        total_power_kwp=8.0,
        daily_consumption_kwh=18.0,
        battery_capacity_kwh=28.0,
        battery_start=90.0,
        scenarios_by_hour={0: "normal"},
        base_temp=28.0,
        irradiance_factor=1.1,
    ),
}