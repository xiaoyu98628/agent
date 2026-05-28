import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from app.application.chat.service import ChatService
from app.application.gateway.service import GatewaySessionService
from app.interfaces.gateway.telegram.handlers import handle_telegram_text
from config.config import config

logger = logging.getLogger(__name__)


def build_telegram_application(
    *,
    chat_service: ChatService | None = None,
    session_service: GatewaySessionService | None = None,
) -> Application:
    telegram_cfg = config().gateway.telegram
    if not telegram_cfg.bot_token:
        raise RuntimeError("GATEWAY_TELEGRAM_BOT_TOKEN is required.")

    chat = chat_service or ChatService()
    sessions = session_service or GatewaySessionService()

    application = Application.builder().token(telegram_cfg.bot_token).build()

    async def _dispatch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.effective_message
        chat_obj = update.effective_chat
        if message is None or chat_obj is None or not message.text:
            return

        async def reply(text: str):
            return await message.reply_text(text)

        async def send_action() -> None:
            await chat_obj.send_action(ChatAction.TYPING)

        await handle_telegram_text(
            chat_id=chat_obj.id,
            text=message.text,
            reply=reply,
            send_action=send_action,
            chat_service=chat,
            session_service=sessions,
        )

    application.add_handler(CommandHandler(["start", "help", "new", "conv"], _dispatch))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _dispatch))
    return application
