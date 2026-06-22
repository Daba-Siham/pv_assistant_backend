from datetime import datetime
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str | None = Field(default=None, min_length=1)
    question: str | None = Field(default=None, min_length=1)
    session_id: str | None = None
    user_id: int | None = None
    context: dict | None = None

    @property
    def text(self) -> str:
        return self.question or self.message or ""


class ChatResponse(BaseModel):
    response: str
    session_id: str | None = None
    user_id: int | None = None
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


class ChatSessionResponse(BaseModel):
    id: int
    session_id: str
    title: str | None = None
    created_at: datetime
    updated_at: datetime
    last_message: str | None = None

    class Config:
        from_attributes = True


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
