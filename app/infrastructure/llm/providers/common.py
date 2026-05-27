from typing import Any

from app.domain.llm.entity import LlmCredentials, ModelSelection, StaticModelEntry
from app.domain.llm.exceptions import MissingCredentialError
from config.config import Config


def static_model(
    provider: str,
    model: str,
    label: str,
    *,
    supports_tools: bool = True,
) -> StaticModelEntry:
    return StaticModelEntry(provider=provider, model=model, label=label, supports_tools=supports_tools)


def strip(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def selection_init_kwargs(selection: ModelSelection) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    if selection.temperature is not None:
        kwargs["temperature"] = selection.temperature
    if selection.max_tokens is not None:
        kwargs["max_tokens"] = selection.max_tokens
    return kwargs


def resolve_api_key_or_fallback(
    configure: Config,
    *,
    provider: str,
    provider_api_key: str | None,
    hint: str,
) -> str:
    api_key = strip(provider_api_key) or strip(configure.llm.api_key)
    if not api_key:
        raise MissingCredentialError(f"未配置 {provider} 的 API Key，请在 .env 设置 {hint}")
    return api_key


def build_openai_compatible_chat_model(
    model: str,
    credentials: LlmCredentials,
    selection: ModelSelection,
) -> Any:
    """OpenAI 兼容 Chat API（openai / zhipu 等）。"""
    from langchain.chat_models import init_chat_model

    init_kwargs = selection_init_kwargs(selection)
    if credentials.base_url:
        init_kwargs["base_url"] = credentials.base_url
    if credentials.api_key:
        init_kwargs["api_key"] = credentials.api_key
    return init_chat_model(model, model_provider="openai", **init_kwargs)
