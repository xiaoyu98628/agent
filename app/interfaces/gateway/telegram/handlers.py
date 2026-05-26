import logging

from app.application.chat.service import ChatService
from app.application.gateway.service import GatewaySessionService
from app.application.support.text import sanitize_text
from app.domain.exceptions import DomainError
from app.domain.gateway.exceptions import UnauthorizedGatewayChatError
from config.config import config

logger = logging.getLogger(__name__)

TELEGRAM_MAX_MESSAGE_LEN = 4096
HELP_TEXT = (
    "Agent Telegram Gateway\n\n"
    "Commands:\n"
    "/start — welcome\n"
    "/help — this help\n"
    "/new — start a new conversation\n"
    "/conv — show current conversation id\n\n"
    "Send any text message to chat with the agent."
)


def _preview_text(text: str, *, limit: int = TELEGRAM_MAX_MESSAGE_LEN) -> str:
    cleaned = text.strip()
    if len(cleaned) <= limit:
        return cleaned or "…"
    return cleaned[: limit - 1] + "…"


def split_telegram_text(text: str, *, limit: int = TELEGRAM_MAX_MESSAGE_LEN) -> list[str]:
    cleaned = sanitize_text(text).strip()
    if not cleaned:
        return ["(empty reply)"]
    if len(cleaned) <= limit:
        return [cleaned]

    chunks: list[str] = []
    current = cleaned
    while current:
        if len(current) <= limit:
            chunks.append(current)
            break
        split_at = current.rfind("\n", 0, limit)
        if split_at <= 0:
            split_at = limit
        chunks.append(current[:split_at].rstrip())
        current = current[split_at:].lstrip()
    return chunks


async def handle_telegram_text(
    *,
    chat_id: int,
    text: str,
    reply,
    send_action,
    chat_service: ChatService,
    session_service: GatewaySessionService,
) -> None:
    platform = GatewaySessionService.PLATFORM_TELEGRAM
    external_chat_id = str(chat_id)

    try:
        session_service.ensure_chat_allowed(platform=platform, chat_id=chat_id)
    except UnauthorizedGatewayChatError as exc:
        await reply(str(exc))
        return

    command = text.strip().split()[0].lower() if text.strip().startswith("/") else ""
    match command:
        case "/start" | "/help":
            await reply(HELP_TEXT)
            return
        case "/new":
            await session_service.reset_conversation(platform=platform, external_chat_id=external_chat_id)
            await reply("Started a new conversation.")
            return
        case "/conv":
            conversation_id = await session_service.resolve_conversation_id(
                platform=platform,
                external_chat_id=external_chat_id,
            )
            await reply(conversation_id or "(none yet)")
            return
        case cmd if cmd.startswith("/"):
            await reply(f"Unknown command: {cmd}. Send /help for commands.")
            return

    telegram_cfg = config().gateway.telegram
    conversation_id = await session_service.resolve_conversation_id(
        platform=platform,
        external_chat_id=external_chat_id,
    )

    await send_action()
    try:
        if telegram_cfg.stream_replies:
            reply_text, resolved_conversation_id = await _stream_reply(
                message=text,
                conversation_id=conversation_id,
                chat_service=chat_service,
                reply=reply,
                edit_interval=telegram_cfg.stream_edit_interval_chars,
            )
        else:
            result = await chat_service.send_message(message=text, conversation_id=conversation_id)
            reply_text = result.reply
            resolved_conversation_id = result.conversation_id
            for chunk in split_telegram_text(reply_text):
                await reply(chunk)

        if resolved_conversation_id:
            await session_service.bind_conversation(
                platform=platform,
                external_chat_id=external_chat_id,
                conversation_id=resolved_conversation_id,
            )
    except DomainError as exc:
        await reply(f"Error: {exc}")
    except Exception:
        logger.exception("telegram chat failed", extra={"chat_id": chat_id})
        await reply("Error: agent request failed.")


async def _stream_reply(
    *,
    message: str,
    conversation_id: str | None,
    chat_service: ChatService,
    reply,
    edit_interval: int,
) -> tuple[str, str | None]:
    placeholder = await reply("…")
    parts: list[str] = []
    last_edit_len = 0
    resolved_conversation_id = conversation_id

    async for event in chat_service.stream_message(message=message, conversation_id=conversation_id):
        match event.event:
            case "delta":
                content = event.data.get("content", "")
                if content:
                    parts.append(content)
                    current = sanitize_text("".join(parts))
                    if len(current) - last_edit_len >= edit_interval:
                        await placeholder.edit_text(_preview_text(current))
                        last_edit_len = len(current)
            case "done":
                resolved_conversation_id = event.data.get("conversation_id", resolved_conversation_id)
                reply_text = sanitize_text(event.data.get("reply") or "".join(parts))
                for index, chunk in enumerate(split_telegram_text(reply_text)):
                    if index == 0:
                        await placeholder.edit_text(chunk)
                    else:
                        await reply(chunk)
                return reply_text, resolved_conversation_id

    fallback = sanitize_text("".join(parts))
    if fallback:
        await placeholder.edit_text(fallback)
    return fallback, resolved_conversation_id
