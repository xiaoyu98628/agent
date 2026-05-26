from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.settings import BASE_SETTINGS_CONFIG
from paths import STORAGE_DIR


class StorageConfig(BaseSettings):
    model_config = SettingsConfigDict(
        **BASE_SETTINGS_CONFIG,
        env_prefix="STORAGE_",
    )

    sqlite_path: str = Field(default="agent.sqlite", description="SQLite 文件名，位于 storage/ 目录")
    default_workspace_id: str = Field(default="local", description="personal 模式默认 workspace")

    @property
    def sqlite_file(self) -> str:
        return str(STORAGE_DIR / self.sqlite_path)
