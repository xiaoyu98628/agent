from fastapi import APIRouter

from app.interfaces.http.ws.v1.endpoints import chat_stream

ws_v1_router = APIRouter(prefix="/v1")

ws_v1_router.include_router(chat_stream.router)
