from typing import Protocol

from app.domain.conversation.entity import Conversation, Message


class ConversationRepository(Protocol):
    async def create(self, conversation: Conversation) -> Conversation: ...

    async def get(self, *, conversation_id: str, workspace_id: str) -> Conversation | None: ...

    async def list_by_workspace(
        self,
        *,
        workspace_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Conversation]: ...

    async def update_model(
        self,
        *,
        conversation_id: str,
        workspace_id: str,
        model_provider: str,
        model_name: str,
        temperature: float | None,
        max_tokens: int | None,
    ) -> None: ...

    async def update_title(self, *, conversation_id: str, workspace_id: str, title: str) -> None: ...

    async def delete(self, *, conversation_id: str, workspace_id: str) -> bool: ...

    async def add_message(self, message: Message) -> Message: ...

    async def list_messages(self, *, conversation_id: str) -> list[Message]: ...
