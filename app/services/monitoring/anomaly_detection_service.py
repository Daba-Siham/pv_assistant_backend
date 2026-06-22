from app.schemas.monitoring import (
    AlertResponse,
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
)


class AnomalyDetectionService:
    def detect(self, request: AnomalyDetectionRequest) -> AnomalyDetectionResponse:
        alerts = []
        recommendations = []

        production_ratio = self._safe_ratio(
            request.production_kwh,
            request.expected_production_kwh
        )

        if request.expected_production_kwh > 0 and production_ratio < 0.5:
            alerts.append(
                AlertResponse(
                    severity="critical",
                    alert_type="low_production",
                    message="La production réelle est très inférieure à la production attendue.",
                    probable_cause="Ombrage important, panneau défectueux, problème de câblage ou météo défavorable.",
                    recommended_action="Vérifier les panneaux, l'onduleur, le câblage et les conditions météo."
                )
            )

            recommendations.append(
                "Comparer la production avec les données météo avant de conclure à une panne matérielle."
            )

        elif request.expected_production_kwh > 0 and production_ratio < 0.75:
            alerts.append(
                AlertResponse(
                    severity="warning",
                    alert_type="reduced_performance",
                    message="La production est inférieure au niveau attendu.",
                    probable_cause="Pertes dues à la température, orientation, poussière ou ombrage partiel.",
                    recommended_action="Nettoyer les panneaux et vérifier l'orientation."
                )
            )

            recommendations.append(
                "Surveiller cette baisse sur plusieurs jours pour confirmer l'anomalie."
            )

        if request.battery_level_percent is not None:
            if request.battery_level_percent < 15:
                alerts.append(
                    AlertResponse(
                        severity="critical",
                        alert_type="battery_critical",
                        message="Le niveau de batterie est critique.",
                        probable_cause="Consommation élevée ou production insuffisante.",
                        recommended_action="Réduire la consommation et vérifier la capacité de batterie."
                    )
                )

                recommendations.append(
                    "Prévoir une batterie plus grande si cette situation se répète."
                )

            elif request.battery_level_percent < 30:
                alerts.append(
                    AlertResponse(
                        severity="warning",
                        alert_type="battery_low",
                        message="Le niveau de batterie est faible.",
                        probable_cause="Production solaire insuffisante ou autonomie mal dimensionnée.",
                        recommended_action="Surveiller la charge de batterie."
                    )
                )

        if request.consumption_kwh > request.production_kwh * 2 and request.production_kwh > 0:
            alerts.append(
                AlertResponse(
                    severity="important",
                    alert_type="high_consumption",
                    message="La consommation est élevée par rapport à la production.",
                    probable_cause="Utilisation simultanée de plusieurs équipements.",
                    recommended_action="Décaler certains usages vers les heures de forte production."
                )
            )

            recommendations.append(
                "Optimiser l'autoconsommation en utilisant les équipements énergivores pendant la journée."
            )

        if request.temperature is not None and request.temperature > 40:
            alerts.append(
                AlertResponse(
                    severity="warning",
                    alert_type="high_temperature",
                    message="Température élevée détectée.",
                    probable_cause="Forte chaleur pouvant réduire le rendement des panneaux.",
                    recommended_action="Tenir compte des pertes thermiques dans l'analyse."
                )
            )

        has_anomaly = len(alerts) > 0
        main_alert = alerts[0] if alerts else None

        return AnomalyDetectionResponse(
            has_anomaly=has_anomaly,
            anomaly_type=main_alert.alert_type if main_alert else None,
            severity=main_alert.severity if main_alert else None,
            alerts=alerts,
            recommendations=recommendations
        )

    def _safe_ratio(self, value: float, reference: float) -> float:
        if reference <= 0:
            return 1.0

        return value / reference