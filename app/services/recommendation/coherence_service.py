from typing import Any

from app.config import settings
from app.schemas.recommendation import CoherenceCheck, InstallationType, PVRecommendationRequest


class PVCoherenceService:
    PANEL_AREA_M2 = 2.0

    def run_checks(
        self,
        request: PVRecommendationRequest,
        ml_result: dict[str, Any],
    ) -> list[CoherenceCheck]:
        checks = [
            self._battery_policy_check(request, ml_result),
            self._surface_check(request, ml_result),
            self._budget_check(request, ml_result),
            self._inverter_check(ml_result),
            self._battery_capacity_check(request, ml_result),
        ]

        return [check for check in checks if check is not None]

    def _battery_policy_check(
        self,
        request: PVRecommendationRequest,
        ml_result: dict[str, Any],
    ) -> CoherenceCheck:
        battery_needed = self._as_bool(ml_result.get("battery_needed"))
        battery_count = self._as_float(ml_result.get("battery_count")) or 0
        battery_capacity = self._as_float(ml_result.get("battery_capacity_kwh")) or 0
        has_battery = battery_needed or battery_count > 0 or battery_capacity > 0

        if request.installation_type == InstallationType.ON_GRID:
            status = "ok" if not has_battery else "warning"
            message = (
                "Installation on_grid: la batterie est optionnelle, pas obligatoire."
                if has_battery
                else "Installation on_grid: batterie non necessaire."
            )
            return CoherenceCheck(code="battery_policy", status=status, message=message)

        status = "ok" if has_battery else "error"
        return CoherenceCheck(
            code="battery_policy",
            status=status,
            message="Installation hybrid/off_grid: une batterie est obligatoire.",
            expected="battery_capacity_kwh > 0 ou battery_count > 0",
            actual={"battery_needed": battery_needed, "battery_count": battery_count},
        )

    def _surface_check(
        self,
        request: PVRecommendationRequest,
        ml_result: dict[str, Any],
    ) -> CoherenceCheck:
        required_area = self._as_float(ml_result.get("required_area_m2"))

        if required_area is None:
            panel_count = self._as_float(ml_result.get("panel_count")) or 0
            required_area = panel_count * self.PANEL_AREA_M2

        status = "ok" if request.available_area_m2 >= required_area else "error"
        return CoherenceCheck(
            code="surface",
            status=status,
            message=(
                "Surface disponible suffisante."
                if status == "ok"
                else "Surface disponible insuffisante pour le nombre de panneaux recommande."
            ),
            expected=round(required_area, 2),
            actual=request.available_area_m2,
        )

    def _budget_check(
        self,
        request: PVRecommendationRequest,
        ml_result: dict[str, Any],
    ) -> CoherenceCheck | None:
        if request.budget is None:
            return None

        estimated_cost = (
            self._as_float(ml_result.get("estimated_cost"))
            or self._as_float(ml_result.get("total_cost"))
            or self._as_float(ml_result.get("cost"))
        )

        if estimated_cost is None:
            return CoherenceCheck(
                code="budget",
                status="warning",
                message="Budget non verifie: le modele n'a pas fourni de cout estime.",
                expected=f"<= {request.budget}",
                actual=None,
            )

        status = "ok" if estimated_cost <= request.budget else "warning"
        return CoherenceCheck(
            code="budget",
            status=status,
            message=(
                "Budget compatible avec l'estimation."
                if status == "ok"
                else "Budget inferieur au cout estime."
            ),
            expected=f"<= {request.budget}",
            actual=estimated_cost,
        )

    def _inverter_check(self, ml_result: dict[str, Any]) -> CoherenceCheck:
        panel_power = (
            self._as_float(ml_result.get("total_panel_power_kwp"))
            or self._as_float(ml_result.get("total_power_kwp"))
            or self._as_float(ml_result.get("pv_power_kwp"))
        )
        inverter_power = (
            self._as_float(ml_result.get("inverter_power_kw"))
            or self._as_float(ml_result.get("recommended_inverter_power_kw"))
        )

        if panel_power is None or inverter_power is None:
            return CoherenceCheck(
                code="inverter_power",
                status="warning",
                message="Cohérence onduleur non verifiee: puissance panneaux ou onduleur absente.",
            )

        lower = panel_power * 0.8
        upper = panel_power * 1.5
        status = "ok" if lower <= inverter_power <= upper else "warning"

        return CoherenceCheck(
            code="inverter_power",
            status=status,
            message=(
                "Puissance onduleur coherente avec la puissance panneaux."
                if status == "ok"
                else "Puissance onduleur a verifier par rapport a la puissance panneaux."
            ),
            expected=f"{round(lower, 2)} - {round(upper, 2)} kW",
            actual=f"{inverter_power} kW",
        )

    def _battery_capacity_check(
        self,
        request: PVRecommendationRequest,
        ml_result: dict[str, Any],
    ) -> CoherenceCheck | None:
        if request.autonomy_days <= 0:
            return None

        if request.installation_type == InstallationType.ON_GRID:
            return None

        required_capacity = (
            request.normalized_daily_consumption_kwh
            * request.autonomy_days
            / (settings.DEFAULT_BATTERY_DOD * settings.DEFAULT_BATTERY_EFFICIENCY)
        )
        predicted_capacity = self._as_float(ml_result.get("battery_capacity_kwh")) or 0
        status = "ok" if predicted_capacity >= required_capacity * 0.9 else "warning"

        return CoherenceCheck(
            code="battery_capacity",
            status=status,
            message=(
                "Capacite batterie coherente avec l'autonomie demandee."
                if status == "ok"
                else "Capacite batterie probablement insuffisante pour l'autonomie demandee."
            ),
            expected=round(required_capacity, 2),
            actual=predicted_capacity,
        )

    @staticmethod
    def _as_float(value: Any) -> float | None:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _as_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"true", "yes", "oui", "1", "needed", "necessaire"}
        return bool(value)
