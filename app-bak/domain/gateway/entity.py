from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class GatewayBinding:
    platform: str
    external_chat_id: str
    workspace_id: str
    conversation_id: str | None
    updated_at: datetime
