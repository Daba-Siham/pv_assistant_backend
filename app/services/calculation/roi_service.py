from app.schemas.calculation import ROIRequest, ROIResponse


class ROIService:
    def calculate_roi(self, request: ROIRequest) -> ROIResponse:
        annual_saving = request.annual_production_kwh * request.electricity_price
        net_annual_saving = annual_saving - request.annual_maintenance_cost

        if net_annual_saving <= 0:
            roi_years = 0
            message = "Le retour sur investissement n'est pas rentable avec ces hypothèses."
        else:
            roi_years = request.total_cost / net_annual_saving

            if roi_years <= 5:
                message = "Très bonne rentabilité estimée."
            elif roi_years <= 10:
                message = "Rentabilité correcte estimée."
            else:
                message = "Rentabilité longue, à optimiser."

        return ROIResponse(
            annual_saving=round(annual_saving, 2),
            net_annual_saving=round(net_annual_saving, 2),
            roi_years=round(roi_years, 2),
            profitability_message=message
        )