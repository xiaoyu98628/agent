from datetime import UTC, datetime

from app.domain.memory.entity import MemoryEntry, MemoryTarget
from app.domain.memory.repository import MemoryRepository
from app.infrastructure.storage.sqlite.database import get_connection


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _format_dt(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()


def _row_to_entry(row) -> MemoryEntry:
    return MemoryEntry(
        id=row["id"],
        workspace_id=row["workspace_id"],
        target=row["target"],
        content=row["content"],
        created_at=_parse_dt(row["created_at"]),
        updated_at=_parse_dt(row["updated_at"]),
    )


class SqliteMemoryRepository(MemoryRepository):
    async def list_entries(self, *, workspace_id: str, target: MemoryTarget | None = None) -> list[MemoryEntry]:
        conn = await get_connection()
        if target:
            cursor = await conn.execute(
                """
                SELECT * FROM memory_entries
                WHERE workspace_id = ? AND target = ?
                ORDER BY updated_at ASC
                """,
                (workspace_id, target),
            )
        else:
            cursor = await conn.execute(
                """
                SELECT * FROM memory_entries
                WHERE workspace_id = ?
                ORDER BY target ASC, updated_at ASC
                """,
                (workspace_id,),
            )
        rows = await cursor.fetchall()
        return [_row_to_entry(row) for row in rows]

    async def add_entry(self, entry: MemoryEntry) -> MemoryEntry:
        conn = await get_connection()
        await conn.execute(
            """
            INSERT INTO memory_entries (id, workspace_id, target, content, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                entry.id,
                entry.workspace_id,
                entry.target,
                entry.content,
                _format_dt(entry.created_at),
                _format_dt(entry.updated_at),
            ),
        )
        await conn.commit()
        return entry

    async def update_entry(self, entry: MemoryEntry) -> MemoryEntry:
        conn = await get_connection()
        await conn.execute(
            """
            UPDATE memory_entries SET content = ?, updated_at = ?
            WHERE id = ? AND workspace_id = ?
            """,
            (entry.content, _format_dt(entry.updated_at), entry.id, entry.workspace_id),
        )
        await conn.commit()
        return entry

    async def delete_entry(self, *, entry_id: str, workspace_id: str) -> bool:
        conn = await get_connection()
        cursor = await conn.execute(
            "DELETE FROM memory_entries WHERE id = ? AND workspace_id = ?",
            (entry_id, workspace_id),
        )
        await conn.commit()
        return cursor.rowcount > 0

    async def find_by_content_substring(
        self,
        *,
        workspace_id: str,
        target: MemoryTarget,
        substring: str,
    ) -> list[MemoryEntry]:
        entries = await self.list_entries(workspace_id=workspace_id, target=target)
        return [entry for entry in entries if substring in entry.content]

    async def total_chars(self, *, workspace_id: str, target: MemoryTarget) -> int:
        entries = await self.list_entries(workspace_id=workspace_id, target=target)
        return sum(len(entry.content) for entry in entries)
