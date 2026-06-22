from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.schemas.recommendation import PVRecommendationRequest, PVRecommendationResponse
from app.services.llm.llm_service import LLMService
from app.services.ml import PVModelService
from app.services.rag.retriever import get_retriever
from app.services.recommendation.coherence_service import PVCoherenceService
from app.services.recommendation.recommendation_formatter import format_ml_recommendation
from app.services.recommendation.recommendation_prompt import RecommendationPromptBuilder


class PVRecommendationService:
    def __init__(self, db: Session | None = None):
        self.db = db
        self.ml_service = PVModelService()
        self.coherence_service = PVCoherenceService()
        self.prompt_builder = RecommendationPromptBuilder()
        self.llm_service = LLMService(db=db)

    def generate(self, request: PVRecommendationRequest) -> PVRecommendationResponse:
        user_inputs = self._serialize_inputs(request)
        ml_result = self.ml_service.predict(request)
        coherence_checks = self.coherence_service.run_checks(request, ml_result)
        checks_as_dict = [check.model_dump() for check in coherence_checks]
        formatted_result = format_ml_recommendation(
            user_inputs=user_inputs,
            ml_result=ml_result,
            checks=checks_as_dict,
        )
        rag_context = self._retrieve_rag_context(request, coherence_checks)

        prompt = self.prompt_builder.build_prompt(
            user_inputs=user_inputs,
            formatted_result=formatted_result,
            ml_result=ml_result,
            coherence_checks=checks_as_dict,
            rag_context=rag_context,
        )

        try:
            raw_response = self.llm_service._call_llm(prompt)
            response = self.llm_service.response_formatter.clean_llm_response(raw_response)
        except Exception as exc:
            response = self._build_fallback_response(
                formatted_result,
                coherence_checks,
                exc,
            )

        return PVRecommendationResponse(
            success=True,
            user_inputs=user_inputs,
            formatted_recommendation=formatted_result,
            ml_recommendation=ml_result if settings.EXPOSE_RAW_ML_RESPONSE else None,
            coherence_checks=coherence_checks,
            rag_context_used=bool(rag_context),
            response=response,
        )

    def _retrieve_rag_context(
        self,
        request: PVRecommendationRequest,
        coherence_checks: list,
    ) -> str:
        query = (
            "dimensionnement photovoltaique materiel recommande panneaux batteries onduleur ROI "
            f"{request.installation_type.value} {request.city} "
            f"orientation {request.orientation} inclinaison {request.tilt_angle} "
            f"controle coherence {' '.join(check.code for check in coherence_checks)}"
        )

        docs = get_retriever().invoke(query)
        return "\n\n".join(doc.page_content for doc in docs)

    @staticmethod
    def _build_fallback_response(
        formatted_result: dict[str, Any],
        coherence_checks: list,
        error: Exception,
        language: str = "french",
    ) -> str:
        data = formatted_result["recommendation_data"]
        recommendation = formatted_result["user_friendly_recommendation"]
        scenario_analysis = data["scenario_analysis"]
        surface_check = data.get("surface_check")
        constraints_text = "\n".join(
            f"- {message}" for message in data.get("constraints_analysis", [])
        ) or "- Aucune contrainte majeure détectée."
        warnings_text = "\n".join(
            f"- {message}" for message in data.get("points_to_check", [])
        ) or "- Aucun point bloquant détecté."
        scenarios = data["scenarios"]
        battery_sentence = (
            "Comme l'installation est connectée au réseau et que l'autonomie demandée est de 0 jour, aucune batterie n'est nécessaire dans cette configuration."
            if not data["battery_visible"]
            else "Vous avez choisi un système connecté au réseau, mais vous demandez une autonomie batterie. Pour répondre à ce besoin, une installation hybride serait plus adaptée."
            if "B" in scenario_analysis.get("detected_scenarios", [])
            else f"La batterie recommandée se situe dans la plage suivante : {data['battery_range']}."
        )
        conclusion = (
            "Le projet doit être ajusté avant validation, car une ou plusieurs contraintes sont bloquantes dans la configuration actuelle."
            if scenario_analysis["global_status"] == "non faisable dans cette configuration"
            else
            "Le projet est intéressant, mais la configuration actuelle est limitée par la surface disponible. La meilleure option est de réduire le nombre de panneaux ou d'augmenter la surface utilisable."
            if surface_check and surface_check.get("status") == "insufficient"
            else "Le projet est techniquement cohérent sous réserve d'un devis installateur et d'une vérification de site."
        )
        realistic_solution = ""
        if surface_check and surface_check.get("status") == "insufficient":
            realistic_solution = (
                "\n\nSolution réaliste selon les contraintes\n\n"
                f"Avec la surface actuelle, il est plus réaliste d'installer environ {surface_check.get('realistic_panel_count')} panneaux. "
                "La couverture énergétique sera donc partielle, sauf si une surface supplémentaire est disponible."
            )

        if language == "english":
            return (
                "Project summary\n\n"
                f"Your project is a {data['installation_type_label']} photovoltaic installation in {data['city']}, "
                f"for about {data['daily_consumption_kwh']} kWh/day. The available area is "
                f"{data['available_area_m2']} m2 and the declared budget is {data['budget_declared']}.\n\n"
                "Global status\n\n"
                f"{scenario_analysis['global_status']}.\n\n"
                "Detected constraints\n\n"
                f"{constraints_text}\n\n"
                "Main recommendation\n\n"
                f"The backend model recommends {data['panels_range']}, with panels rated "
                f"{data['panel_power_range']}. The target photovoltaic power is {data['pv_power_range']}.\n"
                f"{realistic_solution}\n\n"
                "Budget and profitability\n\n"
                f"The likely budget is {data['budget_estimated_range']}. Estimated ROI is "
                f"{data['roi_range']}, categorized as {data['roi_category']}.\n\n"
                "Points to verify\n\n"
                f"{warnings_text}\n\n"
                "Alternative scenarios\n\n"
                f"- Economic scenario: {scenarios['economic']}\n"
                f"- Balanced scenario: {scenarios['balanced']}\n"
                f"- Performance scenario: {scenarios['performance']}"
            ).strip()

        if language == "arabic":
            return (
                "ملخص المشروع\n\n"
                f"المشروع هو تركيب photovoltaic من نوع {data['installation_type_label']} في {data['city']}، "
                f"لاستهلاك يقارب {data['daily_consumption_kwh']} kWh/day. المساحة المتاحة هي "
                f"{data['available_area_m2']} m2 والميزانية المصرح بها هي {data['budget_declared']}.\n\n"
                "الحالة العامة\n\n"
                f"{scenario_analysis['global_status']}.\n\n"
                "القيود المكتشفة\n\n"
                f"{constraints_text}\n\n"
                "التوصية الرئيسية\n\n"
                f"يوصي نموذج backend بـ {data['panels_range']}، مع panels بقدرة "
                f"{data['panel_power_range']}. القدرة photovoltaic المستهدفة هي {data['pv_power_range']}.\n"
                f"{realistic_solution}\n\n"
                "الميزانية و ROI\n\n"
                f"الميزانية المحتملة هي {data['budget_estimated_range']}. ROI التقديري هو "
                f"{data['roi_range']} وتصنيفه {data['roi_category']}.\n\n"
                "نقاط يجب التحقق منها\n\n"
                f"{warnings_text}\n\n"
                "سيناريوهات بديلة\n\n"
                f"- السيناريو الاقتصادي: {scenarios['economic']}\n"
                f"- السيناريو المتوازن: {scenarios['balanced']}\n"
                f"- سيناريو الأداء: {scenarios['performance']}"
            ).strip()

        return f"""
Résumé du projet

Votre projet concerne une installation photovoltaïque {data["installation_type_label"]} à {data["city"]}, pour une consommation journalière d'environ {data["daily_consumption_kwh"]} kWh/j. La surface disponible est de {data["available_area_m2"]} m² et le budget déclaré est {data["budget_declared"]}.

Statut global

{scenario_analysis["global_status"]}.

Analyse des contraintes détectées

{constraints_text}

Recommandation principale

Le modèle recommande {data["panels_range"]}, avec des panneaux de {data["panel_power_range"]}. La puissance photovoltaïque visée est {data["pv_power_range"]}.
{realistic_solution}

Matériel conseillé

Pour ce projet, il est conseillé de comparer:
- panneaux monocristallins performants, par exemple Jinko Solar, LONGi ou Canadian Solar;
- {data["inverter_type"]}, dans la gamme {data["inverter_range"]};
- {battery_sentence}

Budget et rentabilité

Le budget probable se situe {data["budget_estimated_range"]}. La rentabilité estimative est {data["roi_range"]}, avec une rentabilité considérée comme {data["roi_category"]}.

Points à vérifier

{warnings_text}

Scénarios alternatifs

- Scénario économique: {scenarios["economic"]}
- Scénario équilibré: {scenarios["balanced"]}
- Scénario performance: {scenarios["performance"]}

Conclusion

{conclusion}
""".strip()

    @staticmethod
    def _serialize_inputs(request: PVRecommendationRequest) -> dict[str, Any]:
        data = request.model_dump(mode="json")
        data["daily_consumption_kwh_normalized"] = request.normalized_daily_consumption_kwh
        return data
