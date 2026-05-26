from pydantic import BaseModel

from config.agent import AgentConfig
from config.app import AppConfig
from config.cors import CorsConfig
from config.gateway import GatewayConfig, TelegramGatewayConfig
from config.llm import LlmConfig
from config.logging import LoggingConfig
from config.memory import MemoryConfig, SkillsConfig
from config.rag import RagConfig
from config.storage import StorageConfig


class Config(BaseModel):
    app: AppConfig
    llm: LlmConfig
    agent: AgentConfig
    rag: RagConfig
    memory: MemoryConfig
    skills: SkillsConfig
    storage: StorageConfig
    logging: LoggingConfig
    cors: CorsConfig
    gateway: GatewayConfig


def config() -> Config:
    """获取配置。"""
    return Config(
        app=AppConfig(),
        llm=LlmConfig(),
        agent=AgentConfig(),
        rag=RagConfig(),
        memory=MemoryConfig(),
        skills=SkillsConfig(),
        storage=StorageConfig(),
        logging=LoggingConfig(),
        cors=CorsConfig(),
        gateway=GatewayConfig(telegram=TelegramGatewayConfig()),
    )
