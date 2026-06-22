from app.schemas.chat import ChatRequest


class PromptBuilder:
    def build_system_prompt(self) -> str:
        return """
Tu es SolarAI.

Réponds aux questions photovoltaïques avec des réponses utiles, détaillées et pédagogiques.
Utilise le contexte RAG si disponible.
Si le contexte RAG est vide, réponds avec tes connaissances générales.
Réponds dans la langue du dernier message utilisateur, sans utiliser un module externe de détection de langue.
""".strip()

    def build_chat_messages(
        self,
        request: ChatRequest,
        rag_context: str | None = None,
        chat_history: list[dict] | None = None,
    ) -> list[dict[str, str]]:
        messages = [{"role": "system", "content": self.build_system_prompt()}]

        for item in (chat_history or [])[-10:]:
            messages.append({"role": "user", "content": str(item.get("user_message", ""))})
            messages.append({"role": "assistant", "content": str(item.get("assistant_response", ""))})

        if rag_context:
            messages.append({"role": "system", "content": f"Contexte RAG:\n{rag_context}"})

        messages.append({"role": "user", "content": request.message})
        return messages

    def build_chat_prompt(
        self,
        request: ChatRequest,
        rag_context: str | None = None,
        calculation_result: dict | None = None,
        agent_result: dict | None = None,
        chat_history: list[dict] | None = None,
    ) -> str:
        parts = [self.build_system_prompt()]

        if chat_history:
            parts.append("\nHistorique récent de la conversation :")
            for item in chat_history[-10:]:
                parts.append(f"Utilisateur : {item.get('user_message')}")
                parts.append(f"Assistant : {item.get('assistant_response')}")

        if rag_context:
            parts.append("\nContexte RAG :")
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
        parts.append("\nRéponse détaillée :")
        return "\n".join(parts)

    def build_explanation_prompt(self, result: dict) -> str:
        return f"""
Tu es SolarAI.
Explique ce résultat de dimensionnement photovoltaïque à un utilisateur non spécialiste.
Réponds dans la langue appropriée au contexte utilisateur.

Résultat :
{result}

Réponse attendue :
- résumé clair ;
- explication du nombre de panneaux ;
- explication de la batterie ;
- explication de l'onduleur ;
- explication du coût ;
- explication du ROI ;
- recommandations simples.
""".strip()
