from fastapi import APIRouter, status

from app.dependencies import AuthToken, DBSession
from app.schemas.chat import ChatRequest, ChatResponse, ChatHistoryResponse
from app.services.llm.llm_service import LLMService


router = APIRouter()


@router.post("/", response_model=ChatResponse, status_code=status.HTTP_200_OK)
def chat(request: ChatRequest, db: DBSession, token: AuthToken):
    llm_service = LLMService(db=db)
    return llm_service.generate_response(request=request, token=token)


@router.get("/history", response_model=list[ChatHistoryResponse], status_code=status.HTTP_200_OK)
def get_chat_history(db: DBSession, token: AuthToken):
    llm_service = LLMService(db=db)
    return llm_service.get_chat_history(token=token)


@router.delete("/history", status_code=status.HTTP_200_OK)
def clear_chat_history(db: DBSession, token: AuthToken):
    llm_service = LLMService(db=db)
    return llm_service.clear_chat_history(token=token)
