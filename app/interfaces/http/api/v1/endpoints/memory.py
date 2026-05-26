from fastapi import APIRouter, Depends

from app.application.memory.service import MemoryService
from app.interfaces.http.deps.memory_skill import get_memory_service
from app.interfaces.http.presenters.memory_skill import to_memory_entry
from app.interfaces.http.schemas.requests.memory_skill import CreateMemoryEntryRequest
from app.interfaces.http.schemas.responses.memory_skill import MemoryEntryResponse, MemorySnapshotResponse
from app.interfaces.http.support.response.code.success_code import SuccessCode
from app.interfaces.http.support.response.json import JsonResponse

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("", summary="记忆快照")
async def get_memory_snapshot(service: MemoryService = Depends(get_memory_service)) -> JsonResponse[MemorySnapshotResponse]:
    memory_entries = await service.list_entries(target="memory")
    user_entries = await service.list_entries(target="user")
    data = MemorySnapshotResponse(
        memory=[to_memory_entry(item) for item in memory_entries],
        user=[to_memory_entry(item) for item in user_entries],
    )
    return JsonResponse.success(data=data)


@router.post("/entries", summary="新增记忆条目")
async def create_memory_entry(
    body: CreateMemoryEntryRequest,
    service: MemoryService = Depends(get_memory_service),
) -> JsonResponse[MemoryEntryResponse]:
    entry = await service.add_entry(target=body.target, content=body.content)
    return JsonResponse.success(data=to_memory_entry(entry), code=SuccessCode.SUCCESS_CREATED)


@router.delete("/entries/{entry_id}", summary="删除记忆条目")
async def delete_memory_entry(
    entry_id: str,
    service: MemoryService = Depends(get_memory_service),
) -> JsonResponse[None]:
    await service.delete_entry(entry_id)
    return JsonResponse.success(data=None, message="deleted")
