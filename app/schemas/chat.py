from datetime import datetime
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: str | None = None
    user_id: int | None = None
    context: dict | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str | None = None
    sources: list[str] = []
    suggested_questions: list[str] = []
    calculation_result: dict | None = None
    agent_result: dict | None = None


class ChatHistoryResponse(BaseModel):
    id: int
    user_message: str
    assistant_response: str
    session_id: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True