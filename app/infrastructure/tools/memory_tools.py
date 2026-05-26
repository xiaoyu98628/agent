from langchain_core.tools import BaseTool, tool

from app.infrastructure.memory.sqlite_sync import sync_handle_memory_tool
from config.config import config


def build_memory_tools() -> list[BaseTool]:
    configure = config()
    if not configure.memory.enabled:
        return []

    @tool
    def memory(action: str, target: str, content: str | None = None, old_text: str | None = None) -> str:
        """Manage long-term memory. action: add|replace|remove; target: memory|user."""
        return sync_handle_memory_tool(action=action, target=target, content=content, old_text=old_text)

    return [memory]
