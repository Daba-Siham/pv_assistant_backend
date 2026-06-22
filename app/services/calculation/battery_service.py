from app.schemas.calculation import BatteryEstimationRequest, BatteryEstimationResponse


class BatteryService:
    def estimate_battery(self, request: BatteryEstimationRequest) -> BatteryEstimationResponse:
        installation_type = request.installation_type.lower()

        if installation_type == "on-grid" or request.autonomy_days == 0:
            return BatteryEstimationResponse(
                required_capacity_kwh=0,
                required_capacity_ah=0,
                autonomy_days=0,
                battery_voltage=request.battery_voltage,
                battery_needed=False
            )

        required_capacity_kwh = (
            request.daily_consumption_kwh
            * request.autonomy_days
            / (request.dod * request.battery_efficiency)
        )

        required_capacity_ah = (
            required_capacity_kwh * 1000
        ) / request.battery_voltage

        return BatteryEstimationResponse(
            required_capacity_kwh=round(required_capacity_kwh, 2),
            required_capacity_ah=round(required_capacity_ah, 2),
            autonomy_days=request.autonomy_days,
            battery_voltage=request.battery_voltage,
            battery_needed=True
        )