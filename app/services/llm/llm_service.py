import uuid
from datetime import datetime

import requests
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import get_user_id_from_token
from app.models.chat_history import ChatHistory
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.user import User
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
        message_text = request.text.strip()
        session_id = request.session_id or str(uuid.uuid4())
        current_user = self._get_current_user(token)
        user_id = current_user.id if current_user else request.user_id
        chat_session = self._get_or_create_chat_session(user_id, session_id, message_text)
        active_recommendation = self._build_active_recommendation_context(request.context or {})
        suggested_questions = self._extract_suggested_questions(active_recommendation)

        try:
            full_chat_history = (
                self._get_recent_session_messages(chat_session.id)
                if chat_session
                else self._get_recent_history(session_id, user_id=user_id)
            )

            if chat_session:
                self._save_chat_message(chat_session.id, "user", message_text)

            skip_rag = self._should_skip_rag(message_text)
            skip_history = self._should_skip_history(message_text)

            logger.info("skip_rag=%s for message=%s", skip_rag, message_text)
            logger.info("skip_history=%s for message=%s", skip_history, message_text)

            chat_history_for_prompt = [] if skip_history else full_chat_history

            if skip_rag:
                rag_context = ""
            else:
                rag_query = self._build_rag_query(message_text, full_chat_history)
                logger.info("rag_query=%s", rag_query)
                rag_context = self._retrieve_rag_context(rag_query)

            prompt = self.prompt_builder.build_chat_prompt(
                request=request,
                rag_context=rag_context,
                calculation_result=None,
                agent_result=None,
                active_recommendation=active_recommendation,
                suggested_questions=suggested_questions,
                chat_history=chat_history_for_prompt,
                user_profile=self._build_user_profile(current_user),
            )
            logger.info("prompt length=%s", len(prompt))

            raw_response = self._call_llm(prompt)
            response = self.response_formatter.clean_llm_response(raw_response)

            if chat_session:
                self._save_chat_message(chat_session.id, "assistant", response)
                chat_session.updated_at = datetime.utcnow()
                self.db.commit()

            self._save_chat_history(
                user_id=user_id,
                session_id=session_id,
                user_message=message_text,
                assistant_response=response,
                context=request.context,
            )

            return self.response_formatter.format_chat_response(
                response=response,
                session_id=session_id,
                user_id=user_id,
                suggested_questions=suggested_questions,
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

    def get_chat_history(
        self,
        token: str | None = None,
        session_id: str | None = None,
        limit: int = 50,
    ) -> list:
        if self.db is None:
            return []

        user = self._get_current_user(token)
        if not user:
            return []

        query = self.db.query(ChatHistory).filter(ChatHistory.user_id == user.id)
        if session_id:
            query = query.filter(ChatHistory.session_id == session_id)

        histories = query.order_by(ChatHistory.created_at.desc()).limit(limit).all()

        return histories

    def clear_chat_history(self, token: str | None = None, session_id: str | None = None) -> dict:
        IN_MEMORY_HISTORY.clear()

        if self.db is None:
            return {
                "success": False,
                "message": "Base de donnees non disponible",
            }

        user = self._get_current_user(token)
        if not user:
            return {
                "success": False,
                "message": "Utilisateur non authentifie",
            }

        query = self.db.query(ChatHistory).filter(ChatHistory.user_id == user.id)
        if session_id:
            query = query.filter(ChatHistory.session_id == session_id)

        deleted = query.delete(synchronize_session=False)
        self.db.commit()

        return {
            "success": True,
            "deleted": deleted,
            "message": "Historique supprime avec succes",
        }

    def get_chat_sessions(self, token: str | None = None) -> list[dict]:
        if self.db is None:
            return []

        user = self._get_current_user(token)
        if not user:
            return []

        sessions = (
            self.db.query(ChatSession)
            .filter(ChatSession.user_id == user.id)
            .order_by(ChatSession.updated_at.desc())
            .all()
        )

        result = []
        for session in sessions:
            last_message = (
                self.db.query(ChatMessage)
                .filter(ChatMessage.session_id == session.id)
                .order_by(ChatMessage.created_at.desc())
                .first()
            )
            result.append(
                {
                    "id": session.id,
                    "session_id": session.session_id,
                    "title": session.title,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                    "last_message": last_message.content if last_message else None,
                }
            )
        return result

    def get_chat_session_messages(self, token: str | None, session_id: str) -> list[ChatMessage]:
        if self.db is None:
            return []

        user = self._get_current_user(token)
        if not user:
            return []

        session = (
            self.db.query(ChatSession)
            .filter(ChatSession.user_id == user.id, ChatSession.session_id == session_id)
            .first()
        )
        if not session:
            return []

        return (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )

    def save_chat_message(
        self,
        token: str | None,
        session_id: str,
        role: str,
        content: str,
        context: dict | None = None,
    ) -> dict:
        if self.db is None:
            return {"success": False, "session_id": session_id, "message": "Base de donnees non disponible"}

        user = self._get_current_user(token)
        if not user:
            return {"success": False, "session_id": session_id, "message": "Utilisateur non authentifie"}

        message_text = (content or "").strip()
        if not message_text:
            return {"success": True, "session_id": session_id, "message": "Message vide ignore"}

        chat_session = self._get_or_create_chat_session(user.id, session_id, message_text)
        if chat_session is None:
            return {"success": False, "session_id": session_id, "message": "Session de chat introuvable"}

        message = ChatMessage(
            session_id=chat_session.id,
            role=role,
            content=message_text,
            metadata_=context if isinstance(context, dict) else None,
        )

        try:
            self.db.add(message)

            if not chat_session.title:
                chat_session.title = self._make_session_title(message_text)

            chat_session.updated_at = datetime.utcnow()
            self.db.commit()
            return {"success": True, "session_id": session_id}
        except Exception as exc:
            logger.exception("Failed to save chat message: %s", exc)
            self.db.rollback()
            return {
                "success": False,
                "session_id": session_id,
                "message": "Impossible de sauvegarder le message",
            }

    def delete_chat_session(self, token: str | None, session_id: str) -> dict:
        if self.db is None:
            return {"success": False, "message": "Base de donnees non disponible"}

        user = self._get_current_user(token)
        if not user:
            return {"success": False, "message": "Utilisateur non authentifie"}

        deleted = (
            self.db.query(ChatSession)
            .filter(ChatSession.user_id == user.id, ChatSession.session_id == session_id)
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return {"success": True, "deleted": deleted}

    def delete_all_chat_sessions(self, token: str | None) -> dict:
        if self.db is None:
            return {"success": False, "message": "Base de donnees non disponible"}

        user = self._get_current_user(token)
        if not user:
            return {"success": False, "message": "Utilisateur non authentifie"}

        deleted = (
            self.db.query(ChatSession)
            .filter(ChatSession.user_id == user.id)
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return {"success": True, "deleted": deleted}

    def _get_current_user(self, token: str | None) -> User | None:
        if self.db is None or not token:
            return None

        user_id = get_user_id_from_token(token)
        if user_id is None:
            return None

        return self.db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def _build_user_profile(user: User | None) -> dict | None:
        if not user:
            return None

        return {
            "name": user.full_name,
            "email": user.email,
            "knowledge_level": user.knowledge_level,
        }

    @staticmethod
    def _build_active_recommendation_context(context: dict | None) -> dict | None:
        if not isinstance(context, dict):
            return None

        active = context.get("active_recommendation")
        if not isinstance(active, dict):
            return None

        result = active.get("result") or {}
        input_data = active.get("input") or {}
        formatted = (
            result.get("formatted_recommendation", {}) if isinstance(result, dict) else {}
        )
        recommendation_data = formatted.get("recommendation_data", {}) if isinstance(formatted, dict) else {}
        user_friendly = (
            formatted.get("user_friendly_recommendation", {}) if isinstance(formatted, dict) else {}
        )
        scenario_analysis = recommendation_data.get("scenario_analysis", {}) if isinstance(recommendation_data, dict) else {}

        summary = {
            "timestamp": active.get("timestamp"),
            "input": {
                "city": input_data.get("city"),
                "installation_type": input_data.get("installation_type"),
                "daily_consumption_kwh": input_data.get("daily_consumption_kwh"),
                "available_area_m2": input_data.get("available_area_m2"),
                "budget": input_data.get("budget"),
                "orientation": input_data.get("orientation"),
                "autonomy_days": input_data.get("autonomy_days"),
                "roof_type": input_data.get("roof_type"),
                "tilt_angle": input_data.get("tilt_angle"),
                "shading": input_data.get("shading"),
            },
            "recommendation": {
                "global_status": recommendation_data.get("global_status"),
                "detected_scenarios": recommendation_data.get("detected_scenarios", []),
                "panels_range": recommendation_data.get("panels_range"),
                "panel_power_range": recommendation_data.get("panel_power_range"),
                "pv_power_range": recommendation_data.get("pv_power_range"),
                "battery_range": recommendation_data.get("battery_range"),
                "battery_visible": recommendation_data.get("battery_visible"),
                "inverter_type": recommendation_data.get("inverter_type"),
                "inverter_range": recommendation_data.get("inverter_range"),
                "budget_estimated_range": recommendation_data.get("budget_estimated_range"),
                "roi_range": recommendation_data.get("roi_range"),
                "roi_category": recommendation_data.get("roi_category"),
                "scenario_analysis": scenario_analysis,
                "points_to_check": recommendation_data.get("points_to_check", []),
                "questions_to_ask": recommendation_data.get("questions_to_ask", []),
                "scenarios": recommendation_data.get("scenarios", {}),
                "conclusion": recommendation_data.get("conclusion"),
            },
            "formatted_summary": user_friendly,
        }

        return summary

    @staticmethod
    def _extract_suggested_questions(active_recommendation: dict | None) -> list[str]:
        if not isinstance(active_recommendation, dict):
            return []

        recommendation = active_recommendation.get("recommendation") or {}
        questions = recommendation.get("questions_to_ask") or []
        if not isinstance(questions, list):
            return []

        seen: set[str] = set()
        result: list[str] = []
        for item in questions:
            question = str(item or "").strip()
            if not question:
                continue
            key = question.lower()
            if key in seen:
                continue
            seen.add(key)
            result.append(question)
        return result[:6]

    def _get_or_create_chat_session(
        self,
        user_id: int | None,
        session_id: str,
        first_message: str,
    ) -> ChatSession | None:
        if self.db is None or user_id is None:
            return None

        chat_session = (
            self.db.query(ChatSession)
            .filter(ChatSession.user_id == user_id, ChatSession.session_id == session_id)
            .first()
        )
        if chat_session:
            return chat_session

        chat_session = ChatSession(
            user_id=user_id,
            session_id=session_id,
            title=self._make_session_title(first_message),
        )
        self.db.add(chat_session)
        self.db.commit()
        self.db.refresh(chat_session)
        return chat_session

    @staticmethod
    def _make_session_title(message: str) -> str:
        words = message.strip().split()
        return " ".join(words[:6])[:255] or "Nouvelle conversation"

    def _save_chat_message(self, session_pk: int, role: str, content: str) -> None:
        if self.db is None:
            return

        self.db.add(ChatMessage(session_id=session_pk, role=role, content=content))
        self.db.commit()

    def _get_recent_session_messages(self, session_pk: int, limit: int = 10) -> list[dict]:
        if self.db is None:
            return []

        messages = (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_pk)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all()
        )

        pairs = []
        current_user_message = None
        for message in reversed(messages):
            if message.role == "user":
                current_user_message = message.content
            elif message.role == "assistant" and current_user_message:
                pairs.append(
                    {
                        "user_message": current_user_message,
                        "assistant_response": message.content,
                    }
                )
                current_user_message = None

        return pairs

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

    def _get_recent_history(self, session_id: str, user_id: int | None = None) -> list[dict]:
        if self.db is None:
            return IN_MEMORY_HISTORY.get(session_id, [])[-10:]

        try:
            query = self.db.query(ChatHistory).filter(ChatHistory.session_id == session_id)
            if user_id is not None:
                query = query.filter(ChatHistory.user_id == user_id)

            histories = query.order_by(ChatHistory.created_at.desc()).limit(10).all()
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
