from app.schemas.chat import ChatRequest


class PromptBuilder:
    def build_system_prompt(self) -> str:
        return """
Tu es un assistant intelligent spécialisé dans le dimensionnement des systèmes photovoltaïques.

Ton rôle est d'aider l'utilisateur à :
- comprendre les systèmes solaires photovoltaïques
- dimensionner une installation PV
- comprendre les résultats de calcul
- interpréter les alertes de monitoring
- recevoir des recommandations simples et utiles

Tu dois répondre avec un style :
- clair
- pédagogique
- professionnel
- simple pour un utilisateur non spécialiste

Règles importantes :
- Ne donne pas de valeurs techniques inventées si les données sont absentes.
- Si une information manque, explique ce qu'il faut fournir.
- Si un résultat de calcul est disponible, explique-le clairement.
- Si une alerte est détectée, explique la cause probable et l'action recommandée.
- Ne remplace pas les calculs du backend par des suppositions.
- Pour les réponses techniques, précise les hypothèses utilisées.
""".strip()

    def build_chat_prompt(
        self,
        request: ChatRequest,
        rag_context: str | None = None,
        calculation_result: dict | None = None,
        agent_result: dict | None = None,
        chat_history: list[dict] | None = None
    ) -> str:
        parts = []

        parts.append(self.build_system_prompt())

        if chat_history:
            parts.append("\nHistorique récent de la conversation :")
            for item in chat_history[-5:]:
                parts.append(f"Utilisateur : {item.get('user_message')}")
                parts.append(f"Assistant : {item.get('assistant_response')}")

        if rag_context:
            parts.append("\nContexte documentaire utile :")
            parts.append(rag_context)

        if calculation_result:
            parts.append("\nRésultat de dimensionnement disponible :")
            parts.append(str(calculation_result))

        if agent_result:
            parts.append("\nRésultat de l'agent intelligent :")
            parts.append(str(agent_result))

        if request.context:
            parts.append("\nContexte fourni par le frontend :")
            parts.append(str(request.context))

        parts.append("\nQuestion utilisateur :")
        parts.append(request.message)

        parts.append("\nRéponse attendue :")
        return "\n".join(parts)

    def build_explanation_prompt(self, result: dict) -> str:
        return f"""
Explique ce résultat de dimensionnement photovoltaïque à un utilisateur non spécialiste.

Résultat :
{result}

Réponse attendue :
- résumé clair
- explication du nombre de panneaux
- explication de la batterie
- explication de l'onduleur
- explication du coût
- explication du ROI
- recommandations simples
""".strip()