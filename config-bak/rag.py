from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.settings import BASE_SETTINGS_CONFIG


class RagConfig(BaseSettings):
    """RAG 检索与向量库配置。"""

    model_config = SettingsConfigDict(
        **BASE_SETTINGS_CONFIG,
        env_prefix="RAG_",
    )

    enabled: bool = Field(default=True, description="是否启用 RAG 与 search_knowledge 工具")
    chunk_size: int = Field(default=512, description="文档分块大小（字符）")
    chunk_overlap: int = Field(default=50, description="分块重叠（字符）")
    top_k: int = Field(default=5, description="检索返回条数")
    vector_backend: Literal["sqlite", "pgvector", "qdrant"] = Field(default="sqlite", description="向量存储后端")
    embedding_provider: str = Field(default="zhipu", description="Embedding 凭据 provider（与 LLM BYOK 一致）")
    embedding_model: str = Field(default="embedding-3", description="Embedding 模型 ID")
    embedding_dimensions: int = Field(default=1024, ge=256, le=2048, description="embedding-3 输出维度")
    default_knowledge_base_name: str = Field(default="default", description="默认知识库名称")
