import logging

from app.domain.conversation.exceptions import ConversationError, ConversationNotFoundError
from app.domain.exceptions import DomainError
from app.domain.knowledge.exceptions import DocumentNotFoundError, KnowledgeBaseNotFoundError, KnowledgeError
from app.domain.memory.exceptions import MemoryAmbiguousMatchError, MemoryEntryNotFoundError, MemoryError, MemoryLimitExceededError
from app.domain.skill.exceptions import SkillError, SkillNotFoundError
from app.domain.llm.exceptions import LlmError, MissingCredentialError, ModelNotAllowedError, UnsupportedProviderError
from app.interfaces.http.support.response.code.error_code import ErrorCode
from app.interfaces.http.support.response.json import JsonResponse

logger = logging.getLogger("app.channel.exception")


def _resolve_error_code(error: DomainError) -> tuple[ErrorCode, str | None]:
    if isinstance(error, (ConversationNotFoundError, KnowledgeBaseNotFoundError, DocumentNotFoundError, SkillNotFoundError, MemoryEntryNotFoundError)):
        return ErrorCode.NOT_FOUND_ERROR, str(error)
    if isinstance(error, (MissingCredentialError, ModelNotAllowedError, MemoryLimitExceededError, MemoryAmbiguousMatchError)):
        return ErrorCode.PARAMETER_ERROR, str(error)
    if isinstance(error, UnsupportedProviderError):
        return ErrorCode.PARAMETER_ERROR, str(error)
    if isinstance(error, (LlmError, ConversationError, KnowledgeError, SkillError, MemoryError)):
        return ErrorCode.REQUEST_ERROR, str(error)
    return ErrorCode.REQUEST_ERROR, str(error) or None


def to_error_response(error: DomainError) -> tuple[JsonResponse, int]:
    code, message = _resolve_error_code(error)
    logger.warning(
        "domain error",
        extra={"error_type": type(error).__name__, "detail": str(error), "error_code": code.full_code()},
    )
    response = JsonResponse.error(code=code, message=message)
    return response, code.status_code
