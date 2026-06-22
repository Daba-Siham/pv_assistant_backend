from fastapi import APIRouter, Query, status

from app.dependencies import AuthToken, DBSession
from app.schemas.chat import (
    ChatHistoryResponse,
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ChatSessionResponse,
)
from app.services.llm.llm_service import LLMService


router = APIRouter()


@router.post("/", response_model=ChatResponse, status_code=status.HTTP_200_OK)
def chat(request: ChatRequest, db: DBSession, token: AuthToken):
    llm_service = LLMService(db=db)
    return llm_service.generate_response(request=request, token=token)


@router.get("/history", response_model=list[ChatHistoryResponse], status_code=status.HTTP_200_OK)
def get_chat_history(
    db: DBSession,
    token: AuthToken,
    session_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
):
    llm_service = LLMService(db=db)
    return llm_service.get_chat_history(token=token, session_id=session_id, limit=limit)


@router.delete("/history", status_code=status.HTTP_200_OK)
def clear_chat_history(
    db: DBSession,
    token: AuthToken,
    session_id: str | None = Query(default=None),
):
    llm_service = LLMService(db=db)
    return llm_service.clear_chat_history(token=token, session_id=session_id)


@router.get("/sessions", response_model=list[ChatSessionResponse], status_code=status.HTTP_200_OK)
def get_chat_sessions(db: DBSession, token: AuthToken):
    llm_service = LLMService(db=db)
    return llm_service.get_chat_sessions(token=token)


@router.get(
    "/sessions/{session_id}/messages",
    response_model=list[ChatMessageResponse],
    status_code=status.HTTP_200_OK,
)
def get_chat_session_messages(session_id: str, db: DBSession, token: AuthToken):
    llm_service = LLMService(db=db)
    return llm_service.get_chat_session_messages(token=token, session_id=session_id)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_200_OK)
def delete_chat_session(session_id: str, db: DBSession, token: AuthToken):
    llm_service = LLMService(db=db)
    return llm_service.delete_chat_session(token=token, session_id=session_id)


@router.delete("/sessions", status_code=status.HTTP_200_OK)
def delete_all_chat_sessions(db: DBSession, token: AuthToken):
    llm_service = LLMService(db=db)
    return llm_service.delete_all_chat_sessions(token=token)
