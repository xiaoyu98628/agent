from app.domain.llm.entity import ModelSelection, StaticModelEntry
from app.domain.llm.exceptions import UnsupportedProviderError
from app.infrastructure.llm.providers.protocol import LlmProviderAdapter

_REGISTRY: dict[str, LlmProviderAdapter] = {}


def register(adapter: LlmProviderAdapter) -> None:
    _REGISTRY[adapter.name] = adapter


def get_adapter(provider: str) -> LlmProviderAdapter:
    key = provider.strip().lower()
    try:
        return _REGISTRY[key]
    except KeyError:
        raise UnsupportedProviderError(f"不支持的 provider: {key}") from None


def registered_providers() -> frozenset[str]:
    return frozenset(_REGISTRY)


def list_static_model_entries() -> list[StaticModelEntry]:
    entries: list[StaticModelEntry] = []
    for name in sorted(_REGISTRY):
        entries.extend(_REGISTRY[name].static_models)
    return entries


def list_static_models() -> list[ModelSelection]:
    return [ModelSelection(provider=entry.provider, model=entry.model) for entry in list_static_model_entries()]


def model_supports_tools(selection: ModelSelection) -> bool:
    key = selection.cache_key().lower()
    for entry in list_static_model_entries():
        if entry.cache_key().lower() == key:
            return entry.supports_tools
    return True


def _bootstrap_registry() -> None:
    from app.infrastructure.llm.providers.anthropic import adapter as anthropic_adapter
    from app.infrastructure.llm.providers.deepseek import adapter as deepseek_adapter
    from app.infrastructure.llm.providers.ollama import adapter as ollama_adapter
    from app.infrastructure.llm.providers.openai import adapter as openai_adapter
    from app.infrastructure.llm.providers.openrouter import adapter as openrouter_adapter
    from app.infrastructure.llm.providers.zhipu import adapter as zhipu_adapter

    register(openai_adapter)
    register(openrouter_adapter)
    register(anthropic_adapter)
    register(ollama_adapter)
    register(zhipu_adapter)
    register(deepseek_adapter)


_bootstrap_registry()
