from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ToolContext:
    """工具运行时上下文（路径沙箱、输出限制等）。"""

    workspace_root: Path
    allow_write: bool
    dangerous_command_policy: str
    command_timeout_seconds: int
    web_fetch_timeout_seconds: int
    max_output_chars: int
    max_read_file_bytes: int
