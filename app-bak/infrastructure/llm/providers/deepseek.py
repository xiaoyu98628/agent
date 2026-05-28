from dataclasses import dataclass
from typing import Any

from app.domain.llm.entity import LlmCredentials, ModelSelection, StaticModelEntry
from app.infrastructure.llm.providers.common import (
    build_openai_compatible_chat_model,
    resolve_api_key_or_fallback,
    selection_init_kwargs,
    static_model,
    strip,
)
from config.config import Config

_DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
_CREDENTIAL_HINT = "DEEPSEEK_API_KEY 或 LLM_API_KEY"
_REASONER_MODEL = "deepseek-reasoner"


@dataclass(frozen=True, slots=True)
class DeepSeekAdapter:
    name: str = "deepseek"
    static_models: tuple[StaticModelEntry, ...] = (
        static_model("deepseek", "deepseek-chat", "DeepSeek Chat"),
        static_model("deepseek", _REASONER_MODEL, "DeepSeek Reasoner", supports_tools=False),
    )

    def resolve_credentials(self, configure: Config) -> LlmCredentials:
        api_key = resolve_api_key_or_fallback(
            configure,
            provider=self.name,
            provider_api_key=configure.llm.deepseek_api_key,
            hint=_CREDENTIAL_HINT,
        )
        base_url = strip(configure.llm.base_url)
        if not base_url:
            base_url = strip(configure.llm.deepseek_base_url) or _DEFAULT_DEEPSEEK_BASE_URL
        return LlmCredentials(api_key=api_key, base_url=base_url)

    def build_chat_model(self, selection: ModelSelection, credentials: LlmCredentials) -> Any:
        if selection.model == _REASONER_MODEL:
            return _build_reasoner_chat_model(selection, credentials)
        return build_openai_compatible_chat_model(selection.model, credentials, selection)


def _build_reasoner_chat_model(selection: ModelSelection, credentials: LlmCredentials) -> Any:
    from langchain.chat_models import init_chat_model

    init_kwargs = selection_init_kwargs(selection)
    init_kwargs.pop("temperature", None)
    if credentials.base_url:
        init_kwargs["base_url"] = credentials.base_url
    if credentials.api_key:
        init_kwargs["api_key"] = credentials.api_key
    return init_chat_model(selection.model, model_provider="openai", **init_kwargs)


adapter = DeepSeekAdapter()
