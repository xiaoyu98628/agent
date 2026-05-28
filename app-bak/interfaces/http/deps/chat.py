from functools import lru_cache

from app.application.chat.service import ChatService
from app.application.conversation.service import ConversationService
from app.interfaces.http.deps.conversation import get_conversation_service


@lru_cache
def get_chat_service() -> ChatService:
    return ChatService(conversation_service=get_conversation_service())
