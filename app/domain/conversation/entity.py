from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Conversation:
    id: str
    workspace_id: str
    title: str | None
    model_provider: str
    model_name: str
    temperature: float | None
    max_tokens: int | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class Message:
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: datetime
