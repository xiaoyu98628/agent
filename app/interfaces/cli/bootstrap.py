from pathlib import Path

from app.infrastructure.logging.manager import configure_logging
from app.infrastructure.storage.sqlite.database import close_db, init_db
from config.config import config
from paths import STORAGE_DIR


async def startup() -> None:
    configure_logging()
    configure = config()
    Path(STORAGE_DIR).mkdir(parents=True, exist_ok=True)
    await init_db(configure.storage.sqlite_file)


async def shutdown() -> None:
    await close_db()
