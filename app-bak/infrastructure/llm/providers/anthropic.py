from dataclasses import dataclass
from typing import Any

from langchain.chat_models import init_chat_model

from app.domain.llm.entity import LlmCredentials, ModelSelection, StaticModelEntry
from app.infrastructure.llm.providers.common import resolve_api_key_or_fallback, selection_init_kwargs, static_model, strip
from config.config import Config

_CREDENTIAL_HINT = "ANTHROPIC_API_KEY 或 LLM_API_KEY"


@dataclass(frozen=True, slots=True)
class AnthropicAdapter:
    name: str = "anthropic"
    static_models: tuple[StaticModelEntry, ...] = (static_model("anthropic", "claude-sonnet-4-6", "Claude Sonnet 4.6 (Anthropic)"),)

    def resolve_credentials(self, configure: Config) -> LlmCredentials:
        api_key = resolve_api_key_or_fallback(
            configure,
            provider=self.name,
            provider_api_key=configure.llm.anthropic_api_key,
            hint=_CREDENTIAL_HINT,
        )
        return LlmCredentials(api_key=api_key, base_url=strip(configure.llm.base_url))

    def build_chat_model(self, selection: ModelSelection, credentials: LlmCredentials) -> Any:
        return init_chat_model(
            selection.model,
            model_provider="anthropic",
            api_key=credentials.api_key,
            **selection_init_kwargs(selection),
        )


adapter = AnthropicAdapter()
