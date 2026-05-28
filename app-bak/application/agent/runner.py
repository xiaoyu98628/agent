from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from langchain.agents import create_agent

from app.application.agent.middleware import build_summarization_middleware
from app.application.agent.prompt_context import build_runtime_context_prompt
from app.application.support.text import sanitize_text
from app.domain.llm.entity import ModelSelection
from app.infrastructure.llm.factory import build_langchain_model
from app.infrastructure.llm.registry import model_supports_tools
from app.infrastructure.memory.sqlite_sync import sync_format_snapshot
from app.infrastructure.skill.loader import build_skills_prompt_index
from app.infrastructure.tools.registry import build_agent_tools
from config.config import config


def _build_system_prompt(selection: ModelSelection, tool_names: list[str]) -> str:
    configure = config()
    head = (
        f"You are an AI assistant powered by {selection.provider} model `{selection.model}`. "
        "When asked about your identity or model, answer according to this runtime model, not other products."
    )
    parts = [head]
    if tool_names:
        joined = ", ".join(tool_names)
        parts.append(
            f"You have access to tools: {joined}. "
            "Use tools when they help answer the user; explain results clearly. "
            "File paths are relative to the agent workspace directory. "
            "After tool calls, always reply to the user in natural language."
        )
        if "memory" in tool_names:
            parts.append(
                "Use the memory tool to persist compact, durable facts that will matter in future sessions: "
                "user preferences, stable project facts, and tool quirks."
            )
        if "session_search" in tool_names:
            parts.append("When the user refers to prior conversations or missing context, use session_search before asking them to repeat it.")
        if "todo" in tool_names:
            parts.append("For multi-step work, use the todo tool to track concrete pending and completed steps.")
    skill_index = build_skills_prompt_index()
    if skill_index:
        parts.append(skill_index)
    if configure.memory.enabled:
        memory_block = sync_format_snapshot(workspace_id=configure.storage.default_workspace_id)
        if memory_block:
            parts.append(memory_block)
    if configure.agent.context_files_enabled:
        runtime_context = build_runtime_context_prompt(max_chars=configure.agent.max_context_file_chars)
        if runtime_context:
            parts.append(runtime_context)
    return "\n\n".join(parts)


@dataclass(frozen=True, slots=True)
class AgentRunResult:
    reply: str
    model: ModelSelection
    raw_messages: list[Any]


class AgentRunner:
    """LangChain Agent 编排。"""

    def __init__(self, system_prompt: str | None = None) -> None:
        self._system_prompt_override = system_prompt

    def _run_config(self) -> dict[str, Any]:
        configure = config()
        return {"recursion_limit": configure.agent.max_iterations}

    def _create_agent(self, selection: ModelSelection):
        configure = config()
        tools = build_agent_tools(configure) if model_supports_tools(selection) else []
        tool_names = [tool.name for tool in tools]
        system_prompt = self._system_prompt_override or _build_system_prompt(selection, tool_names)
        model = build_langchain_model(selection)
        middleware = build_summarization_middleware(configure, selection)
        return create_agent(
            model=model,
            tools=tools,
            system_prompt=system_prompt,
            middleware=middleware,
        )

    def _build_messages(self, user_message: str, history: list[dict[str, str]] | None) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = list(history or [])
        messages.append({"role": "user", "content": user_message})
        return messages

    def run(
        self,
        *,
        user_message: str,
        selection: ModelSelection,
        history: list[dict[str, str]] | None = None,
    ) -> AgentRunResult:
        agent = self._create_agent(selection)
        messages = self._build_messages(user_message, history)
        result = agent.invoke({"messages": messages}, config=self._run_config())
        raw_messages = result.get("messages", [])
        reply = _extract_reply(raw_messages)
        return AgentRunResult(reply=reply, model=selection, raw_messages=raw_messages)

    async def stream(
        self,
        *,
        user_message: str,
        selection: ModelSelection,
        history: list[dict[str, str]] | None = None,
    ) -> AsyncIterator[str]:
        agent = self._create_agent(selection)
        messages = self._build_messages(user_message, history)
        async for chunk in agent.astream(
            {"messages": messages},
            stream_mode="messages",
            config=self._run_config(),
        ):
            delta = _extract_stream_delta(chunk)
            if delta:
                yield delta


def _extract_stream_delta(chunk: Any) -> str:
    message = chunk[0] if isinstance(chunk, tuple) and chunk else chunk
    if isinstance(message, dict):
        content = message.get("content", "")
    else:
        content = getattr(message, "content", "")
    if isinstance(content, str):
        return sanitize_text(content) if content else ""
    if isinstance(content, list):
        return _message_text(message)
    return ""


def _extract_reply(messages: list[Any]) -> str:
    for message in reversed(messages):
        text = _message_text(message, roles={"ai", "assistant"})
        if text:
            return text

    for message in reversed(messages):
        text = _message_text(message, roles={"tool"})
        if text and not text.startswith("Error:"):
            return text

    return ""


def _message_text(message: Any, *, roles: set[str] | None = None) -> str:
    if isinstance(message, dict):
        role = message.get("role") or message.get("type")
        if roles is not None and role not in roles:
            return ""
        content = message.get("content", "")
    else:
        role = getattr(message, "type", None) or getattr(message, "role", None)
        if roles is not None and role not in roles:
            return ""
        content = getattr(message, "content", "")

    if isinstance(content, str):
        return sanitize_text(content.strip())
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(str(block.get("text", "")))
                elif block.get("type") in {"reasoning", "thinking"}:
                    parts.append(str(block.get("text") or block.get("reasoning", "")))
            elif hasattr(block, "text"):
                parts.append(str(block.text))
        return sanitize_text("".join(parts).strip())
    if content is None:
        return ""
    return sanitize_text(str(content).strip())
