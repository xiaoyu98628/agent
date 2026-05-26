from app.domain.exceptions import DomainError


class ConversationError(DomainError):
    """会话领域错误基类。"""


class ConversationNotFoundError(ConversationError):
    """会话不存在。"""
