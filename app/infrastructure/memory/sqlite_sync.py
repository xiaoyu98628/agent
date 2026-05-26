import sqlite3
from datetime import UTC, datetime

from app.application.support.ids import new_id
from app.domain.memory.entity import MemoryEntry, MemoryTarget
from app.domain.memory.exceptions import MemoryAmbiguousMatchError, MemoryEntryNotFoundError, MemoryLimitExceededError
from config.config import config


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def sync_list_entries(*, workspace_id: str, target: MemoryTarget | None = None) -> list[MemoryEntry]:
    configure = config()
    conn = sqlite3.connect(configure.storage.sqlite_file)
    conn.row_factory = sqlite3.Row
    try:
        if target:
            rows = conn.execute(
                """
                SELECT * FROM memory_entries
                WHERE workspace_id = ? AND target = ?
                ORDER BY updated_at ASC
                """,
                (workspace_id, target),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM memory_entries
                WHERE workspace_id = ?
                ORDER BY target ASC, updated_at ASC
                """,
                (workspace_id,),
            ).fetchall()
        return [_row_to_entry(row) for row in rows]
    finally:
        conn.close()


def sync_format_snapshot(*, workspace_id: str) -> str:
    configure = config()
    if not configure.memory.enabled:
        return ""

    parts: list[str] = []
    memory_entries = sync_list_entries(workspace_id=workspace_id, target="memory")
    if memory_entries:
        body = configure.memory.entry_separator.join(item.content for item in memory_entries)
        parts.append(f"## Agent Memory\n{body}")

    if configure.memory.user_profile_enabled:
        user_entries = sync_list_entries(workspace_id=workspace_id, target="user")
        if user_entries:
            body = configure.memory.entry_separator.join(item.content for item in user_entries)
            parts.append(f"## User Profile\n{body}")

    return "\n\n".join(parts)


def sync_handle_memory_tool(
    *,
    action: str,
    target: str,
    content: str | None = None,
    old_text: str | None = None,
) -> str:
    configure = config()
    if not configure.memory.enabled:
        return "Memory is disabled."

    workspace_id = configure.storage.default_workspace_id
    action_norm = action.strip().lower()
    target_norm = target.strip().lower()
    if target_norm not in {"memory", "user"}:
        return "Error: target must be 'memory' or 'user'."
    if target_norm == "user" and not configure.memory.user_profile_enabled:
        return "Error: user profile memory is disabled."

    match action_norm:
        case "add":
            if not content or not content.strip():
                return "Error: content is required for add."
            try:
                return _sync_add(workspace_id=workspace_id, target=target_norm, content=content.strip())
            except MemoryLimitExceededError as exc:
                return f"Error: {exc}"
        case "replace":
            if not old_text or not content:
                return "Error: old_text and content are required for replace."
            try:
                return _sync_replace(
                    workspace_id=workspace_id,
                    target=target_norm,
                    old_text=old_text,
                    content=content.strip(),
                )
            except (MemoryEntryNotFoundError, MemoryAmbiguousMatchError, MemoryLimitExceededError) as exc:
                return f"Error: {exc}"
        case "remove":
            if not old_text:
                return "Error: old_text is required for remove."
            try:
                return _sync_remove(workspace_id=workspace_id, target=target_norm, old_text=old_text)
            except (MemoryEntryNotFoundError, MemoryAmbiguousMatchError) as exc:
                return f"Error: {exc}"
        case _:
            return "Error: action must be add, replace, or remove."


def _sync_add(*, workspace_id: str, target: MemoryTarget, content: str) -> str:
    configure = config()
    limit = _char_limit(target)
    current = _sync_total_chars(workspace_id=workspace_id, target=target)
    if current + len(content) > limit:
        raise MemoryLimitExceededError(f"Memory limit exceeded for {target} ({limit} chars)")

    now = _now_iso()
    entry_id = new_id()
    conn = sqlite3.connect(configure.storage.sqlite_file)
    try:
        conn.execute(
            """
            INSERT INTO memory_entries (id, workspace_id, target, content, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (entry_id, workspace_id, target, content, now, now),
        )
        conn.commit()
    finally:
        conn.close()
    return f"Added memory entry to {target}."


def _sync_replace(*, workspace_id: str, target: MemoryTarget, old_text: str, content: str) -> str:
    matches = _sync_find_substring(workspace_id=workspace_id, target=target, substring=old_text)
    if not matches:
        raise MemoryEntryNotFoundError("No matching memory entry found.")
    if len(matches) > 1:
        raise MemoryAmbiguousMatchError("Multiple entries match old_text; be more specific.")

    entry = matches[0]
    configure = config()
    limit = _char_limit(target)
    current = _sync_total_chars(workspace_id=workspace_id, target=target)
    delta = len(content) - len(entry.content)
    if current + delta > limit:
        raise MemoryLimitExceededError(f"Memory limit exceeded for {target} ({limit} chars)")

    now = _now_iso()
    conn = sqlite3.connect(configure.storage.sqlite_file)
    try:
        conn.execute(
            "UPDATE memory_entries SET content = ?, updated_at = ? WHERE id = ? AND workspace_id = ?",
            (content, now, entry.id, workspace_id),
        )
        conn.commit()
    finally:
        conn.close()
    return f"Updated memory entry in {target}."


def _sync_remove(*, workspace_id: str, target: MemoryTarget, old_text: str) -> str:
    matches = _sync_find_substring(workspace_id=workspace_id, target=target, substring=old_text)
    if not matches:
        raise MemoryEntryNotFoundError("No matching memory entry found.")
    if len(matches) > 1:
        raise MemoryAmbiguousMatchError("Multiple entries match old_text; be more specific.")

    configure = config()
    conn = sqlite3.connect(configure.storage.sqlite_file)
    try:
        conn.execute(
            "DELETE FROM memory_entries WHERE id = ? AND workspace_id = ?",
            (matches[0].id, workspace_id),
        )
        conn.commit()
    finally:
        conn.close()
    return f"Removed memory entry from {target}."


def _sync_find_substring(*, workspace_id: str, target: MemoryTarget, substring: str) -> list[MemoryEntry]:
    entries = sync_list_entries(workspace_id=workspace_id, target=target)
    return [entry for entry in entries if substring in entry.content]


def _sync_total_chars(*, workspace_id: str, target: MemoryTarget) -> int:
    return sum(len(entry.content) for entry in sync_list_entries(workspace_id=workspace_id, target=target))


def _char_limit(target: MemoryTarget) -> int:
    configure = config()
    return configure.memory.user_char_limit if target == "user" else configure.memory.memory_char_limit


def _row_to_entry(row: sqlite3.Row) -> MemoryEntry:
    return MemoryEntry(
        id=row["id"],
        workspace_id=row["workspace_id"],
        target=row["target"],
        content=row["content"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )
