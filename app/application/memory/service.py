from datetime import UTC, datetime

from app.application.support.ids import new_id
from app.domain.memory.entity import MemoryEntry, MemoryTarget
from app.domain.memory.exceptions import (
    MemoryAmbiguousMatchError,
    MemoryEntryNotFoundError,
    MemoryLimitExceededError,
)
from app.domain.memory.repository import MemoryRepository
from app.infrastructure.memory.sqlite_sync import sync_format_snapshot
from app.infrastructure.storage.sqlite.memory_repository import SqliteMemoryRepository
from config.config import config


def _now() -> datetime:
    return datetime.now(UTC)


class MemoryService:
    def __init__(self, repository: MemoryRepository | None = None) -> None:
        self._repository = repository or SqliteMemoryRepository()
        self._snapshot_cache: str | None = None

    @property
    def workspace_id(self) -> str:
        return config().storage.default_workspace_id

    def format_snapshot_block(self) -> str:
        configure = config()
        if not configure.memory.enabled:
            return ""
        if self._snapshot_cache is None:
            self._snapshot_cache = sync_format_snapshot(workspace_id=self.workspace_id)
        return self._snapshot_cache

    def invalidate_snapshot(self) -> None:
        self._snapshot_cache = None

    async def list_entries(self, *, target: MemoryTarget | None = None) -> list[MemoryEntry]:
        return await self._repository.list_entries(workspace_id=self.workspace_id, target=target)

    async def add_entry(self, *, target: MemoryTarget, content: str) -> MemoryEntry:
        await self._ensure_limit(target=target, extra_chars=len(content))
        now = _now()
        entry = MemoryEntry(
            id=new_id(),
            workspace_id=self.workspace_id,
            target=target,
            content=content.strip(),
            created_at=now,
            updated_at=now,
        )
        saved = await self._repository.add_entry(entry)
        self.invalidate_snapshot()
        return saved

    async def delete_entry(self, entry_id: str) -> None:
        deleted = await self._repository.delete_entry(entry_id=entry_id, workspace_id=self.workspace_id)
        if not deleted:
            raise MemoryEntryNotFoundError(f"Memory entry not found: {entry_id}")
        self.invalidate_snapshot()

    async def _ensure_limit(self, *, target: MemoryTarget, extra_chars: int) -> None:
        configure = config()
        limit = configure.memory.user_char_limit if target == "user" else configure.memory.memory_char_limit
        current = await self._repository.total_chars(workspace_id=self.workspace_id, target=target)
        if current + extra_chars > limit:
            raise MemoryLimitExceededError(f"Memory limit exceeded for {target} ({limit} chars)")

    async def replace_entry(self, *, target: MemoryTarget, old_text: str, content: str) -> MemoryEntry:
        matches = await self._repository.find_by_content_substring(
            workspace_id=self.workspace_id,
            target=target,
            substring=old_text,
        )
        if not matches:
            raise MemoryEntryNotFoundError("No matching memory entry found.")
        if len(matches) > 1:
            raise MemoryAmbiguousMatchError("Multiple entries match old_text; be more specific.")

        entry = matches[0]
        delta = len(content) - len(entry.content)
        await self._ensure_limit(target=target, extra_chars=delta)
        updated = MemoryEntry(
            id=entry.id,
            workspace_id=entry.workspace_id,
            target=entry.target,
            content=content.strip(),
            created_at=entry.created_at,
            updated_at=_now(),
        )
        saved = await self._repository.update_entry(updated)
        self.invalidate_snapshot()
        return saved

    async def remove_by_substring(self, *, target: MemoryTarget, old_text: str) -> None:
        matches = await self._repository.find_by_content_substring(
            workspace_id=self.workspace_id,
            target=target,
            substring=old_text,
        )
        if not matches:
            raise MemoryEntryNotFoundError("No matching memory entry found.")
        if len(matches) > 1:
            raise MemoryAmbiguousMatchError("Multiple entries match old_text; be more specific.")
        await self.delete_entry(matches[0].id)
