# /Users/xiaoyu/www/python/works/agent/app/application/ports/chat_model.py

from typing import Protocol

from app.application.dto.chat import ChatRequest, ChatResponse


class ChatModelPort(Protocol):
    async def complete(self, request: ChatRequest) -> ChatResponse:
        ...
