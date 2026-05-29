from pathlib import Path
from types import SimpleNamespace

import pytest

from app.application.dto.chat import ChatMessage, ChatRequest, ModelSelection
from app.infrastructure.model.model_router import ModelRouter
from app.infrastructure.model.provider_factory import ModelProviderFactory
from app.infrastructure.model.providers import anthropic
from app.infrastructure.model.providers.anthropic import AnthropicClient
from app.infrastructure.model.setup_service import ModelSetupService
from config.model import ActiveModelConfig, ModelConfig


class FakeModels:
    def __init__(self, owner):
        self.owner = owner

    async def list(self):
        self.owner.calls.append(("models.list", None))
        return SimpleNamespace(
            data=[
                SimpleNamespace(id="claude-sonnet-4-5", display_name="Claude Sonnet 4.5"),
                SimpleNamespace(id="claude-haiku-4-5", display_name=None),
            ]
        )


class FakeMessages:
    def __init__(self, owner):
        self.owner = owner

    async def create(self, **kwargs):
        self.owner.calls.append(("messages.create", kwargs))
        return SimpleNamespace(
            content=[
                SimpleNamespace(type="text", text="hello "),
                SimpleNamespace(type="text", text="there"),
            ],
            usage=SimpleNamespace(model_dump=lambda: {"input_tokens": 3, "output_tokens": 2}),
        )


class FakeAsyncAnthropic:
    instances = []

    def __init__(self, api_key, base_url=None):
        self.api_key = api_key
        self.base_url = base_url
        self.calls = []
        self.models = FakeModels(self)
        self.messages = FakeMessages(self)
        self.instances.append(self)


@pytest.fixture(autouse=True)
def fake_anthropic(monkeypatch):
    FakeAsyncAnthropic.instances = []
    monkeypatch.setattr(anthropic, "AsyncAnthropic", FakeAsyncAnthropic)


def test_anthropic_provider_fields():
    fields = ModelSetupService().provider_fields("anthropic")

    assert [field.name for field in fields] == ["api_key_ref", "base_url", "max_tokens"]
    assert fields[0].required is True
    assert fields[0].secret is True
    assert fields[1].placeholder == "https://api.anthropic.com"


@pytest.mark.asyncio
async def test_anthropic_validate_and_list_models():
    provider_config = {"api_key": "test-key", "base_url": "https://api.anthropic.com"}
    service = ModelSetupService()

    await service.validate_provider_config("anthropic", provider_config)
    models = await service.list_models("anthropic", provider_config)

    assert [model.id for model in models] == ["claude-sonnet-4-5", "claude-haiku-4-5"]
    assert models[0].name == "Claude Sonnet 4.5"
    assert models[1].name == "Claude Haiku 4.5"
    assert FakeAsyncAnthropic.instances[0].api_key == "test-key"
    assert FakeAsyncAnthropic.instances[0].base_url == "https://api.anthropic.com"
    assert FakeAsyncAnthropic.instances[0].calls == [("models.list", None)]


def test_save_provider_models_writes_selected_anthropic_models(tmp_path: Path):
    config_dir = tmp_path / "model-providers"
    active_config_file = tmp_path / "model_active.json"
    service = ModelSetupService(config_dir=config_dir, active_config_file=active_config_file)

    saved = service.save_provider_models(
        provider="anthropic",
        provider_config={"api_key": "test-key", "base_url": "https://api.anthropic.com", "max_tokens": "1024"},
        enabled_models={
            "claude-sonnet-4-5": {"temperature": 0.7, "max_tokens": 8192},
            "claude-haiku-4-5": {"temperature": 0.2, "max_tokens": 4096},
        },
        default_model="claude-haiku-4-5",
    )
    loaded = anthropic.load_provider_config(config_dir)
    active = ActiveModelConfig.load(active_config_file)

    assert saved.default_model == "claude-haiku-4-5"
    assert loaded.enabled_models == {
        "claude-sonnet-4-5": {"temperature": 0.7, "max_tokens": 8192},
        "claude-haiku-4-5": {"temperature": 0.2, "max_tokens": 4096},
    }
    assert loaded.config["api_key"] == "test-key"
    assert active.provider == "anthropic"
    assert active.model == "claude-haiku-4-5"


def test_factory_creates_anthropic_provider_from_saved_config(tmp_path: Path):
    config_dir = tmp_path / "model-providers"
    active_config_file = tmp_path / "model_active.json"
    ModelSetupService(config_dir=config_dir, active_config_file=active_config_file).save_provider_models(
        provider="anthropic",
        provider_config={"api_key": "test-key", "max_tokens": "1024"},
        enabled_models={"claude-sonnet-4-5": {"temperature": 0.6, "max_tokens": 1024}},
    )

    model_config = ModelConfig(_env_file=None, providers_config_dir=config_dir, active_config_file=active_config_file, temperature=0.2)
    provider = ModelProviderFactory(model_config).create("anthropic")

    assert isinstance(provider, AnthropicClient)
    assert provider.default_temperature == 0.2
    assert provider.max_tokens == 1024
    assert FakeAsyncAnthropic.instances[0].api_key == "test-key"


def test_model_router_uses_saved_anthropic_default(tmp_path: Path):
    config_dir = tmp_path / "model-providers"
    active_config_file = tmp_path / "model_active.json"
    ModelSetupService(config_dir=config_dir, active_config_file=active_config_file).save_provider_models(
        provider="anthropic",
        provider_config={"api_key": "test-key"},
        enabled_models={"claude-sonnet-4-5": {}, "claude-haiku-4-5": {}},
        default_model="claude-haiku-4-5",
    )
    model_config = ModelConfig(_env_file=None, providers_config_dir=config_dir, active_config_file=active_config_file)
    router = ModelRouter(ModelProviderFactory(model_config), model_config)

    assert router._resolve_model(None) == ModelSelection(provider="anthropic", name="claude-haiku-4-5")


@pytest.mark.asyncio
async def test_anthropic_complete_converts_system_and_messages(tmp_path: Path):
    config_dir = tmp_path / "model-providers"
    active_config_file = tmp_path / "model_active.json"
    ModelSetupService(config_dir=config_dir, active_config_file=active_config_file).save_provider_models(
        provider="anthropic",
        provider_config={"api_key": "test-key", "max_tokens": 512},
        enabled_models={"claude-sonnet-4-5": {"temperature": 0.1, "max_tokens": 256}},
    )
    model_config = ModelConfig(_env_file=None, providers_config_dir=config_dir, active_config_file=active_config_file, temperature=0.3)
    provider = ModelProviderFactory(model_config).create("anthropic")

    response = await provider.complete(
        ChatRequest(
            messages=[
                ChatMessage(role="system", content="You are concise."),
                ChatMessage(role="user", content="hello"),
                ChatMessage(role="assistant", content="hi"),
                ChatMessage(role="user", content="again"),
            ],
            model=ModelSelection(provider="anthropic", name="claude-sonnet-4-5"),
        )
    )

    assert response.content == "hello there"
    _, kwargs = FakeAsyncAnthropic.instances[0].calls[0]
    assert kwargs["model"] == "claude-sonnet-4-5"
    assert kwargs["system"] == "You are concise."
    assert kwargs["messages"] == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
        {"role": "user", "content": "again"},
    ]
    assert kwargs["temperature"] == 0.1
    assert kwargs["max_tokens"] == 256
    assert response.usage == {"input_tokens": 3, "output_tokens": 2}
