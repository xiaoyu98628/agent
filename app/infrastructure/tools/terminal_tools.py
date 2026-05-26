import subprocess

from langchain_core.tools import BaseTool, tool

from app.infrastructure.tools.context import ToolContext


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
