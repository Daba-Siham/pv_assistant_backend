from sqlalchemy.orm import Session

from app.schemas.agent import (
    AgentRequest,
    ToolExecutionRequest,
)
from app.services.agent.workflow import AgentWorkflow


class AgentService:
    def __init__(self, db: Session | None = None):
        self.db = db
        self.workflow = AgentWorkflow(db=db)

    def run(self, request: AgentRequest, token: str | None = None) -> dict:
        result = self.workflow.run(
            user_message=request.user_message,
            user_inputs=request.user_inputs,
            session_id=request.session_id,
            token=token
        )

        return {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "session_id": result.get("session_id", request.session_id),
            "action": result.get("action"),
            "tools_used": result.get("tools_used", []),
            "result": result.get("result"),
            "recommendations": result.get("recommendations", [])
        }

    def execute_tool(
        self,
        request: ToolExecutionRequest,
        token: str | None = None
    ) -> dict:
        execution = self.workflow.execute_tool(
            tool_name=request.tool_name,
            parameters=request.parameters,
            token=token
        )

        return {
            "success": execution.get("success", False),
            "tool_name": execution.get("tool_name", request.tool_name),
            "result": execution.get("result"),
            "error": execution.get("error")
        }

    def list_tools(self) -> list[dict]:
        return self.workflow.list_tools()
