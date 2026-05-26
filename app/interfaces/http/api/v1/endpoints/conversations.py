from fastapi import APIRouter, Depends

from app.application.conversation.service import ConversationService
from app.interfaces.http.deps.conversation import get_conversation_service
from app.interfaces.http.presenters.chat import to_conversation_detail, to_conversation_response
from app.interfaces.http.schemas.requests.conversation import ConversationListQuery, CreateConversationRequest
from app.interfaces.http.schemas.responses.conversation import ConversationDetailResponse, ConversationResponse
from app.interfaces.http.support.response.code.success_code import SuccessCode
from app.interfaces.http.support.response.json import JsonResponse

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", summary="创建会话")
async def create_conversation(
    body: CreateConversationRequest,
    service: ConversationService = Depends(get_conversation_service),
) -> JsonResponse[ConversationResponse]:
    model_req = body.model
    conversation = await service.create(
        title=body.title,
        provider=model_req.provider if model_req else None,
        model=model_req.model if model_req else None,
        temperature=model_req.temperature if model_req else None,
        max_tokens=model_req.max_tokens if model_req else None,
    )
    return JsonResponse.success(data=to_conversation_response(conversation), code=SuccessCode.SUCCESS_CREATED)


@router.get("", summary="会话列表")
async def list_conversations(
    query: ConversationListQuery = Depends(),
    service: ConversationService = Depends(get_conversation_service),
) -> JsonResponse[list[ConversationResponse]]:
    items = await service.list_conversations(limit=query.limit, offset=query.offset)
    return JsonResponse.success(data=[to_conversation_response(item) for item in items])


@router.get("/{conversation_id}", summary="会话详情（含消息）")
async def get_conversation(
    conversation_id: str,
    service: ConversationService = Depends(get_conversation_service),
) -> JsonResponse[ConversationDetailResponse]:
    conversation, messages = await service.get_with_messages(conversation_id)
    return JsonResponse.success(data=to_conversation_detail(conversation, messages))


@router.delete("/{conversation_id}", summary="删除会话")
async def delete_conversation(
    conversation_id: str,
    service: ConversationService = Depends(get_conversation_service),
) -> JsonResponse[None]:
    await service.delete(conversation_id)
    return JsonResponse.success(data=None, message="deleted")
