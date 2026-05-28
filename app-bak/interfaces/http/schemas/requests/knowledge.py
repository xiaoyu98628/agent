from pydantic import BaseModel, Field


class CreateKnowledgeBaseRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class IngestDocumentRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str | None = Field(default=None, description="Raw text content")
    file_path: str | None = Field(default=None, description="Local file path to ingest")


class SearchKnowledgeRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=20)


class KnowledgeBaseListQuery(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
