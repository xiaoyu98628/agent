from pydantic import BaseModel, Field


class ModelSelectionResponse(BaseModel):
    provider: str
    model: str
    temperature: float | None = None
    max_tokens: int | None = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str | None = None
    model: ModelSelectionResponse


class ModelOptionItem(BaseModel):
    provider: str
    model: str
    label: str
    supports_tools: bool = True


class ModelOptionsResponse(BaseModel):
    catalog_source: str
    providers: list[str]
    models: list[ModelOptionItem]
    default: ModelSelectionResponse
