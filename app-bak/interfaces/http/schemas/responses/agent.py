from pydantic import BaseModel, Field


class AgentToolItem(BaseModel):
    name: str
    description: str = ""


class AgentToolsResponse(BaseModel):
    deployment_mode: str
    policy: str
    toolsets: list[str]
    allow_write: bool
    allow_terminal: bool
    workspace_dir: str
    tools: list[AgentToolItem] = Field(default_factory=list)
