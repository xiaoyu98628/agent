
from app.application.dto.chat import ChatRequest, ChatResponse
from app.application.ports.chat_model import ChatModelPort


class ChatModelGateway(ChatModelPort):
    async def complete(self, request: ChatRequest) -> ChatResponse:
        raise NotImplementedError
