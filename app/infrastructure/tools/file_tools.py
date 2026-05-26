from langchain_core.tools import BaseTool, tool

from app.infrastructure.tools.context import ToolContext
from app.infrastructure.tools.path_guard import PathGuard, PathGuardError


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [truncated, total {len(text)} chars]"


def build_file_tools(ctx: ToolContext) -> list[BaseTool]:
    guard = PathGuard(ctx.workspace_root)

    @tool
    def read_file(path: str) -> str:
        """Read a UTF-8 text file under the agent workspace. Path is relative to workspace root."""
        try:
            target = guard.resolve(path)
        except PathGuardError as exc:
            return f"Error: {exc}"
        if not target.exists():
            return f"Error: file not found: {path}"
        if not target.is_file():
            return f"Error: not a file: {path}"
        size = target.stat().st_size
        if size > ctx.max_read_file_bytes:
            return f"Error: file too large ({size} bytes, max {ctx.max_read_file_bytes})"
        try:
            content = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return f"Error: file is not valid UTF-8 text: {path}"
        return _truncate(content, ctx.max_output_chars)

    @tool
    def list_directory(path: str = ".") -> str:
        """List files and directories under the agent workspace. Path is relative to workspace root."""
        try:
            target = guard.resolve(path)
        except PathGuardError as exc:
            return f"Error: {exc}"
        if not target.exists():
            return f"Error: directory not found: {path}"
        if not target.is_dir():
            return f"Error: not a directory: {path}"
        entries: list[str] = []
        for item in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            suffix = "/" if item.is_dir() else ""
            entries.append(f"{item.name}{suffix}")
        if not entries:
            return "(empty directory)"
        return _truncate("\n".join(entries), ctx.max_output_chars)

    tools: list[BaseTool] = [read_file, list_directory]

    if ctx.allow_write:

        @tool
        def write_file(path: str, content: str) -> str:
            """Write UTF-8 text to a file under the agent workspace. Creates parent directories if needed."""
            try:
                target = guard.resolve(path)
            except PathGuardError as exc:
                return f"Error: {exc}"
            if target.exists() and target.is_dir():
                return f"Error: path is a directory: {path}"
            target.parent.mkdir(parents=True, exist_ok=True)
            if len(content.encode("utf-8")) > ctx.max_read_file_bytes:
                return f"Error: content too large (max {ctx.max_read_file_bytes} bytes)"
            target.write_text(content, encoding="utf-8")
            return f"Wrote {len(content)} chars to {path}"

        tools.append(write_file)

    return tools
