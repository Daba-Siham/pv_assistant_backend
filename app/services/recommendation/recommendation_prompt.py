import json
from typing import Any


class RecommendationPromptBuilder:
    def build_prompt(
        self,
        user_inputs: dict[str, Any],
        formatted_result: dict[str, Any],
        ml_result: dict[str, Any],
        coherence_checks: list[dict[str, Any]],
        rag_context: str,
    ) -> str:
        return f"""
You are a professional photovoltaic assistant.

Produce a final recommendation that is clear, simple, and useful for a non-specialist user.

Mandatory rules:
- Answer in the same language as the user's last message.
- Do not force French unless explicitly requested.
- Use RESULTAT_SIMPLIFIE_A_AFFICHER as the main source of the answer.
- Never display overly precise raw model values.
- Do not display unnecessary technical decimals.
- Do not display exact cable sections unless the user asks for a technical report.
- Use ranges for costs.
- Use ranges for inverter power and battery capacity.
- Use a category for ROI: rapide, correct, moyen, or long.
- Never invent technical values.
- Technical values must come from the ML model or backend checks.
- RAG context is only used to explain, justify, and propose equipment families.
- Brands are examples to compare, never a quote or an obligation.
- If installation_type = on_grid and autonomy = 0, do not recommend a battery and do not propose a battery/autonomy scenario.
- If installation_type = hybrid, explain the compromise between battery, autonomy, and budget.
- If installation_type = off_grid, explain that the battery is required.
- If the surface is insufficient, do not conclude that the exact configuration is feasible: explain that the number of panels must be reduced or the available area increased.
- If data is missing, write "a verifier".

ENTREES_UTILISATEUR:
{json.dumps(user_inputs, ensure_ascii=False, indent=2)}

RESULTAT_SIMPLIFIE_A_AFFICHER:
{json.dumps(formatted_result, ensure_ascii=False, indent=2)}

RESULTAT_ML_INTERNE_NE_PAS_AFFICHER_BRUT:
{json.dumps(ml_result, ensure_ascii=False, indent=2)}

CONTROLES_COHERENCE:
{json.dumps(coherence_checks, ensure_ascii=False, indent=2)}

CONTEXTE_RAG_PHOTOVOLTAIQUE:
{rag_context or "Aucun contexte documentaire disponible."}

Expected response format:
1. Short project summary
2. Main recommendation
3. Recommended equipment
4. Budget and profitability
5. Points to verify
6. Alternative scenarios
   - Economic scenario
   - Balanced scenario
   - Autonomy/performance scenario
7. Clear conclusion
""".strip()
