import os
from pathlib import Path

from openai import AsyncOpenAI

from app.application.dto.chat import ChatRequest, ChatResponse
from app.application.dto.model_setup import ModelOption, ProviderConfigField
from app.infrastructure.model.catalog import ProviderCatalog, load_provider_catalog
from config.model import ConfiguredProvider, ModelConfig, load_configured_provider, save_configured_provider

DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
PROVIDER_NAME = "zai"
PROVIDER_CONFIG_FILENAME = "provider_config.json"
PROVIDER_CATALOG_FILENAME = "catalog.json"


def catalog_path() -> Path:
    return Path(__file__).resolve().parent.joinpath(PROVIDER_CATALOG_FILENAME)


def catalog() -> ProviderCatalog:
    return load_provider_catalog(catalog_path())


def provider_config_path(config_dir: Path | None = None) -> Path:
    if config_dir is not None:
        return config_dir.joinpath(PROVIDER_NAME, PROVIDER_CONFIG_FILENAME)
    return Path(__file__).resolve().parent.joinpath(PROVIDER_CONFIG_FILENAME)


def load_provider_config(config_dir: Path | None = None) -> ConfiguredProvider:
    return load_configured_provider(provider_config_path(config_dir))


def save_provider_config(provider: ConfiguredProvider, config_dir: Path | None = None) -> None:
    save_configured_provider(provider_config_path(config_dir), provider)


def create_provider(config: ModelConfig) -> ZAIClient:
    return ZAIClient.from_provider_setup(
        provider_setup=config.provider_setup(PROVIDER_NAME),
        default_temperature=config.temperature,
    )


def config_fields() -> list[ProviderConfigField]:
    return [
        ProviderConfigField(
            name="api_key_ref",
            label="API Key Env",
            required=True,
            secret=True,
            placeholder="ZAI_API_KEY",
        ),
        ProviderConfigField(
            name="base_url",
            label="Base URL",
            required=False,
            placeholder=DEFAULT_BASE_URL,
        ),
        ProviderConfigField(
            name="max_tokens",
            label="Max Tokens",
            required=False,
            placeholder="4096",
        ),
    ]


async def validate_config(provider_config: dict) -> None:
    client = _client_from_provider_config(provider_config)
    await client.models.list()


async def list_models(provider_config: dict) -> list[ModelOption]:
    return [model.to_option() for model in catalog().models]


def _client_from_provider_config(provider_config: dict) -> AsyncOpenAI:
    api_key = provider_config.get("api_key")
    if not api_key and provider_config.get("api_key_ref"):
        api_key = os.getenv(provider_config["api_key_ref"])
    if not api_key:
        raise ValueError("Missing api_key for provider: zai")

    return AsyncOpenAI(api_key=api_key, base_url=provider_config.get("base_url") or DEFAULT_BASE_URL)


class ZAIClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        default_temperature: float | None = None,
        max_tokens: int | None = None,
        enabled_models: dict[str, dict] | None = None,
    ):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.default_temperature = default_temperature
        self.max_tokens = max_tokens
        self.enabled_models = enabled_models or {}

    @classmethod
    def from_provider_setup(cls, provider_setup: ConfiguredProvider, default_temperature: float | int | None = None) -> ZAIClient:
        provider_config = provider_setup.config
        api_key = provider_config.get("api_key")
        if not api_key and provider_config.get("api_key_ref"):
            api_key = os.getenv(provider_config["api_key_ref"])
        if not api_key:
            raise ValueError("Missing api_key for provider: zai")

        max_tokens = provider_config.get("max_tokens")
        if isinstance(max_tokens, str) and max_tokens:
            max_tokens = int(max_tokens)

        return cls(
            api_key=api_key,
            base_url=provider_config.get("base_url") or DEFAULT_BASE_URL,
            default_temperature=default_temperature,
            max_tokens=max_tokens,
            enabled_models=provider_setup.enabled_models,
        )

    async def complete(self, request: ChatRequest) -> ChatResponse:
        if request.model is None:
            raise ValueError("Model selection is required")

        kwargs = {
            "model": request.model.name,
            "messages": [
                {"role": message.role, "content": message.content}
                for message in request.messages
            ],
        }

        model_config = self.enabled_models.get(request.model.name, {})
        temperature = request.temperature
        if temperature is None:
            temperature = model_config.get("temperature", self.default_temperature)
        if temperature is not None:
            kwargs["temperature"] = temperature

        max_tokens = model_config.get("max_tokens", self.max_tokens)
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        response = await self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        return ChatResponse(
            content=choice.message.content or "",
            model=request.model,
            usage=response.usage.model_dump() if response.usage else {},
            raw=response,
        )
