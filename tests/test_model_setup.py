from pathlib import Path
from types import SimpleNamespace

import pytest

from app.application.dto.chat import ChatMessage, ChatRequest, ModelSelection
from app.infrastructure.model.model_router import ModelRouter
from app.infrastructure.model.provider_factory import ModelProviderFactory
from app.infrastructure.model.providers import zai
from app.infrastructure.model.providers.zai import DEFAULT_BASE_URL, ZAIClient
from app.infrastructure.model.setup_service import ModelSetupService
from config.model import ActiveModelConfig, ModelConfig


class FakeModels:
    def __init__(self, owner):
        self.owner = owner

    async def list(self):
        self.owner.calls.append(("models.list", None))
        return SimpleNamespace(
            data=[
                SimpleNamespace(id="glm-4.6"),
                SimpleNamespace(id="glm-4.5"),
            ]
        )


class FakeCompletions:
    def __init__(self, owner):
        self.owner = owner

    async def create(self, **kwargs):
        self.owner.calls.append(("chat.completions.create", kwargs))
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))],
            usage=SimpleNamespace(model_dump=lambda: {"total_tokens": 1}),
        )


class FakeChat:
    def __init__(self, owner):
        self.completions = FakeCompletions(owner)


class FakeAsyncOpenAI:
    instances = []

    def __init__(self, api_key, base_url=None):
        self.api_key = api_key
        self.base_url = base_url
        self.calls = []
        self.models = FakeModels(self)
        self.chat = FakeChat(self)
        self.instances.append(self)


@pytest.fixture(autouse=True)
def fake_zai_openai(monkeypatch):
    FakeAsyncOpenAI.instances = []
    monkeypatch.setattr(zai, "AsyncOpenAI", FakeAsyncOpenAI)


def test_zai_provider_fields():
    fields = ModelSetupService().provider_fields("zai")

    assert [field.name for field in fields] == ["api_key_ref", "base_url", "max_tokens"]
    assert fields[0].required is True
    assert fields[0].secret is True
    assert fields[1].placeholder == DEFAULT_BASE_URL


@pytest.mark.asyncio
async def test_zai_validate_and_list_models_use_default_base_url():
    provider_config = {"api_key": "test-key"}
    service = ModelSetupService()

    await service.validate_provider_config("zai", provider_config)
    models = await service.list_models("zai", provider_config)

    assert [model.id for model in models] == ["glm-5", "glm-4.7", "glm-4.7-flash", "glm-4.6", "glm-4.6v"]
    assert models[-1].input == ["text", "image"]
    assert FakeAsyncOpenAI.instances[0].api_key == "test-key"
    assert FakeAsyncOpenAI.instances[0].base_url == DEFAULT_BASE_URL
    assert FakeAsyncOpenAI.instances[0].calls == [("models.list", None)]


def test_save_provider_models_writes_selected_zai_models(tmp_path: Path):
    config_dir = tmp_path / "model-providers"
    active_config_file = tmp_path / "model_active.json"
    service = ModelSetupService(config_dir=config_dir, active_config_file=active_config_file)

    saved = service.save_provider_models(
        provider="zai",
        provider_config={"api_key": "test-key", "base_url": DEFAULT_BASE_URL, "max_tokens": "2048"},
        enabled_models={
            "glm-4.6": {"temperature": 0.7, "max_tokens": 8192},
            "glm-4.5": {"temperature": 0.2, "max_tokens": 4096},
        },
        default_model="glm-4.5",
    )
    loaded = zai.load_provider_config(config_dir)
    active = ActiveModelConfig.load(active_config_file)

    assert saved.default_model == "glm-4.5"
    assert loaded.enabled_models == {
        "glm-4.6": {"temperature": 0.7, "max_tokens": 8192},
        "glm-4.5": {"temperature": 0.2, "max_tokens": 4096},
    }
    assert loaded.config["api_key"] == "test-key"
    assert active.provider == "zai"
    assert active.model == "glm-4.5"


def test_factory_creates_zai_provider_from_saved_config(tmp_path: Path):
    config_dir = tmp_path / "model-providers"
    active_config_file = tmp_path / "model_active.json"
    ModelSetupService(config_dir=config_dir, active_config_file=active_config_file).save_provider_models(
        provider="zai",
        provider_config={"api_key": "test-key", "max_tokens": "2048"},
        enabled_models={"glm-4.6": {"temperature": 0.6, "max_tokens": 2048}},
    )

    model_config = ModelConfig(_env_file=None, providers_config_dir=config_dir, active_config_file=active_config_file, temperature=0.2)
    provider = ModelProviderFactory(model_config).create("zai")

    assert isinstance(provider, ZAIClient)
    assert provider.default_temperature == 0.2
    assert provider.max_tokens == 2048
    assert FakeAsyncOpenAI.instances[0].base_url == DEFAULT_BASE_URL


def test_model_router_uses_saved_zai_default(tmp_path: Path):
    config_dir = tmp_path / "model-providers"
    active_config_file = tmp_path / "model_active.json"
    ModelSetupService(config_dir=config_dir, active_config_file=active_config_file).save_provider_models(
        provider="zai",
        provider_config={"api_key": "test-key"},
        enabled_models={"glm-4.6": {}, "glm-4.5": {}},
        default_model="glm-4.5",
    )
    model_config = ModelConfig(_env_file=None, providers_config_dir=config_dir, active_config_file=active_config_file)
    router = ModelRouter(ModelProviderFactory(model_config), model_config)

    assert router._resolve_model(None) == ModelSelection(provider="zai", name="glm-4.5")


@pytest.mark.asyncio
async def test_zai_complete_passes_model_and_generation_options(tmp_path: Path):
    config_dir = tmp_path / "model-providers"
    active_config_file = tmp_path / "model_active.json"
    ModelSetupService(config_dir=config_dir, active_config_file=active_config_file).save_provider_models(
        provider="zai",
        provider_config={"api_key": "test-key", "max_tokens": 512},
        enabled_models={"glm-4.6": {"temperature": 0.1, "max_tokens": 256}},
    )
    model_config = ModelConfig(_env_file=None, providers_config_dir=config_dir, active_config_file=active_config_file, temperature=0.3)
    provider = ModelProviderFactory(model_config).create("zai")

    response = await provider.complete(
        ChatRequest(
            messages=[ChatMessage(role="user", content="hello")],
            model=ModelSelection(provider="zai", name="glm-4.6"),
        )
    )

    assert response.content == "ok"
    _, kwargs = FakeAsyncOpenAI.instances[0].calls[0]
    assert kwargs["model"] == "glm-4.6"
    assert kwargs["messages"] == [{"role": "user", "content": "hello"}]
    assert kwargs["temperature"] == 0.1
    assert kwargs["max_tokens"] == 256
