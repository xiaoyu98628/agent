import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Literal

from app.application.agent.runner import AgentRunner
from app.application.conversation.service import ConversationService
from app.application.support.text import sanitize_text
from app.domain.conversation.entity import Conversation
from app.domain.llm.entity import ModelSelection
from app.infrastructure.storage.sqlite.conversation_repository import SqliteConversationRepository


@dataclass(frozen=True, slots=True)
class ChatMessageInput:
    role: str
    content: str


@dataclass(frozen=True, slots=True)
class ChatResult:
    reply: str
    model: ModelSelection
    conversation_id: str | None = None


ChatStreamEventType = Literal["start", "delta", "done", "error"]


@dataclass(frozen=True, slots=True)
class ChatStreamEvent:
    event: ChatStreamEventType
    data: dict[str, Any]


class ChatService:
    """对话用例门面。"""

    def __init__(
        self,
        runner: AgentRunner | None = None,
        conversation_service: ConversationService | None = None,
    ) -> None:
        self._runner = runner or AgentRunner()
        repository = SqliteConversationRepository()
        self._conversations = conversation_service or ConversationService(repository)

    async def send_message(
        self,
        *,
        message: str,
        conversation_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        history: list[ChatMessageInput] | None = None,
    ) -> ChatResult:
        conversation, selection, history_payload = await self._prepare_turn(
            message=message,
            conversation_id=conversation_id,
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            history=history,
        )
        result = await asyncio.to_thread(
            self._runner.run,
            user_message=message,
            selection=selection,
            history=history_payload,
        )
        await self._conversations.append_turn(
            conversation_id=conversation.id,
            user_message=message,
            assistant_message=result.reply,
        )
        return ChatResult(reply=result.reply, model=selection, conversation_id=conversation.id)

    async def stream_message(
        self,
        *,
        message: str,
        conversation_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        history: list[ChatMessageInput] | None = None,
    ) -> AsyncIterator[ChatStreamEvent]:
        conversation, selection, history_payload = await self._prepare_turn(
            message=message,
            conversation_id=conversation_id,
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            history=history,
        )

        start_data = _model_payload(selection)
        start_data["conversation_id"] = conversation.id
        yield ChatStreamEvent(event="start", data=start_data)

        parts: list[str] = []
        async for delta in self._runner.stream(
            user_message=message,
            selection=selection,
            history=history_payload,
        ):
            parts.append(delta)
            yield ChatStreamEvent(event="delta", data={"content": delta})

        reply = sanitize_text("".join(parts))
        if not reply.strip():
            result = await asyncio.to_thread(
                self._runner.run,
                user_message=message,
                selection=selection,
                history=history_payload,
            )
            reply = sanitize_text(result.reply)

        await self._conversations.append_turn(
            conversation_id=conversation.id,
            user_message=message,
            assistant_message=reply,
        )
        yield ChatStreamEvent(
            event="done",
            data={"reply": reply, "model": _model_payload(selection), "conversation_id": conversation.id},
        )

    async def _prepare_turn(
        self,
        *,
        message: str,
        conversation_id: str | None,
        provider: str | None,
        model: str | None,
        temperature: float | None,
        max_tokens: int | None,
        history: list[ChatMessageInput] | None,
    ) -> tuple[Conversation, ModelSelection, list[dict[str, str]]]:
        existing = None
        if conversation_id:
            existing = await self._conversations.get(conversation_id)

        conversation = await self._conversations.ensure_conversation(
            conversation_id=conversation_id,
            user_message=message,
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        selection = await self._conversations.resolve_selection_for_chat(
            conversation=existing or conversation,
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if conversation_id:
            stored = await self._conversations.load_history(conversation.id)
            history_payload = [{"role": item.role, "content": sanitize_text(item.content)} for item in stored]
        else:
            history_payload = [{"role": item.role, "content": sanitize_text(item.content)} for item in (history or [])]

        return conversation, selection, history_payload


def _model_payload(selection: ModelSelection) -> dict[str, Any]:
    return {
        "provider": selection.provider,
        "model": selection.model,
        "temperature": selection.temperature,
        "max_tokens": selection.max_tokens,
    }
