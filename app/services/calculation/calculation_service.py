# app/services/calculation/calculation_service.py

import math
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]

INSTALLATION_CSV = BASE_DIR / "data/materials/installation_costs.csv"
CO2_CSV = BASE_DIR / "data/materials/co2_factors.csv"
ELECTRICITY_CSV = BASE_DIR / "data/materials/electricity_prices.csv"
PANELS_CSV = BASE_DIR / "data/materials/panels.csv"
BATTERIES_CSV = BASE_DIR / "data/materials/batteries.csv"
INVERTERS_CSV = BASE_DIR / "data/materials/inverters.csv"
IRRADIATION_CSV = BASE_DIR / "data/materials/irradiation.csv"



installation_df = pd.read_csv(INSTALLATION_CSV)
co2_df = pd.read_csv(CO2_CSV)
electricity_df = pd.read_csv(ELECTRICITY_CSV)
panels_df = pd.read_csv(PANELS_CSV)
batteries_df = pd.read_csv(BATTERIES_CSV)
inverters_df = pd.read_csv(INVERTERS_CSV)
irradiation_df = pd.read_csv(IRRADIATION_CSV)


def calculate_system(data):

    city = data.city
    daily_consumption = data.daily_consumption_kwh
    available_area = data.available_area_m2
    budget = data.budget
    orientation = data.orientation
    installation_type = data.installation_type
    roof_type = data.roof_type

    # =====================================================
    # DONNÉES SOLAIRES
    # =====================================================

    city_row = irradiation_df[
        irradiation_df["city"].str.lower() == city.lower()
    ]

    if len(city_row) > 0:
        irradiation = float(city_row.iloc[0]["irradiation"])
        tilt_angle = float(city_row.iloc[0]["tilt"])
    else:
        irradiation = 5.5
        tilt_angle = 30

    # =====================================================
    # FACTEUR ORIENTATION
    # =====================================================

    orientation_factors = {
        "Sud": 1.00,
        "Sud-Est": 0.95,
        "Sud-Ouest": 0.95,
        "Est": 0.85,
        "Ouest": 0.85,
        "Nord-Est": 0.65,
        "Nord-Ouest": 0.65,
        "Nord": 0.50,
    }

    orientation_factor = orientation_factors.get(
        orientation,
        1.0
    )

    # =====================================================
    # PANNEAUX
    # =====================================================

    panels_df["score"] = (

    (panels_df["efficiency"] * 40)

    +

    (panels_df["power_w"] / 100 * 40)

    +

    (10000 / panels_df["price"] * 20)

)

    selected_panel = (
        panels_df
        .sort_values("score", ascending=False)
        .iloc[0]
    )

    panel_model = selected_panel["commercial_name"]
    panel_power_w = float(selected_panel["power_w"])
    panel_power_kw = panel_power_w / 1000
    panel_price = float(selected_panel["price"])
    panel_area = float(selected_panel["area"])
    panel_brand = selected_panel["brand"]
    panel_efficiency = float(selected_panel["efficiency"])

    performance_ratio = 0.80

    panel_daily_production = (
    irradiation
    * panel_power_kw
    * performance_ratio
    * orientation_factor
)

    panel_count = math.ceil(
    daily_consumption /
    panel_daily_production
)

    total_power_kwp = round(
    panel_count * panel_power_kw,
    2
)

    estimated_daily_production = round(
    panel_count * panel_daily_production,
    1
)

    required_surface = round(
    panel_count * panel_area,
    1
)

    annual_production = round(
    estimated_daily_production * 365,
    0
)

    installed_power = round(
    (panel_count * panel_power_w) / 1000,
    2
)

    # =====================================================
    # CONTRÔLE SURFACE
    # =====================================================

    if required_surface > available_area:

        panel_count = max(
            1,
            math.floor(
                available_area / panel_area
            )
        )

        total_power_kwp = round(
            panel_count * panel_power_kw,
            2
        )

        estimated_daily_production = round(
            panel_count * panel_daily_production,
            1
        )

        required_surface = round(
            panel_count * panel_area,
            1
        )
    annual_production = round(
    estimated_daily_production * 365,
    0
)
    co2_saved = round(
    annual_production * 0.7,
    0
)

    installed_power = round(
    (panel_count * panel_power_w) / 1000,
    2
)

    # =====================================================
    # BATTERIES
    # =====================================================

    if installation_type.lower() == "on-grid":
    
     battery_count = 0
     battery_cost = 0
     battery_price = 0
     battery_type = "Aucune"
     battery_capacity_unit = 0
     required_capacity = 0
     autonomy_days = 0
     total_battery_capacity = 0

    else:
        autonomy_days = data.autonomy_days
        required_capacity = round(
    daily_consumption
    * data.autonomy_days
    * 1.2,
    1
)
        autonomy_days = round(
            required_capacity /
            daily_consumption,
            1
)

        batteries_df["score"] = (

    batteries_df["capacity_kwh"] * 60

    +

    (10000 / batteries_df["price"] * 40)

)

        selected_battery = (
            batteries_df
            .sort_values("score", ascending=False)
            .iloc[0]
        )

        battery_capacity_unit = float(
            selected_battery["capacity_kwh"]
        )

        battery_price = float(
            selected_battery["price"]
        )

        battery_type = (
            selected_battery["technology"]
        )

        battery_count = math.ceil(
            required_capacity /
            battery_capacity_unit
        )
        total_battery_capacity = (
           battery_count *
          battery_capacity_unit
)

        if daily_consumption > 0:
         autonomy_days = round(
        total_battery_capacity /
        daily_consumption,
        1
    )
        else:
         autonomy_days = 0

        battery_cost = (
            battery_count *
            battery_price
        )

    # =====================================================
    # ONDULEUR
    # =====================================================

    inverter_power = round(
        total_power_kwp * 1.1,
        2
    )

    candidate_inverters = inverters_df[
    (inverters_df["power_w"] >= inverter_power * 1000)
    &
    (
        inverters_df["type"].str.lower()
        == installation_type.lower()
    )
]

    if len(candidate_inverters) > 0:

        selected_inverter = (
            candidate_inverters
            .sort_values("price")
            .iloc[0]
        )

    else:

        selected_inverter = (
            inverters_df
            .sort_values(
                "power_w",
                ascending=False
            )
            .iloc[0]
        )

    inverter_model = (
        selected_inverter["commercial_name"]
    )
    inverter_type = selected_inverter["type"]
    description_map = {
    "hybride":
        "Gestion panneaux, batteries et réseau",

    "on-grid":
        "Injection réseau sans batteries",

    "off-grid":
        "Système autonome avec batteries"
}
    inverter_description = description_map.get(
       inverter_type,
       "Onduleur photovoltaïque"
)

    inverter_cost = float(
        selected_inverter["price"]
    )

    # =====================================================
    # COÛTS
    # =====================================================

    panels_cost = (
        panel_count * panel_price
    )

    row = installation_df[
    (installation_df["power_min"] <= total_power_kwp)
    &
    (installation_df["power_max"] > total_power_kwp)
]

    if len(row) > 0:

     cost_per_kw = float(
        row.iloc[0]["cost_per_kw"]
    )

    else:

     cost_per_kw = 1800

    installation_cost = round(
     total_power_kwp * cost_per_kw,
    0
)
    installation_unit_price = installation_cost

    total_cost = (
        panels_cost
        + battery_cost
        + inverter_cost
        + installation_cost
    )

    country_row = co2_df[
    co2_df["country"].str.lower() == "morocco"
]

    if len(country_row) > 0:
     co2_factor = float(
        country_row.iloc[0]["co2_factor"]
    )
    else:
     co2_factor = 0.72

    co2_saved = round(
    annual_production * co2_factor,
    0
)

    # =====================================================
    # ÉCONOMIES
    # =====================================================

    price_row = electricity_df[
    electricity_df["city"].str.lower() == city.lower()
]

    if len(price_row) > 0:
     electricity_price = float(
        price_row.iloc[0]["price_dh_kwh"]
    )
    else:
     electricity_price = 1.58

    monthly_savings = round(
        estimated_daily_production *
        electricity_price *
        30,
        0
    )

    yearly_savings = (
        monthly_savings * 12
    )

    # =====================================================
    # ROI
    # =====================================================

    if yearly_savings > 0:

        roi_years = round(
            total_cost /
            yearly_savings,
            1
        )

    else:

        roi_years = 0

    # =====================================================
    # RECOMMANDATIONS
    # =====================================================
    surface_insufficient = (
     required_surface > available_area
)
    recommendations = []

    if orientation != "Sud":

        recommendations.append(
            "Orientation Sud recommandée pour maximiser la production."
        )


    if surface_insufficient:
         recommendations.append(
        "Surface disponible insuffisante."
    )

    if total_cost > budget:

        recommendations.append(
            "Le budget est inférieur au coût estimé."
        )

    if installation_type.lower() == "on-grid":

        recommendations.append(
            "Aucun stockage batterie prévu."
        )

    else:

        recommendations.append(
            "Stockage batterie activé."
        )

    recommendations.append(
        "Nettoyage des panneaux conseillé tous les 2 mois."
    )

    recommendations.append(
        "Maintenance annuelle recommandée."
    )

    # =====================================================
    # FAISABILITÉ
    # =====================================================

    surface_ok = (
        required_surface <= available_area
    )

    budget_ok = (
        total_cost <= budget
    )

    production_ok = (
        estimated_daily_production >= daily_consumption
    )
    coverage_rate = round(
    (estimated_daily_production /
     daily_consumption) * 100,
    1
)

    ai_score = 0

    if surface_ok:
     ai_score += 35

    if production_ok:
     ai_score += 35

    if orientation == "Sud":
     ai_score += 20

    if budget_ok:
     ai_score += 10
    else:
     ai_score -= 10

     ai_score = max(0, min(100, ai_score))
   
    if surface_ok and production_ok and budget_ok:
        project_status = "Faisable"

    elif surface_ok and production_ok:
     project_status = "Techniquement faisable"

    else:
     project_status = "Non faisable"

    # =====================================================
    # JSON RESPONSE
    # =====================================================
    ai_comment = []

    if roi_years < 5:
     ai_comment.append(
        "Excellent retour sur investissement."
    )

    elif roi_years < 10:
     ai_comment.append(
        "Projet rentable à moyen terme."
    )

    else:
     ai_comment.append(
        "Retour sur investissement relativement long."
    )

    if coverage_rate >= 100:
     ai_comment.append(
        "La production couvre totalement les besoins."
    )

    else:
     ai_comment.append(
        "La production ne couvre pas totalement les besoins."
    )

    if total_cost > budget:
     ai_comment.append(
        "Le budget disponible est insuffisant."
    )
     
    return {

        "location": city,

        "solar_data": {
            "irradiation": irradiation,
            "performance_ratio": performance_ratio,
            "orientation_factor": orientation_factor
        },

        "panels": {
            "panel_count": panel_count,
            "panel_brand": panel_brand,
            "panel_model": panel_model,
            "panel_power_w": panel_power_w,
            "panel_area_m2": panel_area,
            "total_power_kwp": total_power_kwp,
            "required_surface_m2": required_surface,
            "estimated_daily_production_kwh": estimated_daily_production,
            "tilt_angle": tilt_angle,
            "orientation": orientation
        },

        "battery": {
            "battery_count": battery_count,
            "battery_type": battery_type,
            "battery_unit_capacity_kwh": battery_capacity_unit,
            "required_capacity_kwh": required_capacity,
            "autonomy_days": autonomy_days
        },

        "inverter": {
            "inverter_model": inverter_model,
            "recommended_power_kw": inverter_power,
            "inverter_type": inverter_type,
            "description": inverter_description
        },

        "installation": {
            "roof_type": roof_type,
            "tilt_angle": tilt_angle,
            "orientation": orientation
        },

        "cost": {
            "panel_unit_price": panel_price,
            "battery_unit_price": battery_price,
            "inverter_unit_price": inverter_cost,


            "installation_unit_price": cost_per_kw,
            "installation_cost_per_kw": cost_per_kw,
            "installation_cost": installation_cost,

            "panels_cost": panels_cost,
            "battery_cost": battery_cost,
            "inverter_cost": inverter_cost,
            "installation_cost": installation_cost,
            "total_cost": total_cost
        },

        "roi": {
            "roi_years": roi_years,
            "monthly_savings": monthly_savings,
            "yearly_savings": yearly_savings
        },

        "feasibility": {
            "surface_ok": surface_ok,
            "budget_ok": budget_ok,
            "surface_insufficient": surface_insufficient,
            "production_ok": production_ok
        },

        "performance": {

          "installed_power_kw": installed_power,

           "annual_production_kwh": annual_production,

            "surface_required_m2": required_surface,

            "storage_capacity_kwh": total_battery_capacity,

            "autonomy_days": autonomy_days,

            "panel_efficiency": round(panel_efficiency * 100, 1),

            "coverage_rate_percent": coverage_rate,
           
},

"environment": {
    "co2_saved_kg_per_year": co2_saved
},
"ai_analysis": {
    "score": ai_score,
    "comments": ai_comment
},

"project_status": project_status,

        "recommendations": recommendations
    }
    
class CalculationService:
    def __init__(self, db=None):
        self.db = db

    def calculate_complete_system(self, request, token=None):
        return calculate_system(request)

    def estimate_panels(self, request):
        return calculate_system(request)

    def estimate_batteries(self, request):
        return calculate_system(request)

    def estimate_inverter(self, request):
        return calculate_system(request)

    def estimate_cost(self, request):
        return calculate_system(request)

    def calculate_roi(self, request):
        return calculate_system(request)