from typing import Any

from app.domain.llm.entity import ModelSelection
from app.infrastructure.llm.registry import get_adapter
from config.config import config


def build_langchain_model(selection: ModelSelection) -> Any:
    """将 ModelSelection 解析为 LangChain ChatModel 实例。"""
    adapter = get_adapter(selection.provider)
    credentials = adapter.resolve_credentials(config())
    return adapter.build_chat_model(selection, credentials)
