from app.domain.exceptions import DomainError


class KnowledgeError(DomainError):
    pass


class KnowledgeBaseNotFoundError(KnowledgeError):
    pass


class DocumentNotFoundError(KnowledgeError):
    pass
