from dataclasses import dataclass
from datetime import datetime
from typing import Literal

MemoryTarget = Literal["memory", "user"]


@dataclass(frozen=True, slots=True)
class MemoryEntry:
    id: str
    workspace_id: str
    target: MemoryTarget
    content: str
    created_at: datetime
    updated_at: datetime
