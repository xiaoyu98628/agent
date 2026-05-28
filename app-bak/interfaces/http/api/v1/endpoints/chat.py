from fastapi import APIRouter, Depends

from app.application.chat.service import ChatMessageInput, ChatService
from app.infrastructure.llm.catalog import list_model_options
from app.interfaces.http.deps.chat import get_chat_service
from app.interfaces.http.presenters.chat import to_chat_response
from app.interfaces.http.schemas.requests.chat import ChatRequest
from app.interfaces.http.schemas.responses.chat import ChatResponse, ModelOptionItem, ModelOptionsResponse, ModelSelectionResponse
from app.interfaces.http.support.response.json import JsonResponse
from config.config import config

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", summary="发送对话消息")
async def send_chat_message(
    body: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> JsonResponse[ChatResponse]:
    model_req = body.model
    result = await service.send_message(
        message=body.message,
        conversation_id=body.conversation_id,
        provider=model_req.provider if model_req else None,
        model=model_req.model if model_req else None,
        temperature=model_req.temperature if model_req else None,
        max_tokens=model_req.max_tokens if model_req else None,
        history=[ChatMessageInput(role=m.role, content=m.content) for m in body.history],
    )
    return JsonResponse.success(data=to_chat_response(reply=result.reply, model=result.model, conversation_id=result.conversation_id))


@router.get("/models/options", summary="可选模型列表", include_in_schema=True)
async def get_model_options() -> JsonResponse[ModelOptionsResponse]:
    payload = list_model_options()
    configure = config()
    default = ModelSelectionResponse(
        provider=configure.llm.provider,
        model=configure.llm.model,
        temperature=configure.llm.temperature,
        max_tokens=configure.llm.max_tokens,
    )
    data = ModelOptionsResponse(
        catalog_source=str(payload["catalog_source"]),
        providers=list(payload["providers"]),
        models=[
            ModelOptionItem(
                provider=item.provider,
                model=item.model,
                label=item.label,
                supports_tools=item.supports_tools,
            )
            for item in payload["models"]
        ],
        default=default,
    )
    return JsonResponse.success(data=data)
