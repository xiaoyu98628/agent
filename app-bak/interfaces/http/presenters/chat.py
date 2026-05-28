from app.domain.conversation.entity import Conversation, Message
from app.domain.llm.entity import ModelSelection
from app.interfaces.http.schemas.responses.chat import ChatResponse, ModelSelectionResponse
from app.interfaces.http.schemas.responses.conversation import ConversationDetailResponse, ConversationResponse, MessageResponse


def to_model_selection_response(selection: ModelSelection) -> ModelSelectionResponse:
    return ModelSelectionResponse(
        provider=selection.provider,
        model=selection.model,
        temperature=selection.temperature,
        max_tokens=selection.max_tokens,
    )


def to_chat_response(*, reply: str, model: ModelSelection, conversation_id: str | None = None) -> ChatResponse:
    return ChatResponse(
        reply=reply,
        conversation_id=conversation_id,
        model=to_model_selection_response(model),
    )


def to_conversation_response(conversation: Conversation) -> ConversationResponse:
    return ConversationResponse(
        id=conversation.id,
        workspace_id=conversation.workspace_id,
        title=conversation.title,
        model=to_model_selection_response(
            ModelSelection(
                provider=conversation.model_provider,
                model=conversation.model_name,
                temperature=conversation.temperature,
                max_tokens=conversation.max_tokens,
            )
        ),
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def to_message_response(message: Message) -> MessageResponse:
    return MessageResponse(
        id=message.id,
        role=message.role,
        content=message.content,
        created_at=message.created_at,
    )


def to_conversation_detail(conversation: Conversation, messages: list[Message]) -> ConversationDetailResponse:
    return ConversationDetailResponse(
        **to_conversation_response(conversation).model_dump(),
        messages=[to_message_response(item) for item in messages],
    )
