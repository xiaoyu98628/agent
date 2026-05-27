from dataclasses import dataclass
from typing import Any

from langchain.chat_models import init_chat_model

from app.domain.llm.entity import LlmCredentials, ModelSelection, StaticModelEntry
from app.infrastructure.llm.providers.common import resolve_api_key_or_fallback, selection_init_kwargs, static_model, strip
from config.config import Config

_DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
_CREDENTIAL_HINT = "OPENROUTER_API_KEY 或 LLM_API_KEY"


@dataclass(frozen=True, slots=True)
class OpenRouterAdapter:
    name: str = "openrouter"
    static_models: tuple[StaticModelEntry, ...] = (
        static_model("openrouter", "anthropic/claude-sonnet-4-6", "Claude Sonnet 4.6 (OpenRouter)"),
        static_model("openrouter", "openai/gpt-4o", "GPT-4o (OpenRouter)"),
        static_model("openrouter", "google/gemini-2.5-flash", "Gemini 2.5 Flash (OpenRouter)"),
    )

    def resolve_credentials(self, configure: Config) -> LlmCredentials:
        api_key = resolve_api_key_or_fallback(
            configure,
            provider=self.name,
            provider_api_key=configure.llm.openrouter_api_key,
            hint=_CREDENTIAL_HINT,
        )
        base_url = strip(configure.llm.base_url) or _DEFAULT_OPENROUTER_BASE_URL
        return LlmCredentials(api_key=api_key, base_url=base_url)

    def build_chat_model(self, selection: ModelSelection, credentials: LlmCredentials) -> Any:
        return init_chat_model(
            f"openrouter:{selection.model}",
            api_key=credentials.api_key,
            **selection_init_kwargs(selection),
        )


adapter = OpenRouterAdapter()
