from typing import Protocol

from app.application.dto.chat import ChatRequest, ChatResponse
from app.infrastructure.model.providers.openai_client import OpenAIClient
from config.llm import LlmConfig


class ChatProvider(Protocol):
    async def complete(self, request: ChatRequest) -> ChatResponse:
        ...


class ModelProviderFactory:
    def __init__(self, config: LlmConfig):
        self.config = config
        self._providers: dict[str, ChatProvider] = {}

    def create(self, provider: str) -> ChatProvider:
        if provider not in self.config.allowed_providers:
            raise ValueError(f"Unsupported model provider: {provider}")

        if provider not in self._providers:
            self._providers[provider] = self._build_provider(provider)

        return self._providers[provider]

    def _build_provider(self, provider: str) -> ChatProvider:
        if provider == "openai":
            api_key = self.config.openai_api_key or self.config.api_key
            if not api_key:
                raise ValueError("Missing OPENAI_API_KEY or LLM_API_KEY for provider: openai")

            return OpenAIClient(
                api_key=api_key,
                base_url=self.config.base_url,
                default_temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

        raise ValueError(f"Unsupported model provider: {provider}")
