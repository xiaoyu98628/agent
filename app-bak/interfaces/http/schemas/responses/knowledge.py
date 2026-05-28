from datetime import datetime

from pydantic import BaseModel, Field


class KnowledgeBaseResponse(BaseModel):
    id: str
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class DocumentResponse(BaseModel):
    id: str
    knowledge_base_id: str
    title: str
    source: str | None
    status: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime


class SearchHitResponse(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    content: str
    score: float


class SearchKnowledgeResponse(BaseModel):
    query: str
    hits: list[SearchHitResponse] = Field(default_factory=list)
