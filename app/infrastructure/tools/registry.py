from pathlib import Path

from langchain_core.tools import BaseTool

from app.infrastructure.tools.context import ToolContext
from app.infrastructure.tools.file_tools import build_file_tools
from app.infrastructure.tools.memory_tools import build_memory_tools
from app.infrastructure.tools.policy import (
    TOOLSET_FILE,
    TOOLSET_MEMORY,
    TOOLSET_RAG,
    TOOLSET_SKILLS,
    TOOLSET_TERMINAL,
    TOOLSET_WEB,
    ToolPolicy,
    resolve_tool_policy,
)
from app.infrastructure.tools.rag_tools import build_rag_tools
from app.infrastructure.tools.skill_tools import build_skill_tools
from app.infrastructure.tools.terminal_tools import build_terminal_tools
from app.infrastructure.tools.web_tools import build_web_tools
from config.config import Config


def _build_context(configure: Config, policy: ToolPolicy) -> ToolContext:
    agent_cfg = configure.agent
    return ToolContext(
        workspace_root=Path(agent_cfg.workspace_dir),
        allow_write=policy.allow_write,
        command_timeout_seconds=agent_cfg.command_timeout_seconds,
        web_fetch_timeout_seconds=agent_cfg.web_fetch_timeout_seconds,
        max_output_chars=agent_cfg.max_tool_output_chars,
        max_read_file_bytes=agent_cfg.max_read_file_bytes,
    )


def build_agent_tools(configure: Config) -> list[BaseTool]:
    """按配置组装 LangChain 工具列表。"""
    policy = resolve_tool_policy(configure)
    if not policy.toolsets:
        return []

    ctx = _build_context(configure, policy)
    tools: list[BaseTool] = []

    if TOOLSET_FILE in policy.toolsets:
        tools.extend(build_file_tools(ctx))
    if TOOLSET_WEB in policy.toolsets:
        tools.extend(build_web_tools(ctx))
    if TOOLSET_RAG in policy.toolsets and configure.rag.enabled:
        tools.extend(build_rag_tools())
    if TOOLSET_MEMORY in policy.toolsets and configure.memory.enabled:
        tools.extend(build_memory_tools())
    if TOOLSET_SKILLS in policy.toolsets and configure.skills.enabled:
        tools.extend(build_skill_tools())
    if TOOLSET_TERMINAL in policy.toolsets and policy.allow_terminal:
        tools.extend(build_terminal_tools(ctx))

    return tools


def describe_agent_tools(configure: Config) -> dict:
    """返回当前运行时工具策略与工具名列表（供 API 展示）。"""
    policy = resolve_tool_policy(configure)
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
