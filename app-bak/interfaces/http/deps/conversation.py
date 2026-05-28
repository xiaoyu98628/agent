from functools import lru_cache

from app.application.conversation.service import ConversationService
from app.infrastructure.storage.sqlite.conversation_repository import SqliteConversationRepository


@lru_cache
def get_conversation_service() -> ConversationService:
    return ConversationService(SqliteConversationRepository())
