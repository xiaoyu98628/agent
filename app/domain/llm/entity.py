from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelSelection:
    """运行时模型选择。"""

    provider: str
    model: str
    temperature: float | None = None
    max_tokens: int | None = None

    def cache_key(self) -> str:
        return f"{self.provider}:{self.model}"


@dataclass(frozen=True, slots=True)
class LlmCredentials:
    """LLM 调用凭据。"""

    api_key: str | None = None
    base_url: str | None = None
