from datetime import UTC, datetime

from app.domain.gateway.entity import GatewayBinding
from app.domain.gateway.repository import GatewayBindingRepository
from app.infrastructure.storage.sqlite.database import get_connection


def _now() -> datetime:
    return datetime.now(UTC)


def _format_dt(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _row_to_binding(row) -> GatewayBinding:
    return GatewayBinding(
        platform=row["platform"],
        external_chat_id=row["external_chat_id"],
        workspace_id=row["workspace_id"],
        conversation_id=row["conversation_id"],
        updated_at=_parse_dt(row["updated_at"]),
    )


class SqliteGatewayBindingRepository(GatewayBindingRepository):
    async def get_binding(
        self,
        *,
        platform: str,
        external_chat_id: str,
        workspace_id: str,
    ) -> GatewayBinding | None:
        conn = await get_connection()
        cursor = await conn.execute(
            """
            SELECT * FROM gateway_bindings
            WHERE platform = ? AND external_chat_id = ? AND workspace_id = ?
            """,
            (platform, external_chat_id, workspace_id),
        )
        row = await cursor.fetchone()
        return _row_to_binding(row) if row else None

    async def upsert_binding(
        self,
        *,
        platform: str,
        external_chat_id: str,
        workspace_id: str,
        conversation_id: str | None,
    ) -> GatewayBinding:
        conn = await get_connection()
        now = _format_dt(_now())
        await conn.execute(
            """
            INSERT INTO gateway_bindings (platform, external_chat_id, workspace_id, conversation_id, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(platform, external_chat_id, workspace_id)
            DO UPDATE SET conversation_id = excluded.conversation_id, updated_at = excluded.updated_at
            """,
            (platform, external_chat_id, workspace_id, conversation_id, now),
        )
        await conn.commit()
        binding = await self.get_binding(
            platform=platform,
            external_chat_id=external_chat_id,
            workspace_id=workspace_id,
        )
        assert binding is not None
        return binding
