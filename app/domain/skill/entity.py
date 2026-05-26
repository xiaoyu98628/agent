from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SkillInfo:
    name: str
    description: str
    category: str | None
    relative_path: str


@dataclass(frozen=True, slots=True)
class SkillContent:
    info: SkillInfo
    body: str
    raw: str
