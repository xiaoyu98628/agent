import json
from importlib import import_module
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.settings import BASE_SETTINGS_CONFIG
from paths import BASE_DIR


class ConfiguredProvider(BaseModel):
    config: dict[str, Any] = Field(default_factory=dict)
    selected_models: list[str] = Field(default_factory=list)
    default_model: str | None = None

    @field_validator("selected_models")
    @classmethod
    def validate_selected_models(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(model for model in value if model))


def load_configured_provider(path: Path) -> ConfiguredProvider:
    if not path.exists():
        return ConfiguredProvider()

    with path.open("r", encoding="utf-8") as file:
        return ConfiguredProvider.model_validate(json.load(file))


def save_configured_provider(path: Path, provider: ConfiguredProvider) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(provider.model_dump(mode="json", exclude_none=True), file, ensure_ascii=False, indent=2)
        file.write("\n")


class ModelConfig(BaseSettings):
    model_config = SettingsConfigDict(
        **BASE_SETTINGS_CONFIG,
        env_prefix="MODEL_",
    )

    provider: str | None = Field(default=None, description="运行时覆盖的模型提供者")
    name: str | None = Field(default=None, description="运行时覆盖的模型名称")
    temperature: float | int = Field(default=0.7, ge=0, le=1, description="模型温度")
    allow_override: bool = Field(default=True, description="是否允许请求覆盖模型选择")
    providers_config_dir: Path | None = Field(default=None, description="模型供应商配置目录；为空时使用各 provider 包内配置")

    @field_validator("providers_config_dir")
    @classmethod
    def resolve_providers_config_dir(cls, value: Path | None) -> Path | None:
        if value is None or value.is_absolute():
            return value
        return BASE_DIR.joinpath(value)

    def default_provider(self) -> str:
        provider = self.provider or self._active_provider_from_provider_configs()
        if not provider:
            raise ValueError("Missing model provider. Configure a provider package or set MODEL_PROVIDER.")
        return provider

    def default_model(self) -> str:
        if self.name:
            return self.name

        provider = self.default_provider()
        model = self.provider_setup(provider).default_model
        if not model:
            raise ValueError(f"Missing model name. Configure provider {provider} or set MODEL_NAME.")
        return model

    def provider_config(self, provider: str) -> dict[str, Any]:
        return self.provider_setup(provider).config

    def provider_setup(self, provider: str) -> ConfiguredProvider:
        module = self._provider_module(provider)
        load_provider_config = getattr(module, "load_provider_config", None)
        if load_provider_config is None:
            raise ValueError(f"Model provider does not support provider config: {provider}")
        return load_provider_config(self.providers_config_dir)

    def _active_provider_from_provider_configs(self) -> str | None:
        for provider in ("openai", "zai", "anthropic"):
            try:
                configured_provider = self.provider_setup(provider)
            except ValueError:
                continue
            if configured_provider.default_model:
                return provider
        return None

    def _provider_module(self, provider: str):
        if not provider.isidentifier():
            raise ValueError(f"Unsupported model provider: {provider}")
        return import_module(f"app.infrastructure.model.providers.{provider}")
