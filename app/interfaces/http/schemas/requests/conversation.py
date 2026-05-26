from pydantic import BaseModel, Field

from app.interfaces.http.schemas.requests.chat import ModelSelectionRequest


class CreateConversationRequest(BaseModel):
    title: str | None = Field(default=None, description="会话标题")
    model: ModelSelectionRequest | None = Field(default=None, description="绑定模型")


class ConversationListQuery(BaseModel):
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
