import asyncio
import logging
import signal

from telegram.ext import Application

from app.application.chat.service import ChatService
from app.application.gateway.service import GatewaySessionService
from app.interfaces.gateway.telegram.bot import build_telegram_application
from config.config import config

logger = logging.getLogger(__name__)


async def run_telegram_polling(
    *,
    chat_service: ChatService | None = None,
    session_service: GatewaySessionService | None = None,
) -> None:
    telegram_cfg = config().gateway.telegram
    if not telegram_cfg.enabled:
        raise RuntimeError("GATEWAY_TELEGRAM_ENABLED is false.")
    if not telegram_cfg.bot_token:
        raise RuntimeError("GATEWAY_TELEGRAM_BOT_TOKEN is required.")

    application = build_telegram_application(chat_service=chat_service, session_service=session_service)
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _request_stop() -> None:
        logger.info("telegram gateway stopping")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _request_stop)

    logger.info("telegram gateway starting (polling)")
    async with application:
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)
        logger.info("telegram gateway running")
        await stop_event.wait()
        await application.updater.stop()
    logger.info("telegram gateway stopped")
