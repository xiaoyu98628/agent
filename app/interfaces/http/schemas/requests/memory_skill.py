from typing import Literal

from pydantic import BaseModel, Field


class UpsertSkillRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    description: str = Field(min_length=1, max_length=1024)
    body: str = Field(min_length=1)
    category: str | None = Field(default=None, max_length=64)


class CreateMemoryEntryRequest(BaseModel):
    target: Literal["memory", "user"] = Field(description="memory | user")
    content: str = Field(min_length=1)
