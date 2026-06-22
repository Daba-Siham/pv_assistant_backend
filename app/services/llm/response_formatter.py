class ResponseFormatter:
    def format_chat_response(
        self,
        response: str,
        session_id: str | None = None,
        sources: list[str] | None = None,
        suggested_questions: list[str] | None = None,
        calculation_result: dict | None = None,
        agent_result: dict | None = None
    ) -> dict:
        return {
            "response": response,
            "session_id": session_id,
            "sources": sources or [],
            "suggested_questions": suggested_questions or self.default_suggestions(),
            "calculation_result": calculation_result,
            "agent_result": agent_result
        }

    def default_suggestions(self) -> list[str]:
        return [
            "Comment dimensionner mon installation solaire ?",
            "Combien de panneaux faut-il pour ma consommation ?",
            "Est-ce que j'ai besoin d'une batterie ?",
            "Comment calculer le retour sur investissement ?"
        ]

    def format_error_response(
        self,
        message: str,
        session_id: str | None = None
    ) -> dict:
        return {
            "response": message,
            "session_id": session_id,
            "sources": [],
            "suggested_questions": self.default_suggestions(),
            "calculation_result": None,
            "agent_result": None
        }

    def clean_llm_response(self, response: str) -> str:
        if not response:
            return "Je n'ai pas pu générer une réponse claire."

        response = response.strip()

        unwanted_prefixes = [
            "Assistant:",
            "Réponse:",
            "AI:",
            "Bot:"
        ]

        for prefix in unwanted_prefixes:
            if response.startswith(prefix):
                response = response.replace(prefix, "", 1).strip()

        return response