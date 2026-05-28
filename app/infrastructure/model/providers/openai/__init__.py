from pathlib import Path

from openai import AsyncOpenAI

from app.application.dto.chat import ChatRequest, ChatResponse
from app.application.dto.model_setup import ModelOption, ProviderConfigField
from config.model import ConfiguredProvider, ModelConfig, load_configured_provider, save_configured_provider

PROVIDER_NAME = "openai"
PROVIDER_CONFIG_FILENAME = "provider_config.json"


def provider_config_path(config_dir: Path | None = None) -> Path:
    if config_dir is not None:
        return config_dir.joinpath(PROVIDER_NAME, PROVIDER_CONFIG_FILENAME)
    return Path(__file__).resolve().parent.joinpath(PROVIDER_CONFIG_FILENAME)


def load_provider_config(config_dir: Path | None = None) -> ConfiguredProvider:
    return load_configured_provider(provider_config_path(config_dir))


def save_provider_config(provider: ConfiguredProvider, config_dir: Path | None = None) -> None:
    save_configured_provider(provider_config_path(config_dir), provider)


def create_provider(config: ModelConfig) -> OpenAIClient:
    return OpenAIClient.from_provider_config(
        provider_config=config.provider_config(PROVIDER_NAME),
        default_temperature=config.temperature,
    )


def config_fields() -> list[ProviderConfigField]:
    return [
        ProviderConfigField(
            name="api_key",
            label="API Key",
            required=True,
            secret=True,
            placeholder="sk-...",
        ),
        ProviderConfigField(
            name="base_url",
            label="Base URL",
            required=False,
            placeholder="https://api.openai.com/v1",
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
    client = _client_from_provider_config(provider_config)
    response = await client.models.list()
    return [ModelOption(id=model.id, name=model.id) for model in response.data]


def _client_from_provider_config(provider_config: dict) -> AsyncOpenAI:
    api_key = provider_config.get("api_key")
    if not api_key:
        raise ValueError("Missing api_key for provider: openai")

    return AsyncOpenAI(api_key=api_key, base_url=provider_config.get("base_url"))


class OpenAIClient:
    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        default_temperature: float | None = None,
        max_tokens: int | None = None,
    ):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.default_temperature = default_temperature
        self.max_tokens = max_tokens

    @classmethod
    def from_provider_config(cls, provider_config: dict, default_temperature: float | int | None = None) -> OpenAIClient:
        api_key = provider_config.get("api_key")
        if not api_key:
            raise ValueError("Missing api_key for provider: openai")

        max_tokens = provider_config.get("max_tokens")
        if isinstance(max_tokens, str) and max_tokens:
            max_tokens = int(max_tokens)

        return cls(
            api_key=api_key,
            base_url=provider_config.get("base_url"),
            default_temperature=default_temperature,
            max_tokens=max_tokens,
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

        temperature = request.temperature
        if temperature is None:
            temperature = self.default_temperature
        if temperature is not None:
            kwargs["temperature"] = temperature

        if self.max_tokens is not None:
            kwargs["max_tokens"] = self.max_tokens

        response = await self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        return ChatResponse(
            content=choice.message.content or "",
            model=request.model,
            usage=response.usage.model_dump() if response.usage else {},
            raw=response,
        )
