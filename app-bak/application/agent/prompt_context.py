from datetime import UTC, datetime
from pathlib import Path

from paths import BASE_DIR

_INVISIBLE_CHARS = frozenset(
    {
        "\u200b",
        "\u200c",
        "\u200d",
        "\u2060",
        "\ufeff",
        "\u202a",
        "\u202b",
        "\u202c",
        "\u202d",
        "\u202e",
    }
)

_THREAT_PATTERNS = (
    "ignore previous instructions",
    "ignore all previous",
    "disregard your",
    "forget your instructions",
    "do not tell the user",
    "system prompt override",
    "<system>",
    "]]>",
    "curl ${",
    "cat .env",
    "cat credentials",
)


def build_runtime_context_prompt(*, cwd: Path | None = None, max_chars: int = 20_000) -> str:
    """Build Hermes-style stable runtime context for the system prompt."""
    cwd_path = (cwd or BASE_DIR).resolve()
    sections: list[str] = []

    project_context = _load_project_context(cwd_path=cwd_path, max_chars=max_chars)
    if project_context:
        sections.append(project_context)

    sections.append(f"Current time: {datetime.now(UTC).isoformat()}")

    if not sections:
        return ""

    return "# Runtime Context\n\n" + "\n\n".join(sections)


def _load_project_context(*, cwd_path: Path, max_chars: int) -> str:
    context = _load_hermes_context(cwd_path=cwd_path, max_chars=max_chars)
    if context:
        return context

    for name in ("AGENTS.md", "CLAUDE.md"):
        context_path = cwd_path / name
        if context_path.is_file():
            return _format_context_file(context_path, max_chars=max_chars)

    cursor_rules = cwd_path / ".cursorrules"
    if cursor_rules.is_file():
        return _format_context_file(cursor_rules, max_chars=max_chars)

    cursor_dir = cwd_path / ".cursor" / "rules"
    if cursor_dir.is_dir():
        sections = [_format_context_file(path, max_chars=max_chars) for path in sorted(cursor_dir.glob("*.mdc")) if path.is_file()]
        if sections:
            return "# Project Context\n\nThe following Cursor rule files have been loaded and should be followed:\n\n" + "\n\n".join(sections)

    return ""


def _load_hermes_context(*, cwd_path: Path, max_chars: int) -> str:
    for directory in _walk_to_git_root(cwd_path):
        for name in (".hermes.md", "HERMES.md"):
            path = directory / name
            if path.is_file():
                return _format_context_file(path, max_chars=max_chars)
    return ""


def _walk_to_git_root(cwd_path: Path) -> list[Path]:
    directories: list[Path] = []
    current = cwd_path
    while True:
        directories.append(current)
        if (current / ".git").exists() or current.parent == current:
            return directories
        current = current.parent


def _format_context_file(path: Path, *, max_chars: int) -> str:
    label = path.name
    try:
        content = path.read_text(encoding="utf-8").strip()
    except UnicodeDecodeError:
        return f"## {label}\n[BLOCKED: file is not valid UTF-8 text.]"
    except OSError as exc:
        return f"## {label}\n[BLOCKED: could not read file: {exc}]"

    blocked = _blocked_reason(content)
    if blocked:
        return f"## {label}\n[BLOCKED: {label} contained potential prompt injection ({blocked}). Content not loaded.]"

    return f"## {label}\n{_truncate(content, label=label, max_chars=max_chars)}"


def _blocked_reason(content: str) -> str:
    lowered = content.lower()
    for char in _INVISIBLE_CHARS:
        if char in content:
            return f"invisible_unicode_u+{ord(char):04x}"
    for pattern in _THREAT_PATTERNS:
        if pattern in lowered:
            return "prompt_injection"
    return ""


def _truncate(content: str, *, label: str, max_chars: int) -> str:
    if len(content) <= max_chars:
        return content

    head_chars = int(max_chars * 0.7)
    tail_chars = int(max_chars * 0.2)
    omitted = len(content) - head_chars - tail_chars
    return (
        content[:head_chars]
        + f"\n\n[...truncated {label}: omitted {omitted} of {len(content)} chars. Use file tools to read the full file.]\n\n"
        + content[-tail_chars:]
    )
