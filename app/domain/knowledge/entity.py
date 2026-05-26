from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class KnowledgeBase:
    id: str
    workspace_id: str
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class Document:
    id: str
    knowledge_base_id: str
    workspace_id: str
    title: str
    source: str | None
    status: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    id: str
    document_id: str
    knowledge_base_id: str
    workspace_id: str
    chunk_index: int
    content: str
    embedding: list[float]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class SearchHit:
    chunk_id: str
    document_id: str
    document_title: str
    content: str
    score: float
