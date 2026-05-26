import json
import logging
import uuid

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from starlette.websockets import WebSocketState

from app.application.chat.service import ChatMessageInput, ChatService
from app.domain.exceptions import DomainError
from app.infrastructure.context.request_scope import get_trace_id, set_trace_id
from app.interfaces.http.deps.chat import get_chat_service
from app.interfaces.http.schemas.requests.chat import ChatRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat-stream"])


@router.get("/info", summary="WebSocket 连接说明")
async def chat_stream_info() -> dict:
    """浏览器查看连接说明；流式对话请 WebSocket 连接 /ws/v1/chat。"""
    return {
        "protocol": "websocket",
        "endpoint": "/ws/v1/chat",
        "usage": "连接后发送一条 JSON，字段同 POST /api/v1/chat 的 ChatRequest",
        "events": ["start", "delta", "done", "error"],
        "example_payload": {
            "message": "你好",
            "model": {"provider": "zhipu", "model": "glm-4.7"},
            "history": [],
        },
    }


@router.websocket("")
async def chat_stream(
    websocket: WebSocket,
    service: ChatService = Depends(get_chat_service),
) -> None:
    await websocket.accept()
    trace_id = get_trace_id()
    if not trace_id or trace_id == "-":
        trace_id = str(uuid.uuid4())
        set_trace_id(trace_id)

    try:
        payload = await websocket.receive_json()
        request = ChatRequest.model_validate(payload)
    except WebSocketDisconnect:
        return
    except ValidationError as error:
        await _send_event(websocket, "error", {"message": str(error), "trace_id": trace_id})
        await _safe_close(websocket, code=1003)
        return
    except Exception as error:
        await _send_event(websocket, "error", {"message": str(error), "trace_id": trace_id})
        await _safe_close(websocket, code=1011)
        return

    model_req = request.model
    try:
        async for item in service.stream_message(
            message=request.message,
            conversation_id=request.conversation_id,
            provider=model_req.provider if model_req else None,
            model=model_req.model if model_req else None,
            temperature=model_req.temperature if model_req else None,
            max_tokens=model_req.max_tokens if model_req else None,
            history=[ChatMessageInput(role=m.role, content=m.content) for m in request.history],
        ):
            data = dict(item.data)
            if item.event == "start":
                data["trace_id"] = trace_id
            if not await _send_event(websocket, item.event, data):
                return
        await _safe_close(websocket)
    except WebSocketDisconnect:
        return
    except DomainError as error:
        if await _send_event(websocket, "error", {"message": str(error), "trace_id": trace_id}):
            await _safe_close(websocket, code=1011)
    except Exception as error:
        logger.exception("websocket chat stream failed", extra={"trace_id": trace_id})
        if await _send_event(websocket, "error", {"message": str(error), "trace_id": trace_id}):
            await _safe_close(websocket, code=1011)


async def _send_event(websocket: WebSocket, event: str, data: dict) -> bool:
    """发送事件；连接已关闭时返回 False。"""
    if websocket.client_state != WebSocketState.CONNECTED:
        return False
    try:
        await websocket.send_text(json.dumps({"event": event, "data": data}, ensure_ascii=False))
        return True
    except WebSocketDisconnect:
        return False
    except RuntimeError:
        return False


async def _safe_close(websocket: WebSocket, *, code: int = 1000) -> None:
    if websocket.client_state != WebSocketState.CONNECTED:
        return
    try:
        await websocket.close(code=code)
    except RuntimeError:
        pass
