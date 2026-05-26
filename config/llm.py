from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.settings import BASE_SETTINGS_CONFIG


class StaticModelEntry(BaseSettings):
    """静态模型目录条目。"""

    model_config = SettingsConfigDict(extra="ignore")

    provider: str
    model: str
    label: str
    supports_tools: bool = True


# Phase 1 内置可选模型（可通过配置扩展）
DEFAULT_STATIC_MODELS: list[dict[str, str | bool]] = [
    {"provider": "zhipu", "model": "glm-4.7", "label": "GLM-4.7 (智谱)", "supports_tools": True},
    {"provider": "zhipu", "model": "glm-4-flash", "label": "GLM-4 Flash (智谱)", "supports_tools": True},
    {"provider": "zhipu", "model": "glm-4-plus", "label": "GLM-4 Plus (智谱)", "supports_tools": True},
    {"provider": "zhipu", "model": "glm-5", "label": "GLM-5 (智谱)", "supports_tools": True},
    {"provider": "openrouter", "model": "anthropic/claude-sonnet-4-6", "label": "Claude Sonnet 4.6 (OpenRouter)", "supports_tools": True},
    {"provider": "openrouter", "model": "openai/gpt-4o", "label": "GPT-4o (OpenRouter)", "supports_tools": True},
    {"provider": "openrouter", "model": "google/gemini-2.5-flash", "label": "Gemini 2.5 Flash (OpenRouter)", "supports_tools": True},
    {"provider": "openai", "model": "gpt-4o", "label": "GPT-4o (OpenAI)", "supports_tools": True},
    {"provider": "openai", "model": "gpt-4o-mini", "label": "GPT-4o Mini (OpenAI)", "supports_tools": True},
    {"provider": "anthropic", "model": "claude-sonnet-4-6", "label": "Claude Sonnet 4.6 (Anthropic)", "supports_tools": True},
    {"provider": "ollama", "model": "llama3.2", "label": "Llama 3.2 (Ollama local)", "supports_tools": True},
]


class LlmConfig(BaseSettings):
    """LLM 提供商与模型配置。"""

    model_config = SettingsConfigDict(
        **BASE_SETTINGS_CONFIG,
        env_prefix="LLM_",
    )

    provider: str = Field(default="openrouter", description="默认 provider")
    model: str = Field(default="anthropic/claude-sonnet-4-6", description="默认模型")
    api_key: str | None = Field(default=None, description="通用 API Key fallback（LLM_API_KEY）")
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openrouter_api_key: str | None = Field(default=None, validation_alias="OPENROUTER_API_KEY")
    anthropic_api_key: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    zhipu_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ZHIPUAI_API_KEY", "GLM_API_KEY", "ZAI_API_KEY"),
    )
    base_url: str | None = Field(default=None, description="OpenAI 兼容 Base URL")
    temperature: float = Field(default=0.7, description="采样温度")
    max_tokens: int | None = Field(default=None, description="单次回复最大 token")
    allowed_providers: list[str] = Field(
        default_factory=lambda: ["openai", "openrouter", "anthropic", "ollama", "zhipu"],
        description="允许的 provider 列表",
    )
    zhipu_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ZHIPU_BASE_URL"),
        description="智谱 / Z.ai API Base URL；未设置时默认 Z.ai 国际站",
    )
    ollama_base_url: str | None = Field(default=None, validation_alias="OLLAMA_BASE_URL")
    catalog_source: Literal["static"] = Field(default="static", description="模型目录来源（Phase 1: static）")
    allow_model_override: bool = Field(default=True, description="是否允许请求级覆盖模型")
