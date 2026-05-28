from app.domain.knowledge.entity import Document, KnowledgeBase, SearchHit
from app.interfaces.http.schemas.responses.knowledge import (
    DocumentResponse,
    KnowledgeBaseResponse,
    SearchHitResponse,
)


def to_knowledge_base_response(kb: KnowledgeBase) -> KnowledgeBaseResponse:
    return KnowledgeBaseResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
    )


def to_document_response(document: Document) -> DocumentResponse:
    return DocumentResponse(
        id=document.id,
        knowledge_base_id=document.knowledge_base_id,
        title=document.title,
        source=document.source,
        status=document.status,
        chunk_count=document.chunk_count,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


def to_search_hit_response(hit: SearchHit) -> SearchHitResponse:
    return SearchHitResponse(
        chunk_id=hit.chunk_id,
        document_id=hit.document_id,
        document_title=hit.document_title,
        content=hit.content,
        score=hit.score,
    )
