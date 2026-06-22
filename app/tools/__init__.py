from app.tools.get_solar_data import TOOL_DEFINITION as GET_SOLAR_DATA_TOOL
from app.tools.estimate_panels import TOOL_DEFINITION as ESTIMATE_PANELS_TOOL
from app.tools.estimate_batteries import TOOL_DEFINITION as ESTIMATE_BATTERIES_TOOL
from app.tools.estimate_inverter import TOOL_DEFINITION as ESTIMATE_INVERTER_TOOL
from app.tools.estimate_cost import TOOL_DEFINITION as ESTIMATE_COST_TOOL
from app.tools.calculate_roi import TOOL_DEFINITION as CALCULATE_ROI_TOOL
from app.tools.find_stores import TOOL_DEFINITION as FIND_STORES_TOOL
from app.tools.simulate_system import TOOL_DEFINITION as SIMULATE_SYSTEM_TOOL
from app.tools.detect_anomalies import TOOL_DEFINITION as DETECT_ANOMALIES_TOOL
from app.tools.predict_energy import TOOL_DEFINITION as PREDICT_ENERGY_TOOL


ALL_TOOLS = {
    "get_solar_data": GET_SOLAR_DATA_TOOL,
    "estimate_panels": ESTIMATE_PANELS_TOOL,
    "estimate_batteries": ESTIMATE_BATTERIES_TOOL,
    "estimate_inverter": ESTIMATE_INVERTER_TOOL,
    "estimate_cost": ESTIMATE_COST_TOOL,
    "calculate_roi": CALCULATE_ROI_TOOL,
    "find_stores": FIND_STORES_TOOL,
    "simulate_system": SIMULATE_SYSTEM_TOOL,
    "detect_anomalies": DETECT_ANOMALIES_TOOL,
    "predict_energy": PREDICT_ENERGY_TOOL,
}