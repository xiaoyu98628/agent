from pathlib import Path

from anthropic import AsyncAnthropic

from app.application.dto.chat import ChatMessage, ChatRequest, ChatResponse
from app.application.dto.model_setup import ModelOption, ProviderConfigField
from config.model import ConfiguredProvider, ModelConfig, load_configured_provider, save_configured_provider

DEFAULT_MAX_TOKENS = 4096
PROVIDER_NAME = "anthropic"
PROVIDER_CONFIG_FILENAME = "provider_config.json"


def provider_config_path(config_dir: Path | None = None) -> Path:
    if config_dir is not None:
        return config_dir.joinpath(PROVIDER_NAME, PROVIDER_CONFIG_FILENAME)
    return Path(__file__).resolve().parent.joinpath(PROVIDER_CONFIG_FILENAME)


def load_provider_config(config_dir: Path | None = None) -> ConfiguredProvider:
    return load_configured_provider(provider_config_path(config_dir))


def save_provider_config(provider: ConfiguredProvider, config_dir: Path | None = None) -> None:
    save_configured_provider(provider_config_path(config_dir), provider)


def create_provider(config: ModelConfig) -> AnthropicClient:
    return AnthropicClient.from_provider_config(
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
            placeholder="sk-ant-...",
        ),
        ProviderConfigField(
            name="base_url",
            label="Base URL",
            required=False,
            placeholder="https://api.anthropic.com",
        ),
        ProviderConfigField(
            name="max_tokens",
            label="Max Tokens",
            required=False,
            placeholder=str(DEFAULT_MAX_TOKENS),
        ),
    ]


async def validate_config(provider_config: dict) -> None:
    client = _client_from_provider_config(provider_config)
    await client.models.list()


async def list_models(provider_config: dict) -> list[ModelOption]:
    client = _client_from_provider_config(provider_config)
    response = await client.models.list()
    return [ModelOption(id=model.id, name=getattr(model, "display_name", None) or model.id) for model in response.data]


def _client_from_provider_config(provider_config: dict) -> AsyncAnthropic:
    api_key = provider_config.get("api_key")
    if not api_key:
        raise ValueError("Missing api_key for provider: anthropic")

    return AsyncAnthropic(api_key=api_key, base_url=provider_config.get("base_url"))


class AnthropicClient:
    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        default_temperature: float | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ):
        self.client = AsyncAnthropic(api_key=api_key, base_url=base_url)
        self.default_temperature = default_temperature
        self.max_tokens = max_tokens

    @classmethod
    def from_provider_config(cls, provider_config: dict, default_temperature: float | int | None = None) -> AnthropicClient:
        api_key = provider_config.get("api_key")
        if not api_key:
            raise ValueError("Missing api_key for provider: anthropic")

        max_tokens = provider_config.get("max_tokens") or DEFAULT_MAX_TOKENS
        if isinstance(max_tokens, str):
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

        system, messages = self._convert_messages(request.messages)
        kwargs = {
            "model": request.model.name,
            "messages": messages,
            "max_tokens": self.max_tokens,
        }

        if system:
            kwargs["system"] = system

        temperature = request.temperature
        if temperature is None:
            temperature = self.default_temperature
        if temperature is not None:
            kwargs["temperature"] = temperature

        response = await self.client.messages.create(**kwargs)

        return ChatResponse(
            content=self._response_text(response),
            model=request.model,
            usage=response.usage.model_dump() if getattr(response, "usage", None) else {},
            raw=response,
        )

    def _convert_messages(self, messages: list[ChatMessage]) -> tuple[str | None, list[dict[str, str]]]:
        system_messages = [message.content for message in messages if message.role == "system"]
        chat_messages = [
            {"role": message.role, "content": message.content}
            for message in messages
            if message.role in {"user", "assistant"}
        ]
        return "\n\n".join(system_messages) or None, chat_messages

    def _response_text(self, response) -> str:
        parts = []
        for block in getattr(response, "content", []):
            text = getattr(block, "text", None)
            if text:
                parts.append(text)
        return "".join(parts)
