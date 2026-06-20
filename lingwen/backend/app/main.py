"""FastAPI application entry point for the Lingwen intelligent query engine."""

import logging
import os

from fastapi import FastAPI

from app.config import settings
from app.api.router import api_router
from app.middleware.cors import setup_cors
from app.middleware.logging_middleware import LoggingMiddleware

logger = logging.getLogger(__name__)

# ---- Logging setup: write to file with UTF-8 encoding ----
_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(_LOG_DIR, exist_ok=True)
_LOG_FILE = os.path.join(_LOG_DIR, "lingwen.log")

_file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8", mode="a")
_file_handler.setLevel(logging.DEBUG)
_file_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))

# Attach to root logger so ALL loggers (including pipeline nodes) write to file
_root_logger = logging.getLogger()
_root_logger.setLevel(logging.DEBUG)
_root_logger.addHandler(_file_handler)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title="天府一网监 API",
        version="0.1.0",
        description="天府一网监智能问数引擎 — API 服务",
    )

    # CORS middleware
    setup_cors(app)

    # Request logging middleware
    app.add_middleware(LoggingMiddleware)

    # Mount API routes
    app.include_router(api_router)

    # Startup event: ensure ChromaDB data directory exists
    @app.on_event("startup")
    async def startup_event() -> None:
        os.makedirs(settings.chroma_dir, exist_ok=True)
        logger.info(
            "ChromaDB data directory ensured: %s",
            os.path.abspath(settings.chroma_dir),
        )
        logger.info("Lingwen API started successfully")

    # Health check endpoint
    @app.get("/api/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
