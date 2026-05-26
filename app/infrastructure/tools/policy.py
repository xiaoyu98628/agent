from dataclasses import dataclass

from config.config import Config

TOOLSET_FILE = "file"
TOOLSET_WEB = "web"
TOOLSET_TERMINAL = "terminal"
TOOLSET_RAG = "rag"
TOOLSET_MEMORY = "memory"
TOOLSET_SKILLS = "skills"
TOOLSET_SESSION = "session"
TOOLSET_TODO = "todo"

ALL_TOOLSETS = (TOOLSET_FILE, TOOLSET_WEB, TOOLSET_TERMINAL, TOOLSET_RAG, TOOLSET_MEMORY, TOOLSET_SKILLS, TOOLSET_SESSION, TOOLSET_TODO)


@dataclass(frozen=True, slots=True)
class ToolPolicy:
    policy: str
    toolsets: frozenset[str]
    allow_write: bool
    allow_terminal: bool


def resolve_tool_policy(configure: Config) -> ToolPolicy:
    """按 deployment_mode + agent 配置解析可用 toolset。"""
    app_cfg = configure.app
    agent_cfg = configure.agent
    policy = agent_cfg.default_tool_policy

    allow_write = policy in {"full", "sandbox"}
    allow_terminal = (
        app_cfg.deployment_mode == "personal"
        and policy == "full"
        and TOOLSET_TERMINAL not in agent_cfg.disabled_toolsets
        and (not agent_cfg.enabled_toolsets or TOOLSET_TERMINAL in agent_cfg.enabled_toolsets)
    )

    toolsets = set(ALL_TOOLSETS)
    if not allow_terminal:
        toolsets.discard(TOOLSET_TERMINAL)
    if agent_cfg.enabled_toolsets:
        toolsets &= set(agent_cfg.enabled_toolsets)
    if agent_cfg.disabled_toolsets:
        toolsets -= set(agent_cfg.disabled_toolsets)

    return ToolPolicy(
        policy=policy,
        toolsets=frozenset(toolsets),
        allow_write=allow_write,
        allow_terminal=allow_terminal,
    )
