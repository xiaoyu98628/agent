from datetime import UTC, datetime

from app.application.support.ids import new_id
from app.domain.conversation.entity import Conversation, Message
from app.domain.conversation.repository import ConversationRepository
from app.infrastructure.storage.sqlite.database import get_connection


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _format_dt(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()


def _row_to_conversation(row) -> Conversation:
    return Conversation(
        id=row["id"],
        workspace_id=row["workspace_id"],
        title=row["title"],
        model_provider=row["model_provider"],
        model_name=row["model_name"],
        temperature=row["temperature"],
        max_tokens=row["max_tokens"],
        created_at=_parse_dt(row["created_at"]),
        updated_at=_parse_dt(row["updated_at"]),
    )


def _row_to_message(row) -> Message:
    return Message(
        id=row["id"],
        conversation_id=row["conversation_id"],
        role=row["role"],
        content=row["content"],
        created_at=_parse_dt(row["created_at"]),
    )


class SqliteConversationRepository(ConversationRepository):
    async def create(self, conversation: Conversation) -> Conversation:
        conn = await get_connection()
        await conn.execute(
            """
            INSERT INTO conversations (
                id, workspace_id, title, model_provider, model_name,
                temperature, max_tokens, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conversation.id,
                conversation.workspace_id,
                conversation.title,
                conversation.model_provider,
                conversation.model_name,
                conversation.temperature,
                conversation.max_tokens,
                _format_dt(conversation.created_at),
                _format_dt(conversation.updated_at),
            ),
        )
        await conn.commit()
        return conversation

    async def get(self, *, conversation_id: str, workspace_id: str) -> Conversation | None:
        conn = await get_connection()
        cursor = await conn.execute(
            "SELECT * FROM conversations WHERE id = ? AND workspace_id = ?",
            (conversation_id, workspace_id),
        )
        row = await cursor.fetchone()
        return _row_to_conversation(row) if row else None

    async def list_by_workspace(
        self,
        *,
        workspace_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Conversation]:
        conn = await get_connection()
        cursor = await conn.execute(
            """
            SELECT * FROM conversations
            WHERE workspace_id = ?
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
            """,
            (workspace_id, limit, offset),
        )
        rows = await cursor.fetchall()
        return [_row_to_conversation(row) for row in rows]

    async def update_model(
        self,
        *,
        conversation_id: str,
        workspace_id: str,
        model_provider: str,
        model_name: str,
        temperature: float | None,
        max_tokens: int | None,
    ) -> None:
        conn = await get_connection()
        now = _format_dt(datetime.now(UTC))
        await conn.execute(
            """
            UPDATE conversations
            SET model_provider = ?, model_name = ?, temperature = ?, max_tokens = ?, updated_at = ?
            WHERE id = ? AND workspace_id = ?
            """,
            (model_provider, model_name, temperature, max_tokens, now, conversation_id, workspace_id),
        )
        await conn.commit()

    async def update_title(self, *, conversation_id: str, workspace_id: str, title: str) -> None:
        conn = await get_connection()
        now = _format_dt(datetime.now(UTC))
        await conn.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ? AND workspace_id = ?",
            (title, now, conversation_id, workspace_id),
        )
        await conn.commit()

    async def delete(self, *, conversation_id: str, workspace_id: str) -> bool:
        conn = await get_connection()
        cursor = await conn.execute(
            "DELETE FROM conversations WHERE id = ? AND workspace_id = ?",
            (conversation_id, workspace_id),
        )
        await conn.commit()
        return cursor.rowcount > 0

    async def add_message(self, message: Message) -> Message:
        conn = await get_connection()
        now = _format_dt(datetime.now(UTC))
        await conn.execute(
            """
            INSERT INTO messages (id, conversation_id, role, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                message.id,
                message.conversation_id,
                message.role,
                message.content,
                _format_dt(message.created_at),
            ),
        )
        await conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, message.conversation_id),
        )
        await conn.commit()
        return message

    async def list_messages(self, *, conversation_id: str) -> list[Message]:
        conn = await get_connection()
        cursor = await conn.execute(
            """
            SELECT * FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
            """,
            (conversation_id,),
        )
        rows = await cursor.fetchall()
        return [_row_to_message(row) for row in rows]


def new_message(*, conversation_id: str, role: str, content: str) -> Message:
    return Message(
        id=new_id(),
        conversation_id=conversation_id,
        role=role,
        content=content,
        created_at=datetime.now(UTC),
    )
