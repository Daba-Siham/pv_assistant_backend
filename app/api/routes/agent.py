from fastapi import APIRouter, status

from app.dependencies import DBSession, AuthToken
from app.schemas.agent import AgentRequest, AgentResponse, ToolExecutionRequest, ToolExecutionResponse
from app.services.agent.agent_service import AgentService

router = APIRouter()


@router.post("/run", response_model=AgentResponse, status_code=status.HTTP_200_OK)
def run_agent(request: AgentRequest, db: DBSession, token: AuthToken):
    agent_service = AgentService(db=db)
    return agent_service.run(request=request, token=token)


@router.post("/execute-tool", response_model=ToolExecutionResponse, status_code=status.HTTP_200_OK)
def execute_tool(request: ToolExecutionRequest, db: DBSession, token: AuthToken):
    agent_service = AgentService(db=db)
    return agent_service.execute_tool(request=request, token=token)


@router.get("/tools", status_code=status.HTTP_200_OK)
def list_available_tools():
    agent_service = AgentService()
    return agent_service.list_tools()