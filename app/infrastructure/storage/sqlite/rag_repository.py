import json
from datetime import UTC, datetime

from app.domain.knowledge.entity import Document, DocumentChunk, KnowledgeBase
from app.domain.knowledge.repository import RagRepository
from app.infrastructure.storage.sqlite.database import get_connection


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _format_dt(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()


def _row_to_kb(row) -> KnowledgeBase:
    return KnowledgeBase(
        id=row["id"],
        workspace_id=row["workspace_id"],
        name=row["name"],
        description=row["description"],
        created_at=_parse_dt(row["created_at"]),
        updated_at=_parse_dt(row["updated_at"]),
    )


def _row_to_document(row) -> Document:
    return Document(
        id=row["id"],
        knowledge_base_id=row["knowledge_base_id"],
        workspace_id=row["workspace_id"],
        title=row["title"],
        source=row["source"],
        status=row["status"],
        chunk_count=row["chunk_count"],
        created_at=_parse_dt(row["created_at"]),
        updated_at=_parse_dt(row["updated_at"]),
    )


def _row_to_chunk(row) -> DocumentChunk:
    return DocumentChunk(
        id=row["id"],
        document_id=row["document_id"],
        knowledge_base_id=row["knowledge_base_id"],
        workspace_id=row["workspace_id"],
        chunk_index=row["chunk_index"],
        content=row["content"],
        embedding=json.loads(row["embedding_json"]),
        created_at=_parse_dt(row["created_at"]),
    )


class SqliteRagRepository(RagRepository):
    async def create_knowledge_base(self, kb: KnowledgeBase) -> KnowledgeBase:
        conn = await get_connection()
        await conn.execute(
            """
            INSERT INTO knowledge_bases (id, workspace_id, name, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (kb.id, kb.workspace_id, kb.name, kb.description, _format_dt(kb.created_at), _format_dt(kb.updated_at)),
        )
        await conn.commit()
        return kb

    async def get_knowledge_base(self, *, kb_id: str, workspace_id: str) -> KnowledgeBase | None:
        conn = await get_connection()
        cursor = await conn.execute(
            "SELECT * FROM knowledge_bases WHERE id = ? AND workspace_id = ?",
            (kb_id, workspace_id),
        )
        row = await cursor.fetchone()
        return _row_to_kb(row) if row else None

    async def list_knowledge_bases(self, *, workspace_id: str, limit: int, offset: int) -> list[KnowledgeBase]:
        conn = await get_connection()
        cursor = await conn.execute(
            """
            SELECT * FROM knowledge_bases
            WHERE workspace_id = ?
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
            """,
            (workspace_id, limit, offset),
        )
        rows = await cursor.fetchall()
        return [_row_to_kb(row) for row in rows]

    async def delete_knowledge_base(self, *, kb_id: str, workspace_id: str) -> bool:
        conn = await get_connection()
        cursor = await conn.execute(
            "DELETE FROM knowledge_bases WHERE id = ? AND workspace_id = ?",
            (kb_id, workspace_id),
        )
        await conn.commit()
        return cursor.rowcount > 0

    async def create_document(self, document: Document) -> Document:
        conn = await get_connection()
        await conn.execute(
            """
            INSERT INTO documents (
                id, knowledge_base_id, workspace_id, title, source, status, chunk_count, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document.id,
                document.knowledge_base_id,
                document.workspace_id,
                document.title,
                document.source,
                document.status,
                document.chunk_count,
                _format_dt(document.created_at),
                _format_dt(document.updated_at),
            ),
        )
        now = _format_dt(datetime.now(UTC))
        await conn.execute(
            "UPDATE knowledge_bases SET updated_at = ? WHERE id = ?",
            (now, document.knowledge_base_id),
        )
        await conn.commit()
        return document

    async def get_document(self, *, document_id: str, workspace_id: str) -> Document | None:
        conn = await get_connection()
        cursor = await conn.execute(
            "SELECT * FROM documents WHERE id = ? AND workspace_id = ?",
            (document_id, workspace_id),
        )
        row = await cursor.fetchone()
        return _row_to_document(row) if row else None

    async def update_document_status(
        self,
        *,
        document_id: str,
        workspace_id: str,
        status: str,
        chunk_count: int,
    ) -> None:
        conn = await get_connection()
        now = _format_dt(datetime.now(UTC))
        await conn.execute(
            """
            UPDATE documents SET status = ?, chunk_count = ?, updated_at = ?
            WHERE id = ? AND workspace_id = ?
            """,
            (status, chunk_count, now, document_id, workspace_id),
        )
        await conn.commit()

    async def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        if not chunks:
            return
        conn = await get_connection()
        await conn.executemany(
            """
            INSERT INTO document_chunks (
                id, document_id, knowledge_base_id, workspace_id, chunk_index, content, embedding_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    chunk.id,
                    chunk.document_id,
                    chunk.knowledge_base_id,
                    chunk.workspace_id,
                    chunk.chunk_index,
                    chunk.content,
                    json.dumps(chunk.embedding),
                    _format_dt(chunk.created_at),
                )
                for chunk in chunks
            ],
        )
        await conn.commit()

    async def list_chunks_for_kb(self, *, knowledge_base_id: str, workspace_id: str) -> list[DocumentChunk]:
        conn = await get_connection()
        cursor = await conn.execute(
            """
            SELECT * FROM document_chunks
            WHERE knowledge_base_id = ? AND workspace_id = ?
            """,
            (knowledge_base_id, workspace_id),
        )
        rows = await cursor.fetchall()
        return [_row_to_chunk(row) for row in rows]

    async def delete_document(self, *, document_id: str, workspace_id: str) -> bool:
        conn = await get_connection()
        await conn.execute(
            "DELETE FROM document_chunks WHERE document_id = ? AND workspace_id = ?",
            (document_id, workspace_id),
        )
        cursor = await conn.execute(
            "DELETE FROM documents WHERE id = ? AND workspace_id = ?",
            (document_id, workspace_id),
        )
        await conn.commit()
        return cursor.rowcount > 0
