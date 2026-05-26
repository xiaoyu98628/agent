from functools import lru_cache

from app.application.memory.service import MemoryService
from app.application.skill.service import SkillService


@lru_cache
def get_memory_service() -> MemoryService:
    return MemoryService()


@lru_cache
def get_skill_service() -> SkillService:
    return SkillService()
