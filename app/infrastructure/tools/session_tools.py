import json
import sqlite3

from langchain_core.tools import BaseTool, tool

from config.config import config


def build_session_tools() -> list[BaseTool]:
    @tool
    def session_search(query: str, limit: int = 5) -> str:
        """Search previous conversation messages in this workspace for relevant context."""
        query_text = query.strip()
        if not query_text:
            return "Error: query is required."

        configure = config()
        workspace_id = configure.storage.default_workspace_id
        limit = max(1, min(limit, 20))
        pattern = f"%{query_text}%"

        conn = sqlite3.connect(configure.storage.sqlite_file)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """
                SELECT
                    c.id AS conversation_id,
                    c.title AS conversation_title,
                    c.updated_at AS conversation_updated_at,
                    m.role,
                    m.content,
                    m.created_at
                FROM messages m
                JOIN conversations c ON c.id = m.conversation_id
                WHERE c.workspace_id = ? AND m.content LIKE ?
                ORDER BY m.created_at DESC
                LIMIT ?
                """,
                (workspace_id, pattern, limit),
            ).fetchall()
        except sqlite3.OperationalError as exc:
            return f"Error: session store is not ready: {exc}"
        finally:
            conn.close()

        if not rows:
            return "No matching session messages found."

        payload = [
            {
                "conversation_id": row["conversation_id"],
                "conversation_title": row["conversation_title"],
                "role": row["role"],
                "content": row["content"],
                "created_at": row["created_at"],
                "conversation_updated_at": row["conversation_updated_at"],
            }
            for row in rows
        ]
        return json.dumps(payload, ensure_ascii=False, indent=2)

    return [session_search]
