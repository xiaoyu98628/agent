from dataclasses import dataclass
from typing import Any

from langchain.chat_models import init_chat_model

from app.domain.llm.entity import LlmCredentials, ModelSelection, StaticModelEntry
from app.infrastructure.llm.providers.common import selection_init_kwargs, static_model, strip
from config.config import Config

_DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"


@dataclass(frozen=True, slots=True)
class OllamaAdapter:
    name: str = "ollama"
    static_models: tuple[StaticModelEntry, ...] = (static_model("ollama", "llama3.2", "Llama 3.2 (Ollama local)"),)

    def resolve_credentials(self, configure: Config) -> LlmCredentials:
        return LlmCredentials(
            api_key=None,
            base_url=strip(configure.llm.ollama_base_url) or _DEFAULT_OLLAMA_BASE_URL,
        )

    def build_chat_model(self, selection: ModelSelection, credentials: LlmCredentials) -> Any:
        return init_chat_model(
            selection.model,
            model_provider="ollama",
            base_url=credentials.base_url,
            **selection_init_kwargs(selection),
        )


adapter = OllamaAdapter()
