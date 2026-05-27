from app.domain.llm.entity import LlmCredentials
from app.infrastructure.llm.registry import get_adapter
from config.config import config


def resolve_credentials(provider: str) -> LlmCredentials:
    """从 pydantic-settings（.env）解析 BYOK 凭据。"""
    return get_adapter(provider).resolve_credentials(config())
