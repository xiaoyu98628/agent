from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.settings import BASE_SETTINGS_CONFIG
from paths import STORAGE_DIR


class AgentConfig(BaseSettings):
    """Agent 运行时配置。"""

    model_config = SettingsConfigDict(
        **BASE_SETTINGS_CONFIG,
        env_prefix="AGENT_",
    )

    max_iterations: int = Field(default=25, description="单轮对话最大工具迭代次数")
    default_tool_policy: Literal["full", "sandbox", "readonly"] = Field(
        default="full",
        description="默认工具策略：full 全工具 / sandbox 沙箱 / readonly 只读",
    )
    enabled_toolsets: list[str] = Field(default_factory=list, description="启用的 toolset，空表示全部")
    disabled_toolsets: list[str] = Field(default_factory=list, description="禁用的 toolset")
    sandbox_backend: Literal["none", "docker"] = Field(default="none", description="代码执行沙箱后端")
    workspace_subdir: str = Field(default="workspace", description="Agent 工作目录，位于 storage/ 下")
    command_timeout_seconds: int = Field(default=30, ge=1, le=300, description="终端命令超时（秒）")
    web_fetch_timeout_seconds: int = Field(default=15, ge=1, le=120, description="网页抓取超时（秒）")
    max_tool_output_chars: int = Field(default=8000, ge=500, description="工具输出最大字符数")
    max_read_file_bytes: int = Field(default=512_000, ge=1024, description="read_file 单文件最大字节")
    max_history_messages: int = Field(
        default=200,
        ge=0,
        description="从 SQLite 加载会话历史时的最大消息条数，0 表示不限制",
    )
    summarization_enabled: bool = Field(default=True, description="是否启用 LangChain SummarizationMiddleware 压缩上下文")
    summarization_trigger_messages: int = Field(default=40, ge=4, description="消息数达到该值时触发摘要")
    summarization_keep_messages: int = Field(default=20, ge=2, description="摘要后保留的最近消息条数")
    summarization_trigger_tokens: int | None = Field(
        default=None,
        ge=512,
        description="可选：token 数达到该值时触发摘要",
    )
    summarization_trigger_fraction: float | None = Field(
        default=None,
        ge=0.05,
        le=0.95,
        description="可选：上下文占比达到该值时触发摘要（0~1）",
    )
    summarization_provider: str | None = Field(
        default=None,
        description="摘要模型 provider，空则复用当前对话模型",
    )
    summarization_model: str | None = Field(
        default=None,
        description="摘要模型名称，空则复用当前对话模型",
    )

    @property
    def workspace_dir(self) -> str:
        return str(STORAGE_DIR / self.workspace_subdir)
