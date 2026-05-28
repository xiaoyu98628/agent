from dataclasses import replace

from app.application.dto.chat import ChatRequest, ChatResponse, ModelSelection
from app.infrastructure.model.provider_factory import ModelProviderFactory
from config.model import ModelConfig


class ModelRouter:
    def __init__(self, provider_factory: ModelProviderFactory, config: ModelConfig):
        self.provider_factory = provider_factory
        self.config = config

    async def complete(self, request: ChatRequest) -> ChatResponse:
        selection = self._resolve_model(request.model)
        provider = self.provider_factory.create(selection.provider)
        routed_request = replace(request, model=selection)
        return await provider.complete(routed_request)

    def _resolve_model(self, requested_model: ModelSelection | None) -> ModelSelection:
        if self.config.allow_override and requested_model is not None:
            return requested_model

        return ModelSelection(
            provider=self.config.default_provider(),
            name=self.config.default_model(),
        )
