from app.domain.gateway.entity import GatewayBinding
from app.domain.gateway.exceptions import UnauthorizedGatewayChatError
from app.domain.gateway.repository import GatewayBindingRepository
from app.infrastructure.storage.sqlite.gateway_repository import SqliteGatewayBindingRepository
from config.config import config


class GatewaySessionService:
    """Gateway 外部 chat 与内部 conversation 的绑定。"""

    PLATFORM_TELEGRAM = "telegram"

    def __init__(self, repository: GatewayBindingRepository | None = None) -> None:
        self._repository = repository or SqliteGatewayBindingRepository()

    @property
    def workspace_id(self) -> str:
        return config().storage.default_workspace_id

    def ensure_chat_allowed(self, *, platform: str, chat_id: int | str) -> None:
        configure = config()
        if platform != self.PLATFORM_TELEGRAM:
            return

        telegram_cfg = configure.gateway.telegram
        if not telegram_cfg.allowed_chat_ids:
            if configure.app.deployment_mode == "server":
                raise UnauthorizedGatewayChatError("Telegram chat is not allowed (empty allowlist in server mode).")
            return

        chat_id_int = int(chat_id)
        if chat_id_int not in telegram_cfg.allowed_chat_ids:
            raise UnauthorizedGatewayChatError(f"Telegram chat {chat_id_int} is not allowed.")

    async def get_binding(self, *, platform: str, external_chat_id: str) -> GatewayBinding | None:
        return await self._repository.get_binding(
            platform=platform,
            external_chat_id=external_chat_id,
            workspace_id=self.workspace_id,
        )

    async def bind_conversation(
        self,
        *,
        platform: str,
        external_chat_id: str,
        conversation_id: str | None,
    ) -> GatewayBinding:
        return await self._repository.upsert_binding(
            platform=platform,
            external_chat_id=external_chat_id,
            workspace_id=self.workspace_id,
            conversation_id=conversation_id,
        )

    async def reset_conversation(self, *, platform: str, external_chat_id: str) -> GatewayBinding:
        return await self.bind_conversation(
            platform=platform,
            external_chat_id=external_chat_id,
            conversation_id=None,
        )

    async def resolve_conversation_id(self, *, platform: str, external_chat_id: str) -> str | None:
        binding = await self.get_binding(platform=platform, external_chat_id=external_chat_id)
        return binding.conversation_id if binding else None
