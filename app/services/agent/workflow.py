import uuid
from types import SimpleNamespace

from app.schemas.chat import ChatRequest
from app.services.calculation.calculation_service import CalculationService
from app.services.llm.llm_service import LLMService
from app.services.agent.tool_registry import ToolRegistry


class AgentWorkflow:
    def __init__(self, db=None):
        self.db = db
        self.calculation_service = CalculationService(db)
        self.llm_service = LLMService(db)
        self.tool_registry = ToolRegistry(db)

    def run(self, user_message: str, user_inputs=None, session_id: str | None = None, token=None):
        message = user_message.lower()
        user_inputs = user_inputs or {}
        session_id = session_id or str(uuid.uuid4())

        if (
            "analyse" in message
            or "dimensionnement" in message
            or "installation" in message
            or "solaire" in message
            or "photovoltaique" in message
            or "photovoltaïque" in message
            or "panneaux" in message
            or "solar" in message
            or "panels" in message
        ):
            missing = self._missing_dimensioning_inputs(user_inputs)
            if missing:
                return {
                    "success": False,
                    "message": "Parametres manquants pour le dimensionnement.",
                    "session_id": session_id,
                    "action": "calculate_pv_system",
                    "tools_used": [],
                    "result": None,
                    "recommendations": [
                        f"Veuillez fournir: {', '.join(missing)}"
                    ],
                }

            input_object = self._to_input_object(user_inputs)
            calc = self.calculation_service.calculate_complete_system(input_object)

            solar = calc["solar_data"]
            panels = calc["panels"]
            battery = calc["battery"]
            inverter = calc["inverter"]
            roi = calc["roi"]
            cost = calc["cost"]
            battery_needed = battery["battery_needed"]
            installation_type = input_object.installation_type

            prompt = f"""
You are a Moroccan photovoltaic expert.

IMPORTANT:
Answer only with calculated backend data.
Answer in the same language as the user's last message.

City: {input_object.city}
Installation: {installation_type}
Panels: {panels['panel_count']}
Power: {panels['total_power_kwp']} kWc
Production: {panels['estimated_daily_production_kwh']} kWh/day
ROI: {roi['roi_years']} years
Budget: {cost['total_cost']} DH
Tilt: {solar['optimal_tilt']}\u00b0
Battery required: {battery_needed}
Battery capacity: {battery['required_capacity_kwh']} kWh
Inverter: {inverter['recommended_power_kw']} kW

If the system has no battery:
- never display battery
- never discuss battery

If hybrid:
- explain the hybrid advantages

Answer professionally.
"""

            ai_response = self.llm_service._call_llm(prompt, user_message=user_message)
            self.llm_service._save_chat_history(
                user_id=None,
                session_id=session_id,
                user_message=user_message,
                assistant_response=ai_response,
                context={"agent_result": calc},
            )

            results = {
                "ville": input_object.city,
                "system_type": installation_type,
                "panneaux": f"{panels['panel_count']} panneaux",
                "panel_type": "Monocristallin",
                "power": f"{round(panels['total_power_kwp'], 2)} kWc",
                "battery": (
                    f"{round(battery['required_capacity_kwh'], 1)} kWh"
                    if battery_needed
                    else None
                ),
                "battery_type": "LiFePO4" if battery_needed else None,
                "battery_count": (
                    round(battery["required_capacity_kwh"] / 5)
                    if battery_needed
                    else 0
                ),
                "inverter": f"{round(inverter['recommended_power_kw'], 1)} kW",
                "production": f"{round(panels['estimated_daily_production_kwh'], 1)} kWh/j",
                "roi": f"{round(roi['roi_years'], 1)} ans",
                "cout": f"{round(cost['total_cost'])} DH",
                "inclinaison": f"{solar['optimal_tilt']}\u00b0",
                "orientation": "Sud",
                "irradiation": f"{solar['ghi']} kWh/m\u00b2",
                "installation": installation_type,
            }

            return {
                "success": True,
                "message": ai_response,
                "session_id": session_id,
                "action": "calculate_pv_system",
                "tools_used": ["calculate_pv_system"],
                "result": calc,
                "results": results,
                "raw_data": calc,
                "recommendations": [],
            }

        response = self.llm_service.generate_response(
            request=ChatRequest(
                message=user_message,
                session_id=session_id,
                context={"user_inputs": user_inputs},
            )
        )

        return {
            "success": True,
            "message": response["response"],
            "session_id": response.get("session_id", session_id),
            "action": "general_assistance",
            "tools_used": [],
            "result": None,
            "recommendations": [],
        }

    def execute_tool(self, tool_name: str, parameters: dict, token: str | None = None) -> dict:
        return self.tool_registry.execute(tool_name=tool_name, parameters=parameters, token=token)

    def list_tools(self) -> list[dict]:
        return self.tool_registry.list_tools()

    @staticmethod
    def _missing_dimensioning_inputs(user_inputs: dict) -> list[str]:
        required = [
            "city",
            "daily_consumption_kwh",
            "available_area_m2",
            "budget",
            "orientation",
            "installation_type",
            "autonomy_days",
            "roof_type",
        ]
        return [
            key for key in required
            if key not in user_inputs or user_inputs[key] in (None, "")
        ]

    @staticmethod
    def _to_input_object(user_inputs: dict):
        defaults = {
            "shade_factor": 0.1,
            "distance_to_load_m": 10,
        }
        return SimpleNamespace(**{**defaults, **user_inputs})
