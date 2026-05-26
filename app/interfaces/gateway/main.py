import asyncio

from app.interfaces.cli.bootstrap import shutdown, startup
from app.interfaces.gateway.telegram.runner import run_telegram_polling


async def run_gateway() -> None:
    await startup()
    try:
        await run_telegram_polling()
    finally:
        await shutdown()


def main() -> None:
    asyncio.run(run_gateway())


if __name__ == "__main__":
    main()
