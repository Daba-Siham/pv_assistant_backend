class ResponseFormatter:
    def format_chat_response(
        self,
        response: str,
        session_id: str | None = None,
        sources: list[str] | None = None,
        suggested_questions: list[str] | None = None,
        calculation_result: dict | None = None,
        agent_result: dict | None = None,
        user_id: int | None = None
    ) -> dict:
        return {
            "response": response,
            "session_id": session_id,
            "user_id": user_id,
            "sources": sources or [],
            "suggested_questions": suggested_questions or [],
            "calculation_result": calculation_result,
            "agent_result": agent_result
        }

    def format_error_response(
        self,
        message: str,
        session_id: str | None = None,
        user_id: int | None = None
    ) -> dict:
        return {
            "response": message,
            "session_id": session_id,
            "user_id": user_id,
            "sources": [],
            "suggested_questions": [],
            "calculation_result": None,
            "agent_result": None
        }

    def clean_llm_response(self, response: str) -> str:
        if not response:
            return "Erreur technique : réponse IA vide."

        response = response.strip()
        if not response:
            return "Erreur technique : réponse IA vide."

        unwanted_prefixes = [
            "Assistant:",
            "Reponse:",
            "Réponse:",
            "AI:",
            "Bot:"
        ]

        for prefix in unwanted_prefixes:
            if response.startswith(prefix):
                response = response.replace(prefix, "", 1).strip()

        return response
