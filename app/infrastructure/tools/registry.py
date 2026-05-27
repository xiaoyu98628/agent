from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from langchain_core.tools import BaseTool

from app.infrastructure.tools.context import ToolContext
from app.infrastructure.tools.file_tools import build_file_tools
from app.infrastructure.tools.memory_tools import build_memory_tools
from app.infrastructure.tools.policy import (
    TOOLSET_FILE,
    TOOLSET_MEMORY,
    TOOLSET_RAG,
    TOOLSET_SESSION,
    TOOLSET_SKILLS,
    TOOLSET_TERMINAL,
    TOOLSET_TODO,
    TOOLSET_WEB,
    ToolPolicy,
    resolve_tool_policy,
)
from app.infrastructure.tools.rag_tools import build_rag_tools
from app.infrastructure.tools.session_tools import build_session_tools
from app.infrastructure.tools.skill_tools import build_skill_tools
from app.infrastructure.tools.terminal_tools import build_terminal_tools
from app.infrastructure.tools.todo_tools import build_todo_tools
from app.infrastructure.tools.web_tools import build_web_tools
from config.config import Config


@dataclass(frozen=True, slots=True)
class ToolsetAdapter:
    name: str
    build: Callable[[ToolContext], list[BaseTool]]
    enabled: Callable[[Config, ToolPolicy], bool]


def _build_context(configure: Config, policy: ToolPolicy) -> ToolContext:
    agent_cfg = configure.agent
    return ToolContext(
        workspace_root=Path(agent_cfg.workspace_dir),
        allow_write=policy.allow_write,
        dangerous_command_policy=agent_cfg.dangerous_command_policy,
        command_timeout_seconds=agent_cfg.command_timeout_seconds,
        web_fetch_timeout_seconds=agent_cfg.web_fetch_timeout_seconds,
        max_output_chars=agent_cfg.max_tool_output_chars,
        max_read_file_bytes=agent_cfg.max_read_file_bytes,
    )


def _enabled(_: Config, __: ToolPolicy) -> bool:
    return True


def _rag_enabled(configure: Config, _: ToolPolicy) -> bool:
    return configure.rag.enabled


def _memory_enabled(configure: Config, _: ToolPolicy) -> bool:
    return configure.memory.enabled


def _skills_enabled(configure: Config, _: ToolPolicy) -> bool:
    return configure.skills.enabled


def _terminal_enabled(_: Config, policy: ToolPolicy) -> bool:
    return policy.allow_terminal


def _without_context(builder: Callable[[], list[BaseTool]]) -> Callable[[ToolContext], list[BaseTool]]:
    def wrapped(_: ToolContext) -> list[BaseTool]:
        return builder()

    return wrapped


_TOOLSET_ADAPTERS: tuple[ToolsetAdapter, ...] = (
    ToolsetAdapter(name=TOOLSET_FILE, build=build_file_tools, enabled=_enabled),
    ToolsetAdapter(name=TOOLSET_WEB, build=build_web_tools, enabled=_enabled),
    ToolsetAdapter(name=TOOLSET_RAG, build=_without_context(build_rag_tools), enabled=_rag_enabled),
    ToolsetAdapter(name=TOOLSET_MEMORY, build=_without_context(build_memory_tools), enabled=_memory_enabled),
    ToolsetAdapter(name=TOOLSET_SKILLS, build=_without_context(build_skill_tools), enabled=_skills_enabled),
    ToolsetAdapter(name=TOOLSET_SESSION, build=_without_context(build_session_tools), enabled=_enabled),
    ToolsetAdapter(name=TOOLSET_TODO, build=_without_context(build_todo_tools), enabled=_enabled),
    ToolsetAdapter(name=TOOLSET_TERMINAL, build=build_terminal_tools, enabled=_terminal_enabled),
)


def registered_toolsets() -> tuple[str, ...]:
    return tuple(adapter.name for adapter in _TOOLSET_ADAPTERS)


def build_agent_tools(configure: Config) -> list[BaseTool]:
    """按配置组装 LangChain 工具列表。"""
    policy = resolve_tool_policy(configure, available_toolsets=registered_toolsets())
    if not policy.toolsets:
        return []

    ctx = _build_context(configure, policy)
    tools: list[BaseTool] = []
    for adapter in _TOOLSET_ADAPTERS:
        if adapter.name in policy.toolsets and adapter.enabled(configure, policy):
            tools.extend(adapter.build(ctx))

    return tools


def describe_agent_tools(configure: Config) -> dict:
    """返回当前运行时工具策略与工具名列表（供 API 展示）。"""
    policy = resolve_tool_policy(configure, available_toolsets=registered_toolsets())
    tools = build_agent_tools(configure)
    return {
        "deployment_mode": configure.app.deployment_mode,
        "policy": policy.policy,
        "toolsets": sorted(policy.toolsets),
        "allow_write": policy.allow_write,
        "allow_terminal": policy.allow_terminal,
        "workspace_dir": configure.agent.workspace_dir,
        "tools": [{"name": tool.name, "description": tool.description or ""} for tool in tools],
    }
