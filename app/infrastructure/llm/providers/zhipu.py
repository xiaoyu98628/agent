from dataclasses import dataclass
from typing import Any

from app.domain.llm.entity import LlmCredentials, ModelSelection, StaticModelEntry
from app.infrastructure.llm.providers.common import (
    build_openai_compatible_chat_model,
    resolve_api_key_or_fallback,
    static_model,
    strip,
)
from config.config import Config

_DEFAULT_ZHIPU_BASE_URL = "https://api.z.ai/api/paas/v4"
_CREDENTIAL_HINT = "ZHIPUAI_API_KEY / GLM_API_KEY / ZAI_API_KEY 或 LLM_API_KEY"


@dataclass(frozen=True, slots=True)
class ZhipuAdapter:
    name: str = "zhipu"
    static_models: tuple[StaticModelEntry, ...] = (
        static_model("zhipu", "glm-4.7", "GLM-4.7 (智谱)"),
        static_model("zhipu", "glm-4-flash", "GLM-4 Flash (智谱)"),
        static_model("zhipu", "glm-4-plus", "GLM-4 Plus (智谱)"),
        static_model("zhipu", "glm-5", "GLM-5 (智谱)"),
    )

    def resolve_credentials(self, configure: Config) -> LlmCredentials:
        api_key = resolve_api_key_or_fallback(
            configure,
            provider=self.name,
            provider_api_key=configure.llm.zhipu_api_key,
            hint=_CREDENTIAL_HINT,
        )
        base_url = strip(configure.llm.base_url)
        if not base_url:
            base_url = strip(configure.llm.zhipu_base_url) or _DEFAULT_ZHIPU_BASE_URL
        return LlmCredentials(api_key=api_key, base_url=base_url)

    def build_chat_model(self, selection: ModelSelection, credentials: LlmCredentials) -> Any:
        return build_openai_compatible_chat_model(selection.model, credentials, selection)


adapter = ZhipuAdapter()
