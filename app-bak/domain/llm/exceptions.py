from app.domain.exceptions import DomainError


class LlmError(DomainError):
    """LLM 领域错误基类。"""


class UnsupportedProviderError(LlmError):
    """不支持的 provider。"""


class MissingCredentialError(LlmError):
    """缺少 API Key 或凭据。"""


class ModelNotAllowedError(LlmError):
    """模型不在允许列表中。"""
