from typing import Literal

from app.domain.llm.entity import StaticModelEntry
from app.infrastructure.llm.registry import list_static_model_entries
from config.config import config


def list_model_options() -> dict[str, Literal["static"] | list[str] | list[StaticModelEntry] | dict[str, str]]:
    """返回 Phase 1 静态模型目录。"""
    configure = config()
    entries = list_static_model_entries()
    providers = sorted({entry.provider for entry in entries})
    allowed = [p for p in providers if p in configure.llm.allowed_providers]
    filtered = [entry for entry in entries if entry.provider in allowed]
    return {
        "catalog_source": configure.llm.catalog_source,
        "providers": allowed,
        "models": filtered,
        "default": {
            "provider": configure.llm.provider,
            "model": configure.llm.model,
        },
    }
