from pydantic import BaseModel

from config.app import AppConfig
from config.model import ModelConfig


class Config(BaseModel):
    app: AppConfig
    model: ModelConfig


def config() -> Config:
    """获取配置。"""
    return Config(
        app=AppConfig(),
        model=ModelConfig(),
    )
