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

    def merge_with_report(self, simulation: dict, report_data: dict | None) -> dict:
        """
        Merge la simulation dynamique avec les données du rapport.
        Le rapport fournit : config système (panneaux, batteries, etc.)
        La simulation fournit : données heure par heure
        """
        if report_data is None:
            return simulation

        return {
            # Données dynamiques (from simulation)
            "data": simulation["data"],
            "alerts": simulation["alerts"],
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