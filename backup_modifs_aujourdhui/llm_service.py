import uuid

import requests
from sqlalchemy.orm import Session

from app.config import settings
from app.models.chat_history import ChatHistory
from app.schemas.chat import ChatRequest
from app.services.llm.prompt_builder import PromptBuilder
from app.services.llm.response_formatter import ResponseFormatter
from app.services.rag.retriever import RAGRetriever
from app.services.shared.logger import get_logger


logger = get_logger(__name__)


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
            rag_context = self._retrieve_rag_context(request.message)

            prompt = self.prompt_builder.build_chat_prompt(
                request=request,
                rag_context=rag_context,
                calculation_result=None,
                agent_result=None,
                chat_history=chat_history,
            )
            messages = self.prompt_builder.build_chat_messages(
                request=request,
                rag_context=rag_context,
                chat_history=chat_history,
            )

            raw_response = self._call_llm(prompt=prompt, messages=messages)
            response = self.response_formatter.clean_llm_response(raw_response)

            self._save_chat_history(
                user_id=request.user_id,
                session_id=session_id,
                user_message=request.message,
                assistant_response=response,
                context=request.context,
            )

            return self.response_formatter.format_chat_response(
                response=response,
                session_id=session_id,
            )

        except Exception as exc:
            logger.exception("LLM chat generation failed: %s", exc)
            message = "Erreur technique pendant la generation de la reponse IA. Consultez les logs backend."
            return self.response_formatter.format_error_response(
                message=message,
                session_id=session_id,
            )

    def explain_calculation_result(self, result: dict) -> str:
        prompt = self.prompt_builder.build_explanation_prompt(result)
        response = self._call_llm(prompt=prompt)
        return self.response_formatter.clean_llm_response(response)

    def get_chat_history(self, token: str | None = None) -> list:
        if self.db is None:
            return []

        return (
            self.db.query(ChatHistory)
            .order_by(ChatHistory.created_at.desc())
            .limit(50)
            .all()
        )

    def clear_chat_history(self, token: str | None = None) -> dict:
        if self.db is None:
            return {
                "success": False,
                "message": "Base de donnees non disponible",
            }

        self.db.query(ChatHistory).delete()
        self.db.commit()
        return {
            "success": True,
            "message": "Historique supprime avec succes",
        }

    def _call_llm(
        self,
        prompt: str,
        messages: list[dict[str, str]] | None = None,
        user_message: str | None = None,
        **_: object,
    ) -> str:
        chat_messages = messages or [{"role": "user", "content": prompt}]
        providers = self._provider_order()
        errors = []

        for provider in providers:
            try:
                if provider == "ollama":
                    return self._call_ollama(prompt)

                if provider == "openai":
                    return self._call_openai(chat_messages)

                if provider == "groq":
                    return self._call_groq(chat_messages)
            except Exception as exc:
                logger.exception("LLM provider %s failed: %s", provider, exc)
                errors.append(f"{provider}: {exc}")

        raise RuntimeError("All configured LLM providers failed: " + " | ".join(errors))

    @staticmethod
    def _provider_order() -> list[str]:
        configured = settings.LLM_PROVIDER.lower()
        providers = [configured]

        if settings.GROQ_API_KEY and "groq" not in providers:
            providers.append("groq")

        if settings.OPENAI_API_KEY and "openai" not in providers:
            providers.append("openai")

        if "ollama" not in providers:
            providers.append("ollama")

        return providers

    def _call_ollama(self, prompt: str) -> str:
        url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": settings.LLM_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": settings.LLM_TEMPERATURE,
                "num_predict": settings.LLM_MAX_TOKENS,
            },
        }

        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json().get("response", "")

    def _call_openai(self, messages: list[dict[str, str]]) -> str:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.LLM_MODEL or "gpt-4o-mini",
            "messages": messages,
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS,
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def _call_groq(self, messages: list[dict[str, str]]) -> str:
        if not settings.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not configured")

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.LLM_MODEL if settings.LLM_MODEL != "llama3" else "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS,
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def _retrieve_rag_context(self, message: str) -> str:
        try:
            logger.info("RAG called for query=%s", message)
            docs = self.rag_retriever.invoke(message)
            logger.info("RAG retrieved %s chunks for query=%s", len(docs), message)
            rag_context = "\n\n".join(doc.page_content for doc in docs)
            logger.info("RAG context length=%s", len(rag_context or ""))
            return rag_context
        except Exception as exc:
            logger.exception("RAG retrieval failed for query=%s: %s", message, exc)
            return ""

    def _get_recent_history(self, session_id: str) -> list[dict]:
        if self.db is None:
            return []

        try:
            histories = (
                self.db.query(ChatHistory)
                .filter(ChatHistory.session_id == session_id)
                .order_by(ChatHistory.created_at.desc())
                .limit(10)
                .all()
            )
        except Exception:
            self.db.rollback()
            return []

        return [
            {
                "user_message": history.user_message,
                "assistant_response": history.assistant_response,
            }
            for history in reversed(histories)
        ]

    def _save_chat_history(
        self,
        user_id: int | None,
        session_id: str,
        user_message: str,
        assistant_response: str,
        context: dict | None = None,
    ) -> None:
        if self.db is None:
            return

        history = ChatHistory(
            user_id=user_id,
            session_id=session_id,
            user_message=user_message,
            assistant_response=assistant_response,
            context=context,
        )

        try:
            self.db.add(history)
            self.db.commit()
        except Exception:
            self.db.rollback()
