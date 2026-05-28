from app.domain.exceptions import DomainError


class SkillError(DomainError):
    pass


class SkillNotFoundError(SkillError):
    pass
