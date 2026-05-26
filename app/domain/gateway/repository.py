from typing import Protocol

from app.domain.gateway.entity import GatewayBinding


class GatewayBindingRepository(Protocol):
    async def get_binding(
        self,
        *,
        platform: str,
        external_chat_id: str,
        workspace_id: str,
    ) -> GatewayBinding | None: ...

    async def upsert_binding(
        self,
        *,
        platform: str,
        external_chat_id: str,
        workspace_id: str,
        conversation_id: str | None,
    ) -> GatewayBinding: ...
