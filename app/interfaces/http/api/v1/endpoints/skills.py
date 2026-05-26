from fastapi import APIRouter, Depends

from app.application.memory.service import MemoryService
from app.application.skill.service import SkillService
from app.interfaces.http.deps.memory_skill import get_memory_service, get_skill_service
from app.interfaces.http.presenters.memory_skill import to_memory_entry, to_skill_detail, to_skill_response
from app.interfaces.http.schemas.requests.memory_skill import CreateMemoryEntryRequest, UpsertSkillRequest
from app.interfaces.http.schemas.responses.memory_skill import MemoryEntryResponse, MemorySnapshotResponse, SkillDetailResponse, SkillResponse
from app.interfaces.http.support.response.code.success_code import SuccessCode
from app.interfaces.http.support.response.json import JsonResponse

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("", summary="技能列表")
async def list_skills(service: SkillService = Depends(get_skill_service)) -> JsonResponse[list[SkillResponse]]:
    items = service.list_skills()
    return JsonResponse.success(data=[to_skill_response(item) for item in items])


@router.get("/{name}", summary="技能详情")
async def get_skill(name: str, service: SkillService = Depends(get_skill_service)) -> JsonResponse[SkillDetailResponse]:
    content = service.get_skill(name)
    return JsonResponse.success(data=to_skill_detail(content))


@router.put("/{name}", summary="创建或更新技能")
async def upsert_skill(
    name: str,
    body: UpsertSkillRequest,
    service: SkillService = Depends(get_skill_service),
) -> JsonResponse[SkillResponse]:
    skill = service.upsert_skill(
        name=name or body.name,
        description=body.description,
        body=body.body,
        category=body.category,
    )
    return JsonResponse.success(data=to_skill_response(skill), code=SuccessCode.SUCCESS_CREATED)
