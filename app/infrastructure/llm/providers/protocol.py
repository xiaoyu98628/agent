from typing import Any, Protocol

from app.domain.llm.entity import LlmCredentials, ModelSelection, StaticModelEntry
from config.config import Config


class LlmProviderAdapter(Protocol):
    """单个 LLM 厂商的凭据解析与 ChatModel 构建。

    上层 Agent 仍消费 LangChain ChatModel。若某厂商需官方 SDK，在 adapter 内包装为
    BaseChatModel 后再返回，调用方无需感知。
    """

    name: str
    static_models: tuple[StaticModelEntry, ...]

    def resolve_credentials(self, configure: Config) -> LlmCredentials:
        """从 Config 解析 BYOK；缺 key 时抛 MissingCredentialError。"""
        ...

    def build_chat_model(self, selection: ModelSelection, credentials: LlmCredentials) -> Any:
        """返回 LangChain ChatModel 实例（或 init_chat_model 可识别的等价类型）。"""
        ...
