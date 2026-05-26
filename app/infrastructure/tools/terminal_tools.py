import re
import subprocess

from langchain_core.tools import BaseTool, tool

from app.infrastructure.tools.context import ToolContext

_DANGEROUS_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\brm\s+(-[^\n]*[rf][^\n]*|-[^\n]*[fr][^\n]*)\s+(/|~|\$HOME|\.)"), "recursive delete"),
    (re.compile(r"\b(?:mkfs|fdisk|parted|diskutil)\b", re.IGNORECASE), "disk formatting or partitioning"),
    (re.compile(r"\bdd\s+.*\bof=/dev/", re.IGNORECASE), "raw device write"),
    (re.compile(r">\s*/(?:etc|bin|sbin|usr|var)/"), "system path overwrite"),
    (re.compile(r"\b(?:shutdown|reboot|halt|poweroff)\b", re.IGNORECASE), "system shutdown"),
    (re.compile(r"\b(?:killall|pkill)\s+(-9\s+)?(?:python|uvicorn|postgres|redis|node|npm|docker)\b", re.IGNORECASE), "broad process kill"),
    (re.compile(r"\bDROP\s+(?:TABLE|DATABASE)\b", re.IGNORECASE), "destructive SQL"),
    (re.compile(r"\bDELETE\s+FROM\b(?![\s\S]*\bWHERE\b)", re.IGNORECASE), "delete without WHERE"),
    (re.compile(r"\bcurl\b[\s\S]*\|\s*(?:sh|bash|zsh)\b", re.IGNORECASE), "remote shell execution"),
    (re.compile(r"\bwget\b[\s\S]*\|\s*(?:sh|bash|zsh)\b", re.IGNORECASE), "remote shell execution"),
)


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [truncated, total {len(text)} chars]"


def build_terminal_tools(ctx: ToolContext) -> list[BaseTool]:
    timeout = ctx.command_timeout_seconds
    cwd = str(ctx.workspace_root)
    max_chars = ctx.max_output_chars

    @tool
    def run_terminal_command(command: str) -> str:
        """Run a shell command in the agent workspace directory. stdout/stderr are returned."""
        command = command.strip()
        if not command:
            return "Error: empty command"
        danger = _detect_dangerous_command(command)
        if danger and ctx.dangerous_command_policy == "block":
            return f"Error: blocked dangerous command ({danger}). Set AGENT_DANGEROUS_COMMAND_POLICY=allow to permit it in personal mode."
        try:
            completed = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
            )
        except subprocess.TimeoutExpired:
            return f"Error: command timed out after {timeout}s"
        except OSError as exc:
            return f"Error: {exc}"

        parts: list[str] = [f"exit_code={completed.returncode}"]
        if completed.stdout:
            parts.append(f"stdout:\n{completed.stdout.rstrip()}")
        if completed.stderr:
            parts.append(f"stderr:\n{completed.stderr.rstrip()}")
        if len(parts) == 1:
            parts.append("(no output)")
        return _truncate("\n".join(parts), max_chars)

    return [run_terminal_command]


def _detect_dangerous_command(command: str) -> str:
    for pattern, description in _DANGEROUS_PATTERNS:
        if pattern.search(command):
            return description
    return ""
