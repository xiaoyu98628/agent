from datetime import UTC, datetime

from app.application.support.ids import new_id
from app.application.support.text import sanitize_text
from app.domain.conversation.entity import Conversation, Message
from app.domain.conversation.enums import MessageRole
from app.domain.conversation.exceptions import ConversationNotFoundError
from app.domain.conversation.repository import ConversationRepository
from app.domain.llm.entity import ModelSelection
from app.infrastructure.llm.selection import resolve_selection
from app.infrastructure.storage.sqlite.conversation_repository import new_message
from config.config import config


def _now() -> datetime:
    return datetime.now(UTC)


def _title_from_message(message: str) -> str:
    text = message.strip().replace("\n", " ")
    return text[:50] + ("..." if len(text) > 50 else "")


class ConversationService:
    def __init__(self, repository: ConversationRepository) -> None:
        self._repository = repository

    @property
    def workspace_id(self) -> str:
        return config().storage.default_workspace_id

    async def create(
        self,
        *,
        title: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> Conversation:
        selection = resolve_selection(
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        now = _now()
        conversation = Conversation(
            id=new_id(),
            workspace_id=self.workspace_id,
            title=title,
            model_provider=selection.provider,
            model_name=selection.model,
            temperature=selection.temperature,
            max_tokens=selection.max_tokens,
            created_at=now,
            updated_at=now,
        )
        return await self._repository.create(conversation)

    async def get(self, conversation_id: str) -> Conversation:
        conversation = await self._repository.get(
            conversation_id=conversation_id,
            workspace_id=self.workspace_id,
        )
        if conversation is None:
            raise ConversationNotFoundError(f"会话不存在: {conversation_id}")
        return conversation

    async def get_with_messages(self, conversation_id: str) -> tuple[Conversation, list[Message]]:
        conversation = await self.get(conversation_id)
        messages = await self._repository.list_messages(conversation_id=conversation_id)
        return conversation, messages

    async def list_conversations(self, *, limit: int = 50, offset: int = 0) -> list[Conversation]:
        return await self._repository.list_by_workspace(
            workspace_id=self.workspace_id,
            limit=limit,
            offset=offset,
        )

    async def delete(self, conversation_id: str) -> None:
        deleted = await self._repository.delete(
            conversation_id=conversation_id,
            workspace_id=self.workspace_id,
        )
        if not deleted:
            raise ConversationNotFoundError(f"会话不存在: {conversation_id}")

    async def resolve_selection_for_chat(
        self,
        *,
        conversation: Conversation | None,
        provider: str | None,
        model: str | None,
        temperature: float | None,
        max_tokens: int | None,
    ) -> ModelSelection:
        if conversation is None:
            return resolve_selection(
                provider=provider,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        has_override = any(value is not None for value in (provider, model, temperature, max_tokens))
        if not has_override:
            return ModelSelection(
                provider=conversation.model_provider,
                model=conversation.model_name,
                temperature=conversation.temperature,
                max_tokens=conversation.max_tokens,
            )

        selection = resolve_selection(
            provider=provider or conversation.model_provider,
            model=model or conversation.model_name,
            temperature=temperature if temperature is not None else conversation.temperature,
            max_tokens=max_tokens if max_tokens is not None else conversation.max_tokens,
        )
        await self._repository.update_model(
            conversation_id=conversation.id,
            workspace_id=conversation.workspace_id,
            model_provider=selection.provider,
            model_name=selection.model,
            temperature=selection.temperature,
            max_tokens=selection.max_tokens,
        )
        return selection

    async def ensure_conversation(
        self,
        *,
        conversation_id: str | None,
        user_message: str,
        provider: str | None,
        model: str | None,
        temperature: float | None,
        max_tokens: int | None,
    ) -> Conversation:
        if conversation_id:
            return await self.get(conversation_id)

        selection = resolve_selection(
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        now = _now()
        conversation = Conversation(
            id=new_id(),
            workspace_id=self.workspace_id,
            title=_title_from_message(user_message),
            model_provider=selection.provider,
            model_name=selection.model,
            temperature=selection.temperature,
            max_tokens=selection.max_tokens,
            created_at=now,
            updated_at=now,
        )
        return await self._repository.create(conversation)

    async def load_history(self, conversation_id: str) -> list[Message]:
        messages = await self._repository.list_messages(conversation_id=conversation_id)
        limit = config().agent.max_history_messages
        if limit > 0 and len(messages) > limit:
            return messages[-limit:]
        return messages

    async def append_turn(self, *, conversation_id: str, user_message: str, assistant_message: str) -> None:
        await self._repository.add_message(
            new_message(
                conversation_id=conversation_id,
                role=MessageRole.USER,
                content=sanitize_text(user_message),
            )
        )
        await self._repository.add_message(
            new_message(
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=sanitize_text(assistant_message),
            )
        )
