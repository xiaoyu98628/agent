from dataclasses import dataclass, field
from typing import Any, Literal

ChatRole = Literal["system", "user", "assistant", "tool"]


@dataclass(frozen=True)
class ModelSelection:
    provider: str
    name: str


@dataclass(frozen=True)
class ChatMessage:
    role: ChatRole
    content: str


@dataclass(frozen=True)
class ChatRequest:
    messages: list[ChatMessage]
    model: ModelSelection | None = None
    temperature: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ChatResponse:
    content: str
    model: ModelSelection | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    raw: Any | None = None
