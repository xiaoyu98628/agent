from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any

from app.application.dto.model_setup import ModelOption, ProviderConfigField
from config.model import ActiveModelConfig, ConfiguredProvider
from paths import MODEL_ACTIVE_CONFIG_FILE


class ModelSetupService:
    def __init__(self, config_dir: Path | None = None, active_config_file: Path = MODEL_ACTIVE_CONFIG_FILE):
        self.config_dir = config_dir
        self.active_config_file = active_config_file

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
        enabled_models: dict[str, dict[str, Any]],
        default_model: str | None = None,
    ) -> ConfiguredProvider:
        if not enabled_models:
            raise ValueError("At least one model must be selected.")

        resolved_default_model = default_model or next(iter(enabled_models))
        if resolved_default_model not in enabled_models:
            raise ValueError("Default model must be one of enabled models.")

        configured_provider = ConfiguredProvider(
            config=provider_config,
            enabled_models=enabled_models,
            default_model=resolved_default_model,
        )
        module = self._provider_module(provider)
        save_provider_config = getattr(module, "save_provider_config", None)
        if save_provider_config is None:
            raise ValueError(f"Model provider does not support provider config: {provider}")
        save_provider_config(configured_provider, self.config_dir)
        ActiveModelConfig(provider=provider, model=resolved_default_model).save(self.active_config_file)
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
