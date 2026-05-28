from typing import Literal, Protocol

from app.domain.memory.entity import MemoryEntry, MemoryTarget


class MemoryRepository(Protocol):
    async def list_entries(self, *, workspace_id: str, target: MemoryTarget | None = None) -> list[MemoryEntry]: ...

    async def add_entry(self, entry: MemoryEntry) -> MemoryEntry: ...

    async def update_entry(self, entry: MemoryEntry) -> MemoryEntry: ...

    async def delete_entry(self, *, entry_id: str, workspace_id: str) -> bool: ...

    async def find_by_content_substring(
        self,
        *,
        workspace_id: str,
        target: MemoryTarget,
        substring: str,
    ) -> list[MemoryEntry]: ...

    async def total_chars(self, *, workspace_id: str, target: MemoryTarget) -> int: ...
