# app/services/monitoring/user_simulation_service.py

from data.simulations.users_simulations import USERS_SIMULATIONS


class UserSimulationService:

    def get_simulation_by_user_id(self, user_id: int) -> dict:
        """
        Retourne la simulation 24h du user selon son ID.
        Si l'ID n'existe pas dans le dictionnaire (ex: ID > 7), 
        on attribue par défaut la simulation de l'ID 1.
        """
        # .get(user_id, USERS_SIMULATIONS[1]) signifie : 
        # Cherche user_id, sinon renvoie USERS_SIMULATIONS[1]
        return USERS_SIMULATIONS.get(user_id, USERS_SIMULATIONS[1])

    def deduplicate_alerts(self, alerts):
        seen = set()
        result = []

        for alert in alerts or []:
            if isinstance(alert, dict):
                key = (
                    alert.get("alert_type", ""),
                    alert.get("message", "")
                )
            else:
                key = (
                    getattr(alert, "alert_type", ""),
                    getattr(alert, "message", "")
                )

            if key in seen:
                continue

            seen.add(key)
            result.append(alert)

        return result

    def merge_with_report(self, simulation: dict, report_data: dict | None) -> dict:
        """
        Merge la simulation dynamique avec les données du rapport.
        Le rapport fournit : config système (panneaux, batteries, etc.)
        La simulation fournit : données heure par heure
        """
        if report_data is None:
            merged_simulation = dict(simulation)
            merged_simulation["alerts"] = self.deduplicate_alerts(merged_simulation.get("alerts", []))
            return merged_simulation

        alerts = self.deduplicate_alerts(simulation["alerts"])
        return {
            # Données dynamiques (from simulation)
            "data": simulation["data"],
            "alerts": alerts,
            "summary": simulation["summary"],

            # Config système (from rapport) — enrichissement
            "system_config": {
                "panels": report_data.get("panels", {}),
                "battery": report_data.get("battery", {}),
                "inverter": report_data.get("inverter", {}),
                "installation": report_data.get("installation", {}),
                "solar_data": report_data.get("solar_data", {}),
                "cost": report_data.get("cost", {}),
                "roi": report_data.get("roi", {}),
                "location": report_data.get("location", ""),
                "project_status": report_data.get("project_status", ""),
                "recommendations": report_data.get("recommendations", []),
            }
        }
