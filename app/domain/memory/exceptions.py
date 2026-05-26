from app.domain.exceptions import DomainError


class MemoryError(DomainError):
    pass


class MemoryEntryNotFoundError(MemoryError):
    pass


class MemoryLimitExceededError(MemoryError):
    pass


class MemoryAmbiguousMatchError(MemoryError):
    pass
