from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.settings import BASE_SETTINGS_CONFIG


class TelegramGatewayConfig(BaseSettings):
    model_config = SettingsConfigDict(
        **BASE_SETTINGS_CONFIG,
        env_prefix="GATEWAY_TELEGRAM_",
    )

    enabled: bool = Field(default=False, description="是否启用 Telegram Gateway")
    bot_token: str = Field(default="", description="Telegram Bot Token（@BotFather）")
    allowed_chat_ids: list[int] = Field(
        default_factory=list,
        description="允许使用的 chat id 白名单，空列表表示 personal 模式下允许全部",
    )
    stream_replies: bool = Field(default=True, description="是否流式更新回复（edit 占位消息）")
    stream_edit_interval_chars: int = Field(default=120, ge=20, description="流式模式下每累计多少字符 edit 一次")


class GatewayConfig(BaseModel):
    telegram: TelegramGatewayConfig = Field(default_factory=TelegramGatewayConfig)
