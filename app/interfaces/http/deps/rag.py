from functools import lru_cache

from app.application.rag.service import RagService


@lru_cache
def get_rag_service() -> RagService:
    return RagService()
