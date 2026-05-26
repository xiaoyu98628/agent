from pydantic import BaseModel, Field


class ModelSelectionRequest(BaseModel):
    provider: str | None = Field(default=None, description="provider，如 openrouter / openai")
    model: str | None = Field(default=None, description="模型 ID")
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1)


class ChatHistoryMessage(BaseModel):
    role: str = Field(description="user / assistant / system")
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, description="用户消息")
    conversation_id: str | None = Field(default=None, description="会话 ID；不传则自动创建新会话")
    model: ModelSelectionRequest | None = Field(default=None, description="可选，覆盖默认/会话模型")
    history: list[ChatHistoryMessage] = Field(
        default_factory=list,
        description="无 conversation_id 时可选传入临时历史；有 conversation_id 时忽略",
    )
