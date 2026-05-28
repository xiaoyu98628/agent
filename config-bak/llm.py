from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.settings import BASE_SETTINGS_CONFIG


class LlmConfig(BaseSettings):
    """LLM 提供商与模型配置。"""

    model_config = SettingsConfigDict(
        **BASE_SETTINGS_CONFIG,
        env_prefix="LLM_",
    )

    provider: str = Field(default="openrouter", description="默认 provider")
    model: str = Field(default="anthropic/claude-sonnet-4-6", description="默认模型")

    api_key: str | None = Field(default=None, description="通用 API Key fallback（LLM_API_KEY）")
    base_url: str | None = Field(default=None, description="OpenAI 兼容 Base URL")

    # OpenAI
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")

    # OpenRouter
    openrouter_api_key: str | None = Field(default=None, validation_alias="OPENROUTER_API_KEY")

    # Anthropic
    anthropic_api_key: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")

    # 智谱
    zhipu_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ZHIPUAI_API_KEY", "GLM_API_KEY", "ZAI_API_KEY"),
    )
    zhipu_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ZHIPU_BASE_URL"),
        description="智谱 / Z.ai API Base URL；未设置时默认 Z.ai 国际站",
    )

    # DeepSeek
    deepseek_api_key: str | None = Field(default=None, validation_alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DEEPSEEK_BASE_URL"),
        description="DeepSeek API Base URL；未设置时默认 https://api.deepseek.com",
    )

    # Ollama
    ollama_base_url: str | None = Field(default=None, validation_alias="OLLAMA_BASE_URL")

    temperature: float = Field(default=0.7, description="采样温度")
    max_tokens: int | None = Field(default=None, description="单次回复最大 token")

    allowed_providers: list[str] = Field(
        default_factory=lambda: ["openai", "openrouter", "anthropic", "ollama", "zhipu", "deepseek"],
        description="允许的 provider 列表",
    )
    catalog_source: Literal["static"] = Field(default="static", description="模型目录来源（Phase 1: static）")
    allow_model_override: bool = Field(default=True, description="是否允许请求级覆盖模型")
