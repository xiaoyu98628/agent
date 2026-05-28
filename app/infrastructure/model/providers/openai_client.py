from openai import AsyncOpenAI

from app.application.dto.chat import ChatRequest, ChatResponse


class OpenAIClient:
    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        default_temperature: float | None = None,
        max_tokens: int | None = None,
    ):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.default_temperature = default_temperature
        self.max_tokens = max_tokens

    async def complete(self, request: ChatRequest) -> ChatResponse:
        if request.model is None:
            raise ValueError("Model selection is required")

        kwargs = {
            "model": request.model.name,
            "messages": [
                {"role": message.role, "content": message.content}
                for message in request.messages
            ],
        }

        temperature = request.temperature
        if temperature is None:
            temperature = self.default_temperature
        if temperature is not None:
            kwargs["temperature"] = temperature

        if self.max_tokens is not None:
            kwargs["max_tokens"] = self.max_tokens

        response = await self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        return ChatResponse(
            content=choice.message.content or "",
            model=request.model,
            usage=response.usage.model_dump() if response.usage else {},
            raw=response,
        )
