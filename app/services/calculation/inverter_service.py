from app.schemas.calculation import InverterEstimationRequest, InverterEstimationResponse


class InverterService:
    def estimate_inverter(self, request: InverterEstimationRequest) -> InverterEstimationResponse:
        if request.max_load_kw is not None:
            minimum_power = max(request.total_panel_power_kwp, request.max_load_kw)
        else:
            minimum_power = request.total_panel_power_kwp

        recommended_power = minimum_power * request.margin

        return InverterEstimationResponse(
            recommended_power_kw=round(recommended_power, 2),
            minimum_power_kw=round(minimum_power, 2),
            inverter_margin=request.margin
        )