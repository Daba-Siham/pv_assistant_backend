from app.schemas.monitoring import (
    EnergyPredictionRequest,
    EnergyPredictionResponse,
)


class PredictionService:
    def predict_energy(self, request: EnergyPredictionRequest) -> EnergyPredictionResponse:
        peak_sun_hours = self._estimate_peak_sun_hours(
            city=request.city,
            weather_condition=request.weather_condition
        )

        temperature_factor = self._temperature_factor(request.temperature_avg)

        daily_production = (
            request.total_power_kwp
            * peak_sun_hours
            * 0.75
            * temperature_factor
        )

        estimated_total_production = daily_production * request.prediction_days

        battery_risk = self._estimate_battery_risk(
            estimated_production_kwh=estimated_total_production,
            prediction_days=request.prediction_days,
            weather_condition=request.weather_condition
        )

        recommendations = self._build_recommendations(
            weather_condition=request.weather_condition,
            battery_risk=battery_risk,
            temperature_avg=request.temperature_avg
        )

        return EnergyPredictionResponse(
            prediction_days=request.prediction_days,
            estimated_production_kwh=round(estimated_total_production, 2),
            estimated_consumption_kwh=None,
            battery_risk=battery_risk,
            recommendations=recommendations
        )

    def _estimate_peak_sun_hours(
        self,
        city: str | None,
        weather_condition: str | None
    ) -> float:
        base_hsp = 5.5

        if city:
            city_lower = city.lower()

            if city_lower in ["marrakech", "agadir", "ouarzazate"]:
                base_hsp = 6.0
            elif city_lower in ["tanger", "tetouan"]:
                base_hsp = 5.0
            elif city_lower in ["nador", "oujda"]:
                base_hsp = 5.6

        if weather_condition:
            weather = weather_condition.lower()

            if weather in ["nuageux", "cloudy"]:
                base_hsp *= 0.65
            elif weather in ["pluie", "rain", "rainy"]:
                base_hsp *= 0.4
            elif weather in ["ensoleille", "ensoleillé", "sunny"]:
                base_hsp *= 1.0

        return base_hsp

    def _temperature_factor(self, temperature_avg: float | None) -> float:
        if temperature_avg is None:
            return 1.0

        if temperature_avg <= 25:
            return 1.0

        loss = (temperature_avg - 25) * 0.004

        return max(0.75, 1 - loss)

    def _estimate_battery_risk(
        self,
        estimated_production_kwh: float,
        prediction_days: int,
        weather_condition: str | None
    ) -> str:
        average_daily_production = estimated_production_kwh / prediction_days

        if weather_condition and weather_condition.lower() in ["pluie", "rain", "rainy"]:
            return "high"

        if average_daily_production < 3:
            return "medium"

        return "low"

    def _build_recommendations(
        self,
        weather_condition: str | None,
        battery_risk: str,
        temperature_avg: float | None
    ) -> list[str]:
        recommendations = []

        if battery_risk == "high":
            recommendations.append(
                "Risque élevé de batterie faible : réduire les consommations non essentielles."
            )
        elif battery_risk == "medium":
            recommendations.append(
                "Risque moyen : surveiller le niveau de batterie pendant la période prévue."
            )
        else:
            recommendations.append(
                "Production prévue correcte selon les hypothèses utilisées."
            )

        if weather_condition and weather_condition.lower() in ["nuageux", "cloudy", "pluie", "rain", "rainy"]:
            recommendations.append(
                "La météo défavorable peut réduire fortement la production solaire."
            )

        if temperature_avg and temperature_avg > 35:
            recommendations.append(
                "Température élevée : le rendement des panneaux peut diminuer."
            )

        return recommendations