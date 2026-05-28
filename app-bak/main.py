from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.infrastructure.logging.manager import configure_logging
from app.infrastructure.storage.sqlite.database import close_db, init_db
from app.interfaces.http.handlers.register import register_exception_handlers
from app.interfaces.http.middleware.register import register_middleware
from app.interfaces.http.routers.register import register_route
from config.config import config
from paths import STORAGE_DIR


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure = config()
    Path(STORAGE_DIR).mkdir(parents=True, exist_ok=True)
    await init_db(configure.storage.sqlite_file)
    yield
    await close_db()


def create_app() -> FastAPI:
    """创建 FastAPI 应用。"""
    configure_logging()

    configure = config()

    app = FastAPI(
        title=configure.app.name,
        debug=configure.app.debug,
        lifespan=lifespan,
    )

    register_middleware(app=app)
    register_exception_handlers(app=app)
    register_route(app=app)

    @app.get(path="/health", summary="健康检测")
    async def health():
        return {"message": "ok", "deployment_mode": configure.app.deployment_mode}

    return app


app = create_app()


def main() -> None:
    import uvicorn

    configure = config()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=configure.app.port,
        reload=configure.app.debug,
    )


if __name__ == "__main__":
    main()
