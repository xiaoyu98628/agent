from langchain_core.tools import BaseTool, tool

from app.infrastructure.vector.sqlite_search import sync_search_formatted
from config.config import config


def build_rag_tools() -> list[BaseTool]:
    configure = config()
    if not configure.rag.enabled:
        return []

    @tool
    def search_knowledge(query: str, knowledge_base_id: str | None = None) -> str:
        """Search indexed knowledge base documents for passages relevant to the query."""
        return sync_search_formatted(query=query, knowledge_base_id=knowledge_base_id)

    return [search_knowledge]
