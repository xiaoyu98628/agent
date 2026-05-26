from typing import Any

from langchain.chat_models import init_chat_model

from app.domain.llm.entity import LlmCredentials, ModelSelection
from app.domain.llm.exceptions import UnsupportedProviderError
from app.infrastructure.llm.credentials import resolve_credentials


def build_langchain_model(selection: ModelSelection) -> str | Any:
    """将 ModelSelection 解析为 LangChain model 字符串或 ChatModel 实例。"""
    credentials = resolve_credentials(selection.provider)
    provider = selection.provider.strip().lower()

    kwargs: dict[str, Any] = {}
    if selection.temperature is not None:
        kwargs["temperature"] = selection.temperature
    if selection.max_tokens is not None:
        kwargs["max_tokens"] = selection.max_tokens

    match provider:
        case "openrouter":
            return init_chat_model(
                f"openrouter:{selection.model}",
                api_key=credentials.api_key,
                **kwargs,
            )
        case "openai" | "zhipu":
            return _init_openai_compatible(selection.model, credentials, kwargs)
        case "anthropic":
            return init_chat_model(
                selection.model,
                model_provider="anthropic",
                api_key=credentials.api_key,
                **kwargs,
            )
        case "ollama":
            return init_chat_model(
                selection.model,
                model_provider="ollama",
                base_url=credentials.base_url,
                **kwargs,
            )
        case _:
            raise UnsupportedProviderError(f"不支持的 provider: {provider}")


def _init_openai_compatible(model: str, credentials: LlmCredentials, kwargs: dict[str, Any]) -> Any:
    init_kwargs = dict(kwargs)
    if credentials.base_url:
        init_kwargs["base_url"] = credentials.base_url
    if credentials.api_key:
        init_kwargs["api_key"] = credentials.api_key
    return init_chat_model(model, model_provider="openai", **init_kwargs)
