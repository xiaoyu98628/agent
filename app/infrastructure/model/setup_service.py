from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any

from app.application.dto.model_setup import ModelOption, ProviderConfigField
from config.model import ConfiguredProvider


class ModelSetupService:
    def __init__(self, config_dir: Path | None = None):
        self.config_dir = config_dir

    def provider_fields(self, provider: str) -> list[ProviderConfigField]:
        module = self._provider_module(provider)
        fields = getattr(module, "config_fields", None)
        if fields is None:
            raise ValueError(f"Model provider does not support setup: {provider}")
        return fields()

    async def validate_provider_config(self, provider: str, provider_config: dict[str, Any]) -> None:
        module = self._provider_module(provider)
        validate_config = getattr(module, "validate_config", None)
        if validate_config is None:
            raise ValueError(f"Model provider does not support validation: {provider}")
        await validate_config(provider_config)

    async def list_models(self, provider: str, provider_config: dict[str, Any]) -> list[ModelOption]:
        module = self._provider_module(provider)
        list_models = getattr(module, "list_models", None)
        if list_models is None:
            raise ValueError(f"Model provider does not support model listing: {provider}")
        return await list_models(provider_config)

    def save_provider_models(
        self,
        provider: str,
        provider_config: dict[str, Any],
        selected_models: list[str],
        default_model: str | None = None,
    ) -> ConfiguredProvider:
        if not selected_models:
            raise ValueError("At least one model must be selected.")

        unique_models = list(dict.fromkeys(selected_models))
        resolved_default_model = default_model or unique_models[0]
        if resolved_default_model not in unique_models:
            raise ValueError("Default model must be one of selected models.")

        configured_provider = ConfiguredProvider(
            config=provider_config,
            selected_models=unique_models,
            default_model=resolved_default_model,
        )
        module = self._provider_module(provider)
        save_provider_config = getattr(module, "save_provider_config", None)
        if save_provider_config is None:
            raise ValueError(f"Model provider does not support provider config: {provider}")
        save_provider_config(configured_provider, self.config_dir)
        return configured_provider

    def _provider_module(self, provider: str) -> ModuleType:
        if not provider.isidentifier():
            raise ValueError(f"Unsupported model provider: {provider}")

        module_name = f"app.infrastructure.model.providers.{provider}"
        try:
            return import_module(module_name)
        except ModuleNotFoundError as exc:
            if exc.name == module_name:
                raise ValueError(f"Unsupported model provider: {provider}") from exc
            raise
