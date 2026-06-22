from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    user_message: str = Field(..., min_length=1)
    session_id: str | None = None
    user_inputs: dict | None = None


class AgentResponse(BaseModel):
    success: bool
    message: str
    session_id: str | None = None
    action: str | None = None
    tools_used: list[str] = []
    result: dict | None = None
    recommendations: list[str] = []


class ToolExecutionRequest(BaseModel):
    tool_name: str = Field(..., min_length=1)
    parameters: dict = Field(default_factory=dict)


class ToolExecutionResponse(BaseModel):
    success: bool
    tool_name: str
    result: dict | None = None
    error: str | None = None
