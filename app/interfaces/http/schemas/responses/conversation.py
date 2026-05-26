from datetime import datetime

from pydantic import BaseModel, Field

from app.interfaces.http.schemas.responses.chat import ModelSelectionResponse


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime


class ConversationResponse(BaseModel):
    id: str
    workspace_id: str
    title: str | None
    model: ModelSelectionResponse
    created_at: datetime
    updated_at: datetime


class ConversationDetailResponse(ConversationResponse):
    messages: list[MessageResponse] = Field(default_factory=list)
