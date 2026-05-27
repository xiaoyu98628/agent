from dataclasses import dataclass
from typing import Any

from app.domain.llm.entity import LlmCredentials, ModelSelection, StaticModelEntry
from app.infrastructure.llm.providers.common import (
    build_openai_compatible_chat_model,
    resolve_api_key_or_fallback,
    static_model,
    strip,
)
from config.config import Config

_DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
_CREDENTIAL_HINT = "DEEPSEEK_API_KEY 或 LLM_API_KEY"


@dataclass(frozen=True, slots=True)
class DeepSeekAdapter:
    name: str = "deepseek"
    static_models: tuple[StaticModelEntry, ...] = (
        static_model("deepseek", "deepseek-chat", "DeepSeek Chat"),
        static_model("deepseek", "deepseek-reasoner", "DeepSeek Reasoner"),
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
        return build_openai_compatible_chat_model(selection.model, credentials, selection)


adapter = DeepSeekAdapter()
