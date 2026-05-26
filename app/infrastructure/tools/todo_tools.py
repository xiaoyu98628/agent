import json
import sqlite3
from datetime import UTC, datetime

from langchain_core.tools import BaseTool, tool

from app.application.support.ids import new_id
from config.config import config

_VALID_STATUSES = frozenset({"pending", "done"})


def build_todo_tools() -> list[BaseTool]:
    @tool
    def todo(action: str, content: str | None = None, todo_id: str | None = None, status: str | None = None) -> str:
        """Manage the agent's working todo list. action: add|list|update|remove|clear; status: pending|done."""
        action_norm = action.strip().lower()
        match action_norm:
            case "add":
                if not content or not content.strip():
                    return "Error: content is required for add."
                return _add_todo(content=content.strip())
            case "list":
                return _list_todos(status=status)
            case "update":
                if not todo_id:
                    return "Error: todo_id is required for update."
                return _update_todo(todo_id=todo_id, content=content, status=status)
            case "remove":
                if not todo_id:
                    return "Error: todo_id is required for remove."
                return _remove_todo(todo_id=todo_id)
            case "clear":
                return _clear_done()
            case _:
                return "Error: action must be add, list, update, remove, or clear."

    return [todo]


def _connect() -> sqlite3.Connection:
    configure = config()
    conn = sqlite3.connect(configure.storage.sqlite_file)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_todos (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            content TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_todos_workspace ON agent_todos(workspace_id, status, updated_at DESC)")
    conn.commit()
    return conn


def _workspace_id() -> str:
    return config().storage.default_workspace_id


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _add_todo(*, content: str) -> str:
    todo_id = new_id()
    now = _now_iso()
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO agent_todos (id, workspace_id, content, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (todo_id, _workspace_id(), content, "pending", now, now),
        )
        conn.commit()
    finally:
        conn.close()
    return json.dumps({"id": todo_id, "status": "pending", "content": content}, ensure_ascii=False)


def _list_todos(*, status: str | None) -> str:
    status_norm = status.strip().lower() if status else None
    if status_norm and status_norm not in _VALID_STATUSES:
        return "Error: status must be pending or done."

    conn = _connect()
    try:
        if status_norm:
            rows = conn.execute(
                """
                SELECT * FROM agent_todos
                WHERE workspace_id = ? AND status = ?
                ORDER BY updated_at DESC
                """,
                (_workspace_id(), status_norm),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM agent_todos
                WHERE workspace_id = ?
                ORDER BY status ASC, updated_at DESC
                """,
                (_workspace_id(),),
            ).fetchall()
    finally:
        conn.close()

    payload = [
        {
            "id": row["id"],
            "content": row["content"],
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _update_todo(*, todo_id: str, content: str | None, status: str | None) -> str:
    status_norm = status.strip().lower() if status else None
    if status_norm and status_norm not in _VALID_STATUSES:
        return "Error: status must be pending or done."
    if content is None and status_norm is None:
        return "Error: provide content or status to update."

    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM agent_todos WHERE id = ? AND workspace_id = ?",
            (todo_id, _workspace_id()),
        ).fetchone()
        if row is None:
            return f"Error: todo not found: {todo_id}"
        next_content = content.strip() if content and content.strip() else row["content"]
        next_status = status_norm or row["status"]
        conn.execute(
            """
            UPDATE agent_todos
            SET content = ?, status = ?, updated_at = ?
            WHERE id = ? AND workspace_id = ?
            """,
            (next_content, next_status, _now_iso(), todo_id, _workspace_id()),
        )
        conn.commit()
    finally:
        conn.close()
    return json.dumps({"id": todo_id, "status": next_status, "content": next_content}, ensure_ascii=False)


def _remove_todo(*, todo_id: str) -> str:
    conn = _connect()
    try:
        cursor = conn.execute(
            "DELETE FROM agent_todos WHERE id = ? AND workspace_id = ?",
            (todo_id, _workspace_id()),
        )
        conn.commit()
    finally:
        conn.close()
    if cursor.rowcount <= 0:
        return f"Error: todo not found: {todo_id}"
    return f"Removed todo: {todo_id}"


def _clear_done() -> str:
    conn = _connect()
    try:
        cursor = conn.execute(
            "DELETE FROM agent_todos WHERE workspace_id = ? AND status = ?",
            (_workspace_id(), "done"),
        )
        conn.commit()
    finally:
        conn.close()
    return f"Cleared {cursor.rowcount} done todo(s)."
