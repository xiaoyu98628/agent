from typing import Any

from langchain_openai import OpenAIEmbeddings

from app.infrastructure.llm.credentials import resolve_credentials
from config.config import config


def build_embeddings() -> OpenAIEmbeddings:
    """构建 Embedding 客户端（OpenAI 兼容，含智谱 Z.ai）。"""
    configure = config()
    provider = configure.rag.embedding_provider.strip().lower()
    credentials = resolve_credentials(provider)
    model = configure.rag.embedding_model.strip()

    if provider == "zhipu" and not model.startswith("embedding-"):
        model = "embedding-3"

    kwargs: dict[str, Any] = {"model": model}
    if credentials.api_key:
        kwargs["api_key"] = credentials.api_key
    if credentials.base_url:
        kwargs["base_url"] = credentials.base_url
    if provider == "zhipu" and model.startswith("embedding-3"):
        kwargs["dimensions"] = configure.rag.embedding_dimensions
    return OpenAIEmbeddings(**kwargs)
