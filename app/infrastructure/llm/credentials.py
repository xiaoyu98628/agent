from app.domain.llm.entity import LlmCredentials
from app.domain.llm.exceptions import MissingCredentialError
from config.config import Config, config

_DEFAULT_ZHIPU_BASE_URL = "https://api.z.ai/api/paas/v4"
_DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
_DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"

_PROVIDER_KEY_HINTS: dict[str, str] = {
    "openai": "OPENAI_API_KEY 或 LLM_API_KEY",
    "openrouter": "OPENROUTER_API_KEY 或 LLM_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY 或 LLM_API_KEY",
    "zhipu": "ZHIPUAI_API_KEY / GLM_API_KEY / ZAI_API_KEY 或 LLM_API_KEY",
}


def _strip(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _provider_api_key(provider_norm: str, configure: Config) -> str | None:
    match provider_norm:
        case "openai":
            return _strip(configure.llm.openai_api_key)
        case "openrouter":
            return _strip(configure.llm.openrouter_api_key)
        case "anthropic":
            return _strip(configure.llm.anthropic_api_key)
        case "zhipu":
            return _strip(configure.llm.zhipu_api_key)
        case _:
            return None


def resolve_credentials(provider: str) -> LlmCredentials:
    """从 pydantic-settings（.env）解析 BYOK 凭据。"""
    provider_norm = provider.strip().lower()
    configure = config()

    if provider_norm == "ollama":
        return LlmCredentials(
            api_key=None,
            base_url=_strip(configure.llm.ollama_base_url) or _DEFAULT_OLLAMA_BASE_URL,
        )

    api_key = _provider_api_key(provider_norm, configure) or _strip(configure.llm.api_key)
    if not api_key:
        hint = _PROVIDER_KEY_HINTS.get(provider_norm, "LLM_API_KEY")
        raise MissingCredentialError(f"未配置 {provider_norm} 的 API Key，请在 .env 设置 {hint}")

    base_url = _strip(configure.llm.base_url)
    if provider_norm == "openrouter" and not base_url:
        base_url = _DEFAULT_OPENROUTER_BASE_URL
    if provider_norm == "zhipu" and not base_url:
        base_url = _strip(configure.llm.zhipu_base_url) or _DEFAULT_ZHIPU_BASE_URL

    return LlmCredentials(api_key=api_key, base_url=base_url)
