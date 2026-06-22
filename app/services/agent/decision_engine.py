class DecisionEngine:
    def decide(self, user_message: str, user_inputs: dict | None = None) -> dict:
        message = user_message.lower()
        user_inputs = user_inputs or {}

        if self._is_dimensioning_request(message, user_inputs):
            return {
                "action": "calculate_pv_system",
                "tool_name": "calculate_pv_system",
                "reason": "L'utilisateur souhaite dimensionner une installation photovoltaïque."
            }

        if self._is_solar_data_request(message, user_inputs):
            return {
                "action": "get_solar_data",
                "tool_name": "get_solar_data",
                "reason": "L'utilisateur demande des données solaires ou une analyse de localisation."
            }

        if self._is_monitoring_request(message, user_inputs):
            return {
                "action": "simulate_system",
                "tool_name": "simulate_system",
                "reason": "L'utilisateur souhaite surveiller ou simuler le fonctionnement du système."
            }

        if self._is_anomaly_request(message, user_inputs):
            return {
                "action": "detect_anomalies",
                "tool_name": "detect_anomalies",
                "reason": "L'utilisateur parle d'une panne, d'une alerte ou d'un comportement anormal."
            }

        if self._is_store_request(message, user_inputs):
            return {
                "action": "find_stores",
                "tool_name": "find_stores",
                "reason": "L'utilisateur cherche des magasins ou fournisseurs proches."
            }

        if self._is_roi_request(message, user_inputs):
            return {
                "action": "calculate_roi",
                "tool_name": "calculate_roi",
                "reason": "L'utilisateur demande le retour sur investissement."
            }

        return {
            "action": "general_assistance",
            "tool_name": None,
            "reason": "Aucun outil spécifique requis. Réponse générale."
        }

    def _is_dimensioning_request(self, message: str, user_inputs: dict) -> bool:
        keywords = [
            "dimensionner",
            "dimensionnement",
            "installation",
            "panneaux",
            "batterie",
            "onduleur",
            "combien de panneaux",
            "système pv",
            "systeme pv",
            "photovoltaïque",
            "photovoltaique"
        ]

        required_inputs = [
            "daily_consumption_kwh",
            "available_area_m2"
        ]

        has_keyword = any(keyword in message for keyword in keywords)
        has_inputs = all(key in user_inputs for key in required_inputs)

        return has_keyword or has_inputs

    def _is_solar_data_request(self, message: str, user_inputs: dict) -> bool:
        keywords = [
            "irradiation",
            "ghi",
            "dni",
            "température",
            "temperature",
            "ensoleillement",
            "données solaires",
            "donnees solaires",
            "ville",
            "localisation"
        ]

        has_coordinates = "latitude" in user_inputs and "longitude" in user_inputs

        return any(keyword in message for keyword in keywords) or has_coordinates

    def _is_monitoring_request(self, message: str, user_inputs: dict) -> bool:
        keywords = [
            "monitoring",
            "surveillance",
            "suivi",
            "simulation",
            "production",
            "consommation",
            "niveau batterie",
            "état système",
            "etat systeme"
        ]

        return any(keyword in message for keyword in keywords)

    def _is_anomaly_request(self, message: str, user_inputs: dict) -> bool:
        keywords = [
            "panne",
            "anomalie",
            "alerte",
            "problème",
            "probleme",
            "batterie faible",
            "surcharge",
            "défaillance",
            "defaillance",
            "baisse de production"
        ]

        return any(keyword in message for keyword in keywords)

    def _is_store_request(self, message: str, user_inputs: dict) -> bool:
        keywords = [
            "magasin",
            "boutique",
            "fournisseur",
            "acheter",
            "e-commerce",
            "commerce",
            "proche",
            "près de moi",
            "pres de moi"
        ]

        return any(keyword in message for keyword in keywords)

    def _is_roi_request(self, message: str, user_inputs: dict) -> bool:
        keywords = [
            "roi",
            "retour sur investissement",
            "rentabilité",
            "rentabilite",
            "économie",
            "economie",
            "amortissement"
        ]

        return any(keyword in message for keyword in keywords)