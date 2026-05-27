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

_CREDENTIAL_HINT = "OPENAI_API_KEY 或 LLM_API_KEY"


@dataclass(frozen=True, slots=True)
class OpenAiAdapter:
    name: str = "openai"
    static_models: tuple[StaticModelEntry, ...] = (
        static_model("openai", "gpt-4o", "GPT-4o (OpenAI)"),
        static_model("openai", "gpt-4o-mini", "GPT-4o Mini (OpenAI)"),
    )

    def resolve_credentials(self, configure: Config) -> LlmCredentials:
        api_key = resolve_api_key_or_fallback(
            configure,
            provider=self.name,
            provider_api_key=configure.llm.openai_api_key,
            hint=_CREDENTIAL_HINT,
        )
        return LlmCredentials(api_key=api_key, base_url=strip(configure.llm.base_url))

    def build_chat_model(self, selection: ModelSelection, credentials: LlmCredentials) -> Any:
        return build_openai_compatible_chat_model(selection.model, credentials, selection)


adapter = OpenAiAdapter()
