from langchain.agents.middleware import SummarizationMiddleware

from app.domain.llm.entity import ModelSelection
from app.infrastructure.llm.factory import build_langchain_model
from config.config import Config


def build_summarization_middleware(configure: Config, selection: ModelSelection) -> list[SummarizationMiddleware]:
    """组装 LangChain 短时记忆中间件（上下文摘要压缩）。"""
    agent_cfg = configure.agent
    if not agent_cfg.summarization_enabled:
        return []

    if agent_cfg.summarization_provider and agent_cfg.summarization_model:
        summary_selection = ModelSelection(
            provider=agent_cfg.summarization_provider,
            model=agent_cfg.summarization_model,
            temperature=selection.temperature,
            max_tokens=selection.max_tokens,
        )
    else:
        summary_selection = selection

    triggers: list[tuple[str, int] | tuple[str, float]] = [("messages", agent_cfg.summarization_trigger_messages)]
    if agent_cfg.summarization_trigger_tokens is not None:
        triggers.append(("tokens", agent_cfg.summarization_trigger_tokens))
    if agent_cfg.summarization_trigger_fraction is not None:
        triggers.append(("fraction", agent_cfg.summarization_trigger_fraction))

    trigger: tuple[str, int] | tuple[str, float] | list[tuple[str, int] | tuple[str, float]]
    trigger = triggers[0] if len(triggers) == 1 else triggers

    return [
        SummarizationMiddleware(
            model=build_langchain_model(summary_selection),
            trigger=trigger,
            keep=("messages", agent_cfg.summarization_keep_messages),
        )
    ]
