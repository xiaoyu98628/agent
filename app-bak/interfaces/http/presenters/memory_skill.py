from app.domain.memory.entity import MemoryEntry
from app.domain.skill.entity import SkillContent, SkillInfo
from app.interfaces.http.schemas.responses.memory_skill import (
    MemoryEntryResponse,
    SkillDetailResponse,
    SkillResponse,
)


def to_skill_response(skill: SkillInfo) -> SkillResponse:
    return SkillResponse(
        name=skill.name,
        description=skill.description,
        category=skill.category,
        relative_path=skill.relative_path,
    )


def to_skill_detail(content: SkillContent) -> SkillDetailResponse:
    return SkillDetailResponse(
        name=content.info.name,
        description=content.info.description,
        category=content.info.category,
        relative_path=content.info.relative_path,
        body=content.body,
    )


def to_memory_entry(entry: MemoryEntry) -> MemoryEntryResponse:
    return MemoryEntryResponse(
        id=entry.id,
        target=entry.target,
        content=entry.content,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )
