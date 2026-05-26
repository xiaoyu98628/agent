from datetime import datetime

from pydantic import BaseModel


class SkillResponse(BaseModel):
    name: str
    description: str
    category: str | None
    relative_path: str


class SkillDetailResponse(SkillResponse):
    body: str


class MemoryEntryResponse(BaseModel):
    id: str
    target: str
    content: str
    created_at: datetime
    updated_at: datetime


class MemorySnapshotResponse(BaseModel):
    memory: list[MemoryEntryResponse]
    user: list[MemoryEntryResponse]
