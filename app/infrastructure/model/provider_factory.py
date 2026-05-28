from importlib import import_module
from typing import Protocol

from app.application.dto.chat import ChatRequest, ChatResponse
from config.model import ModelConfig


class ChatProvider(Protocol):
    async def complete(self, request: ChatRequest) -> ChatResponse:
        ...


class ModelProviderFactory:
    def __init__(self, config: ModelConfig):
        self.config = config
        self._providers: dict[str, ChatProvider] = {}

    def create(self, provider: str) -> ChatProvider:
        if provider not in self._providers:
            self._providers[provider] = self._build_provider(provider)

        return self._providers[provider]

    def _build_provider(self, provider: str) -> ChatProvider:
        if not provider.isidentifier():
            raise ValueError(f"Unsupported model provider: {provider}")

        module_name = f"app.infrastructure.model.providers.{provider}"
        try:
            module = import_module(module_name)
        except ModuleNotFoundError as exc:
            if exc.name == module_name:
                raise ValueError(f"Unsupported model provider: {provider}") from exc
            raise

        create_provider = getattr(module, "create_provider", None)
        if create_provider is None:
            raise ValueError(f"Unsupported model provider: {provider}")

        return create_provider(self.config)
