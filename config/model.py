import json
from importlib import import_module
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.settings import BASE_SETTINGS_CONFIG
from paths import BASE_DIR, MODEL_ACTIVE_CONFIG_FILE


class ConfiguredProvider(BaseModel):
    config: dict[str, Any] = Field(default_factory=dict)
    enabled_models: dict[str, dict[str, Any]] = Field(default_factory=dict)
    default_model: str | None = None

    @field_validator("enabled_models")
    @classmethod
    def validate_enabled_models(cls, value: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        return {model_id: model_config for model_id, model_config in value.items() if model_id}


class ActiveModelConfig(BaseModel):
    provider: str | None = None
    model: str | None = None

    @classmethod
    def load(cls, path: Path = MODEL_ACTIVE_CONFIG_FILE) -> ActiveModelConfig:
        if not path.exists():
            return cls()

        with path.open("r", encoding="utf-8") as file:
            return cls.model_validate(json.load(file))

    def save(self, path: Path = MODEL_ACTIVE_CONFIG_FILE) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(self.model_dump(mode="json", exclude_none=True), file, ensure_ascii=False, indent=2)
            file.write("\n")


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
    active_config_file: Path = Field(default=MODEL_ACTIVE_CONFIG_FILE, description="当前默认模型配置文件")

    @field_validator("providers_config_dir")
    @classmethod
    def resolve_providers_config_dir(cls, value: Path | None) -> Path | None:
        if value is None or value.is_absolute():
            return value
        return BASE_DIR.joinpath(value)

    @field_validator("active_config_file")
    @classmethod
    def resolve_active_config_file(cls, value: Path) -> Path:
        if value.is_absolute():
            return value
        return BASE_DIR.joinpath(value)

    def default_provider(self) -> str:
        active_model = ActiveModelConfig.load(self.active_config_file)
        provider = self.provider or active_model.provider
        if not provider:
            raise ValueError(f"Missing model provider. Configure {self.active_config_file} or set MODEL_PROVIDER.")
        return provider

    def default_model(self) -> str:
        if self.name:
            return self.name

        active_model = ActiveModelConfig.load(self.active_config_file)
        model = active_model.model
        if not model:
            raise ValueError(f"Missing model name. Configure {self.active_config_file} or set MODEL_NAME.")
        return model

    def provider_config(self, provider: str) -> dict[str, Any]:
        return self.provider_setup(provider).config

    def provider_setup(self, provider: str) -> ConfiguredProvider:
        module = self._provider_module(provider)
        load_provider_config = getattr(module, "load_provider_config", None)
        if load_provider_config is None:
            raise ValueError(f"Model provider does not support provider config: {provider}")
        return load_provider_config(self.providers_config_dir)

    def _provider_module(self, provider: str):
        if not provider.isidentifier():
            raise ValueError(f"Unsupported model provider: {provider}")
        return import_module(f"app.infrastructure.model.providers.{provider}")
