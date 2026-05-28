from app.domain.llm.entity import ModelSelection
from app.domain.llm.exceptions import ModelNotAllowedError, UnsupportedProviderError
from app.infrastructure.llm.registry import list_static_models
from config.config import config


def default_selection() -> ModelSelection:
    """系统默认模型（config/llm.py）。"""
    configure = config()
    return ModelSelection(
        provider=configure.llm.provider,
        model=configure.llm.model,
        temperature=configure.llm.temperature,
        max_tokens=configure.llm.max_tokens,
    )


def resolve_selection(
    *,
    provider: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> ModelSelection:
    """合并请求参数与默认值，得到最终 ModelSelection。"""
    configure = config()
    base = default_selection()

    if provider is None and model is None and temperature is None and max_tokens is None:
        return base

    if not configure.llm.allow_model_override and (provider is not None or model is not None):
        return base

    selection = ModelSelection(
        provider=(provider or base.provider).strip().lower(),
        model=(model or base.model).strip(),
        temperature=temperature if temperature is not None else base.temperature,
        max_tokens=max_tokens if max_tokens is not None else base.max_tokens,
    )
    validate_selection(selection)
    return selection


def validate_selection(selection: ModelSelection) -> None:
    """校验 provider / model 是否允许。"""
    configure = config()
    provider = selection.provider.strip().lower()

    if provider not in {p.lower() for p in configure.llm.allowed_providers}:
        raise UnsupportedProviderError(f"不支持的 provider: {provider}")

    allowed_models = {entry.cache_key() for entry in list_static_models()}
    if allowed_models and selection.cache_key() not in allowed_models:
        raise ModelNotAllowedError(f"模型不在允许列表中: {selection.cache_key()}")
