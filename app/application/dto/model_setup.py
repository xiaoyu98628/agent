from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProviderConfigField:
    name: str
    label: str
    required: bool = False
    secret: bool = False
    placeholder: str | None = None


@dataclass(frozen=True)
class ModelOption:
    id: str
    name: str | None = None
    reasoning: bool = False
    input: list[str] = field(default_factory=lambda: ["text"])
    context_window: int | None = None
    max_tokens: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
