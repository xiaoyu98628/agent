from app.application.dto.chat import ChatRequest, ChatResponse
from app.application.ports.chat_model import ChatModelPort
from app.infrastructure.model.model_router import ModelRouter


class ChatModelGateway(ChatModelPort):
    def __init__(self, router: ModelRouter):
        self.router = router

    async def complete(self, request: ChatRequest) -> ChatResponse:
        return await self.router.complete(request)
