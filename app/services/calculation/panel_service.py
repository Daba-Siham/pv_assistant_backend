import math

from app.schemas.calculation import PanelEstimationRequest, PanelEstimationResponse


class PanelService:
    def estimate_panels(self, request: PanelEstimationRequest) -> PanelEstimationResponse:
        production_per_panel = (
            request.panel_power_w / 1000
            * request.peak_sun_hours
            * request.performance_ratio
            * request.shade_factor
        )

        if production_per_panel <= 0:
            panel_count = 0
        else:
            panel_count = math.ceil(request.daily_consumption_kwh / production_per_panel)

        total_power_kwp = round((panel_count * request.panel_power_w) / 1000, 2)
        estimated_daily_production = round(panel_count * production_per_panel, 2)
        required_area = round(panel_count * request.panel_area_m2, 2)

        is_area_sufficient = True

        if request.available_area_m2 is not None:
            is_area_sufficient = required_area <= request.available_area_m2

        return PanelEstimationResponse(
            panel_count=panel_count,
            panel_power_w=request.panel_power_w,
            total_power_kwp=total_power_kwp,
            estimated_daily_production_kwh=estimated_daily_production,
            required_area_m2=required_area,
            is_area_sufficient=is_area_sufficient
        )