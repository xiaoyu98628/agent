from fastapi import APIRouter

from app.infrastructure.tools.registry import describe_agent_tools
from app.interfaces.http.schemas.responses.agent import AgentToolItem, AgentToolsResponse
from app.interfaces.http.support.response.json import JsonResponse
from config.config import config

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/tools", summary="当前可用工具列表")
async def get_agent_tools() -> JsonResponse[AgentToolsResponse]:
    payload = describe_agent_tools(config())
    data = AgentToolsResponse(
        deployment_mode=payload["deployment_mode"],
        policy=payload["policy"],
        toolsets=list(payload["toolsets"]),
        allow_write=payload["allow_write"],
        allow_terminal=payload["allow_terminal"],
        workspace_dir=payload["workspace_dir"],
        tools=[AgentToolItem.model_validate(item) for item in payload["tools"]],
    )
    return JsonResponse.success(data=data)
