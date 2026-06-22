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
IN_MEMORY_HISTORY: dict[str, list[dict[str, str]]] = {}


class LLMService:
    def __init__(self, db: Session | None = None):
        self.db = db
        self.prompt_builder = PromptBuilder()
        self.response_formatter = ResponseFormatter()
        self.rag_retriever = RAGRetriever()

    def generate_response(self, request: ChatRequest, token: str | None = None) -> dict:
        session_id = request.session_id or str(uuid.uuid4())

        try:
            full_chat_history = self._get_recent_history(session_id)

            skip_rag = self._should_skip_rag(request.message)
            skip_history = self._should_skip_history(request.message)

            logger.info("skip_rag=%s for message=%s", skip_rag, request.message)
            logger.info("skip_history=%s for message=%s", skip_history, request.message)

            chat_history_for_prompt = [] if skip_history else full_chat_history

            if skip_rag:
                rag_context = ""
            else:
                rag_query = self._build_rag_query(request.message, full_chat_history)
                logger.info("rag_query=%s", rag_query)
                rag_context = self._retrieve_rag_context(rag_query)

            prompt = self.prompt_builder.build_chat_prompt(
                request=request,
                rag_context=rag_context,
                calculation_result=None,
                agent_result=None,
                chat_history=chat_history_for_prompt,
            )
            logger.info("prompt length=%s", len(prompt))

            raw_response = self._call_llm(prompt)
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
            if self._is_rate_limit_error(exc):
                return self.response_formatter.format_error_response(
                    message="La limite du fournisseur IA est atteinte. Veuillez réessayer dans quelques instants.",
                    session_id=session_id,
                )
            return self.response_formatter.format_error_response(
                message="Erreur technique pendant la generation de la reponse IA. Consultez les logs backend.",
                session_id=session_id,
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
        IN_MEMORY_HISTORY.clear()

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

    def _call_llm(self, prompt: str, **_: object) -> str:
        provider = settings.LLM_PROVIDER.lower()

        if provider == "ollama":
            return self._call_ollama(prompt)

        if provider == "openai":
            return self._call_openai(prompt)

        if provider == "groq":
            return self._call_groq(prompt)

        raise RuntimeError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")

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

        data = response.json()
        return data.get("response", "")

    def _call_openai(self, prompt: str) -> str:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": settings.LLM_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": self.prompt_builder.build_system_prompt(),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS,
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"]

    def _call_groq(self, prompt: str) -> str:
        if not settings.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not configured")

        url = "https://api.groq.com/openai/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": settings.LLM_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": self.prompt_builder.build_system_prompt(),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS,
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"]

    def _retrieve_rag_context(self, message: str) -> str:
        try:
            logger.info("RAG called for query=%s", message)
            rag_context = self.rag_retriever.retrieve_context_only(message)
            original_length = len(rag_context or "")
            limited_context = (rag_context or "")[:2000]
            logger.info("RAG context length before=%s after=%s", original_length, len(limited_context))
            return limited_context
        except Exception as exc:
            logger.exception("RAG retrieval failed for query=%s: %s", message, exc)
            return ""

    def _build_rag_query(self, message: str, chat_history: list[dict]) -> str:
        if self._should_skip_rag(message):
            return message

        if not self._is_short_followup(message) or not chat_history:
            return message

        topic = self._extract_recent_topic(chat_history)
        if not topic:
            return message

        return f"{message} about {topic}"

    @staticmethod
    def _is_short_followup(message: str) -> bool:
        normalized = message.strip().lower()
        if LLMService._should_skip_rag(normalized):
            return False

        if len(normalized.split()) <= 3:
            return True

        exact_followups = {
            "informations",
            "continue",
        }
        if normalized in exact_followups:
            return True

        followups = [
            "more details",
            "more information",
            "donne plus",
            "plus de details",
            "plus de détails",
            "translate to french",
            "speak english",
        ]
        return any(phrase in normalized for phrase in followups)

    @staticmethod
    def _should_skip_rag(message: str) -> bool:
        normalized = " ".join(message.strip().lower().split())
        if not normalized:
            return True

        skip_messages = {
            "hi",
            "hello",
            "bonjour",
            "salut",
            "salam",
            "speak english",
            "in english",
            "answer in english",
            "réponds en français",
            "reponds en francais",
            "répondre en français",
            "repondre en francais",
            "alors repondre en francais",
            "alors réponds en français",
            "alors reponds en francais",
            "translate to french",
            "traduit en français",
            "traduit en francais",
        }
        return normalized in skip_messages

    @staticmethod
    def _should_skip_history(message: str) -> bool:
        normalized = " ".join(message.strip().lower().split())
        if not normalized:
            return True

        skip_messages = {
            "hi",
            "hello",
            "hey",
            "bonjour",
            "salut",
            "salam",
            "السلام عليكم",
            "مرحبا",
            "speak english",
            "in english",
            "answer in english",
            "réponds en français",
            "reponds en francais",
            "répondre en français",
            "repondre en francais",
            "alors repondre en francais",
            "alors réponds en français",
            "alors reponds en francais",
        }

        return normalized in skip_messages

    @staticmethod
    def _extract_recent_topic(chat_history: list[dict]) -> str | None:
        topics = {
            "solar panels": ["panel", "panels", "panneau", "panneaux"],
            "photovoltaic energy": ["photovoltaic", "photovoltaique", "photovoltaïque", "solaire", "solar"],
            "batteries": ["battery", "batterie", "batteries"],
            "inverters": ["inverter", "onduleur", "inverters"],
            "ROI": ["roi", "rentabilite", "rentabilité"],
            "monitoring": ["monitoring", "surveillance"],
        }

        for item in reversed(chat_history):
            text = f"{item.get('user_message', '')} {item.get('assistant_response', '')}".lower()
            for topic, keywords in topics.items():
                if any(keyword in text for keyword in keywords):
                    return topic

        return None

    @staticmethod
    def _is_rate_limit_error(exc: Exception) -> bool:
        response = getattr(exc, "response", None)
        return getattr(response, "status_code", None) == 429

    def _get_recent_history(self, session_id: str) -> list[dict]:
        if self.db is None:
            return IN_MEMORY_HISTORY.get(session_id, [])[-10:]

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
            return IN_MEMORY_HISTORY.get(session_id, [])[-10:]

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
        IN_MEMORY_HISTORY.setdefault(session_id, []).append(
            {
                "user_message": user_message,
                "assistant_response": assistant_response,
            }
        )
        IN_MEMORY_HISTORY[session_id] = IN_MEMORY_HISTORY[session_id][-10:]

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
