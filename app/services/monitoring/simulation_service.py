import math
import random
from datetime import datetime, timedelta

from app.schemas.monitoring import (
    MonitoringDataPoint,
    MonitoringSimulationRequest,
    MonitoringSimulationResponse,
)


class SimulationService:
    def simulate(self, request: MonitoringSimulationRequest) -> MonitoringSimulationResponse:
        data_points = []
        alerts = []

        start_time = datetime.utcnow()
        battery_level = (
            18.0
            if request.battery_capacity_kwh and request.scenario.lower() == "batterie_faible"
            else 80.0
            if request.battery_capacity_kwh
            else None
        )

        for hour in range(request.duration_hours):
            timestamp = start_time + timedelta(hours=hour)

            production = self._simulate_production(
                hour=hour,
                total_power_kwp=request.total_power_kwp,
                scenario=request.scenario
            )
            irradiance = self._simulate_irradiance(
                hour=hour,
                scenario=request.scenario
            )

            consumption = self._simulate_consumption(
                hour=hour,
                daily_consumption_kwh=request.daily_consumption_kwh,
                scenario=request.scenario
            )

            temperature = self._simulate_temperature(hour)
            panel_temperature = self._simulate_panel_temperature(
                ambient_temperature=temperature,
                irradiance_w_m2=irradiance
            )
            energy_balance = production - consumption
            grid_import = max(consumption - production, 0)
            grid_export = max(production - consumption, 0)
            performance_ratio = self._calculate_performance_ratio(
                production_kwh=production,
                total_power_kwp=request.total_power_kwp,
                irradiance_w_m2=irradiance
            )

            if battery_level is not None:
                battery_level = self._update_battery_level(
                    current_level=battery_level,
                    production_kwh=production,
                    consumption_kwh=consumption,
                    battery_capacity_kwh=request.battery_capacity_kwh or 1
                )

            system_status = self._determine_status(
                production_kwh=production,
                consumption_kwh=consumption,
                battery_level=battery_level,
                scenario=request.scenario
            )

            data_point = MonitoringDataPoint(
                timestamp=timestamp,
                production_kwh=round(production, 2),
                consumption_kwh=round(consumption, 2),
                battery_level_percent=round(battery_level, 2) if battery_level is not None else None,
                temperature=round(temperature, 2),
                irradiance_w_m2=round(irradiance, 2),
                panel_temperature_c=round(panel_temperature, 2),
                performance_ratio_percent=round(performance_ratio, 2),
                energy_balance_kwh=round(energy_balance, 2),
                grid_import_kwh=round(grid_import, 2),
                grid_export_kwh=round(grid_export, 2),
                system_status=system_status
            )

            data_points.append(data_point)

            if system_status != "normal":
                alerts.append(
                    {
                        "timestamp": timestamp.isoformat(),
                        "severity": self._severity_from_status(system_status),
                        "alert_type": system_status,
                        "message": self._alert_message(system_status)
                    }
                )

        summary = self._build_summary(data_points)

        return MonitoringSimulationResponse(
            simulation_id=None,
            scenario=request.scenario,
            duration_hours=request.duration_hours,
            data=data_points,
            alerts=alerts,
            summary=summary
        )

    def _simulate_production(self, hour: int, total_power_kwp: float, scenario: str) -> float:
        hour_of_day = hour % 24

        if hour_of_day < 6 or hour_of_day > 18:
            base_production = 0.0
        else:
            solar_factor = math.sin((hour_of_day - 6) / 12 * math.pi)
            base_production = total_power_kwp * solar_factor

        scenario = scenario.lower()

        if scenario == "panne":
            if 10 <= hour_of_day <= 15:
                base_production *= 0.15

        elif scenario == "meteo_defavorable":
            base_production *= 0.45

        elif scenario == "ombrage":
            base_production *= 0.65

        noise = random.uniform(0.9, 1.1)

        return max(base_production * noise, 0)

    def _simulate_irradiance(self, hour: int, scenario: str) -> float:
        hour_of_day = hour % 24

        if hour_of_day < 6 or hour_of_day > 18:
            irradiance = 0.0
        else:
            solar_factor = math.sin((hour_of_day - 6) / 12 * math.pi)
            irradiance = 950 * solar_factor

        scenario = scenario.lower()

        if scenario == "panne":
            irradiance *= 0.95
        elif scenario == "meteo_defavorable":
            irradiance *= 0.45
        elif scenario == "ombrage":
            irradiance *= 0.65
        elif scenario == "batterie_faible":
            irradiance *= 0.85

        return max(irradiance * random.uniform(0.95, 1.05), 0)

    def _simulate_consumption(self, hour: int, daily_consumption_kwh: float, scenario: str) -> float:
        hour_of_day = hour % 24
        average_hourly = daily_consumption_kwh / 24

        if 7 <= hour_of_day <= 9:
            factor = 1.5
        elif 18 <= hour_of_day <= 22:
            factor = 1.8
        elif 0 <= hour_of_day <= 5:
            factor = 0.5
        else:
            factor = 1.0

        if scenario.lower() == "surcharge":
            factor *= 2.2

        if scenario.lower() == "batterie_faible":
            factor *= 1.15

        noise = random.uniform(0.85, 1.15)

        return max(average_hourly * factor * noise, 0)

    def _simulate_temperature(self, hour: int) -> float:
        hour_of_day = hour % 24

        base_temp = 22
        daily_variation = 8 * math.sin((hour_of_day - 6) / 24 * 2 * math.pi)
        noise = random.uniform(-1.5, 1.5)

        return base_temp + daily_variation + noise

    def _simulate_panel_temperature(
        self,
        ambient_temperature: float,
        irradiance_w_m2: float
    ) -> float:
        return ambient_temperature + (irradiance_w_m2 / 1000) * 24

    def _calculate_performance_ratio(
        self,
        production_kwh: float,
        total_power_kwp: float,
        irradiance_w_m2: float
    ) -> float:
        if irradiance_w_m2 <= 50 or total_power_kwp <= 0:
            return 0

        theoretical_production = total_power_kwp * irradiance_w_m2 / 1000

        if theoretical_production <= 0:
            return 0

        return min((production_kwh / theoretical_production) * 100, 100)

    def _update_battery_level(
        self,
        current_level: float,
        production_kwh: float,
        consumption_kwh: float,
        battery_capacity_kwh: float
    ) -> float:
        energy_balance = production_kwh - consumption_kwh
        variation_percent = (energy_balance / battery_capacity_kwh) * 100

        new_level = current_level + variation_percent

        return min(max(new_level, 0), 100)

    def _determine_status(
        self,
        production_kwh: float,
        consumption_kwh: float,
        battery_level: float | None,
        scenario: str
    ) -> str:
        if scenario.lower() == "panne" and production_kwh < 0.2:
            return "probable_panel_failure"

        if scenario.lower() == "batterie_faible":
            return "low_battery"

        if battery_level is not None and battery_level < 20:
            return "low_battery"

        if consumption_kwh > production_kwh * 3 and production_kwh > 0:
            return "high_consumption"

        if scenario.lower() == "surcharge":
            return "overload"

        return "normal"

    def _severity_from_status(self, status: str) -> str:
        severities = {
            "probable_panel_failure": "critical",
            "low_battery": "important",
            "high_consumption": "warning",
            "overload": "critical"
        }

        return severities.get(status, "info")

    def _alert_message(self, status: str) -> str:
        messages = {
            "probable_panel_failure": "Baisse anormale de production : panne probable d'un panneau ou problème de câblage.",
            "low_battery": "Niveau de batterie faible. Réduire la consommation ou recharger.",
            "high_consumption": "Consommation élevée par rapport à la production.",
            "overload": "Surcharge détectée dans le système."
        }

        return messages.get(status, "État système à vérifier.")

    def _build_summary(self, data_points: list[MonitoringDataPoint]) -> dict:
        total_production = sum(point.production_kwh for point in data_points)
        total_consumption = sum(point.consumption_kwh for point in data_points)

        battery_values = [
            point.battery_level_percent
            for point in data_points
            if point.battery_level_percent is not None
        ]

        average_battery = (
            sum(battery_values) / len(battery_values)
            if battery_values
            else None
        )

        abnormal_points = [
            point
            for point in data_points
            if point.system_status != "normal"
        ]

        return {
            "total_production_kwh": round(total_production, 2),
            "total_consumption_kwh": round(total_consumption, 2),
            "energy_balance_kwh": round(total_production - total_consumption, 2),
            "average_battery_level_percent": round(average_battery, 2) if average_battery is not None else None,
            "abnormal_points_count": len(abnormal_points),
            "global_status": "normal" if not abnormal_points else "needs_attention"
        }
