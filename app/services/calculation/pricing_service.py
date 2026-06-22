from app.schemas.calculation import CostEstimationRequest, CostEstimationResponse


class PricingService:
    def estimate_cost(self, request: CostEstimationRequest) -> CostEstimationResponse:
        panels_cost = request.panel_count * request.panel_unit_price
        batteries_cost = request.battery_count * request.battery_unit_price
        inverter_cost = request.inverter_count * request.inverter_unit_price

        total_cost = (
            panels_cost
            + batteries_cost
            + inverter_cost
            + request.installation_cost
            + request.cable_cost
            + request.maintenance_cost
        )

        return CostEstimationResponse(
            panels_cost=round(panels_cost, 2),
            batteries_cost=round(batteries_cost, 2),
            inverter_cost=round(inverter_cost, 2),
            installation_cost=round(request.installation_cost, 2),
            cable_cost=round(request.cable_cost, 2),
            maintenance_cost=round(request.maintenance_cost, 2),
            total_cost=round(total_cost, 2)
        )