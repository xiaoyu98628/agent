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
    metadata: dict[str, Any] = field(default_factory=dict)
