from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.settings import BASE_SETTINGS_CONFIG
from paths import STORAGE_DIR


class MemoryConfig(BaseSettings):
    model_config = SettingsConfigDict(
        **BASE_SETTINGS_CONFIG,
        env_prefix="MEMORY_",
    )

    enabled: bool = Field(default=True, description="是否启用长期记忆")
    user_profile_enabled: bool = Field(default=True, description="是否启用 USER 画像")
    memory_char_limit: int = Field(default=2200, ge=256, description="memory 目标字符上限")
    user_char_limit: int = Field(default=1375, ge=256, description="user 目标字符上限")
    entry_separator: str = Field(default="\n§\n", description="渲染条目分隔符")


class SkillsConfig(BaseSettings):
    model_config = SettingsConfigDict(
        **BASE_SETTINGS_CONFIG,
        env_prefix="SKILLS_",
    )

    enabled: bool = Field(default=True, description="是否启用 Skills")
    skills_subdir: str = Field(default="skills", description="Skills 根目录，位于 storage/ 下")

    @property
    def skills_dir(self) -> str:
        return str(STORAGE_DIR / self.skills_subdir)
