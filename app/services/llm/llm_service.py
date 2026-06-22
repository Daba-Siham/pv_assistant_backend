import uuid
import requests

from sqlalchemy.orm import Session

from app.config import settings
from app.models.chat_history import ChatHistory
from app.schemas.chat import ChatRequest
from app.services.llm.prompt_builder import PromptBuilder
from app.services.llm.response_formatter import ResponseFormatter
from app.services.rag.retriever import RAGRetriever

class LLMService:
    def __init__(self, db: Session | None = None):
        self.db = db
        self.prompt_builder = PromptBuilder()
        self.response_formatter = ResponseFormatter()
        self.rag_retriever = RAGRetriever()

    def generate_response(self, request: ChatRequest, token: str | None = None) -> dict:
        session_id = request.session_id or str(uuid.uuid4())

        try:
            chat_history = self._get_recent_history(session_id)
            rag_context = self.rag_retriever.retrieve_context_only(request.message)

            prompt = self.prompt_builder.build_chat_prompt(
                request=request,
                rag_context=rag_context,
                calculation_result=None,
                agent_result=None,
                chat_history=chat_history
            )

            raw_response = self._call_llm(prompt)
            response = self.response_formatter.clean_llm_response(raw_response)

            self._save_chat_history(
                user_id=request.user_id,
                session_id=session_id,
                user_message=request.message,
                assistant_response=response,
                context=request.context
            )
            

            return self.response_formatter.format_chat_response(
                response=response,
                session_id=session_id
            )

        except Exception:
            return self.response_formatter.format_error_response(
                message="Désolé, une erreur est survenue pendant la génération de la réponse.",
                session_id=session_id
            )

    def explain_calculation_result(self, result: dict) -> str:
        prompt = self.prompt_builder.build_explanation_prompt(result)
        response = self._call_llm(prompt)
        return self.response_formatter.clean_llm_response(response)

    def get_chat_history(self, token: str | None = None) -> list:
        if self.db is None:
            return []

        histories = (
            self.db.query(ChatHistory)
            .order_by(ChatHistory.created_at.desc())
            .limit(50)
            .all()
        )

        return histories

    def clear_chat_history(self, token: str | None = None) -> dict:
        if self.db is None:
            return {
                "success": False,
                "message": "Base de données non disponible"
            }

        self.db.query(ChatHistory).delete()
        self.db.commit()

        return {
            "success": True,
            "message": "Historique supprimé avec succès"
        }

    def _call_llm(self, prompt: str) -> str:
        provider = settings.LLM_PROVIDER.lower()

        if provider == "ollama":
            return self._call_ollama(prompt)

        if provider == "openai":
            return self._call_openai(prompt)

        if provider == "groq":
            return self._call_groq(prompt)

        return self._fallback_response(prompt)

    def _call_ollama(self, prompt: str) -> str:
        url = f"{settings.OLLAMA_BASE_URL}/api/generate"

        payload = {
            "model": settings.LLM_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": settings.LLM_TEMPERATURE,
                "num_predict": settings.LLM_MAX_TOKENS
            }
        }

        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()

        data = response.json()
        return data.get("response", "")

    def _call_openai(self, prompt: str) -> str:
        if not settings.OPENAI_API_KEY:
            return self._fallback_response(prompt)

        url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": settings.LLM_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": self.prompt_builder.build_system_prompt()
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"]

    def _call_groq(self, prompt: str) -> str:
        if not settings.GROQ_API_KEY:
            return self._fallback_response(prompt)

        url = "https://api.groq.com/openai/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": settings.LLM_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": self.prompt_builder.build_system_prompt()
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"]

    def _fallback_response(self, prompt: str) -> str:
        return (
            "Je peux vous aider à dimensionner une installation photovoltaïque. "
            "Pour commencer, j’ai besoin de votre consommation journalière en kWh, "
            "votre ville ou vos coordonnées GPS, la surface disponible, le type "
            "d’installation souhaité et l’autonomie batterie désirée."
        )

    def _get_recent_history(self, session_id: str) -> list[dict]:
        if self.db is None:
            return []

        histories = (
            self.db.query(ChatHistory)
            .filter(ChatHistory.session_id == session_id)
            .order_by(ChatHistory.created_at.asc())
            .limit(10)
            .all()
        )

        return [
            {
                "user_message": history.user_message,
                "assistant_response": history.assistant_response
            }
            for history in histories
        ]

    def _save_chat_history(
        self,
        user_id: int | None,
        session_id: str,
        user_message: str,
        assistant_response: str,
        context: dict | None = None
    ) -> None:
        if self.db is None:
            return

        history = ChatHistory(
            user_id=user_id,
            session_id=session_id,
            user_message=user_message,
            assistant_response=assistant_response,
            context=context
        )

        self.db.add(history)
        self.db.commit()