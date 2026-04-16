"""FastAPI application for the Noir Canvas pipeline.

CORS origins are loaded from the ALLOWED_ORIGINS environment variable.
All mutation endpoints require X-API-Key authentication (see deps.py).
Long-running operations use BackgroundTasks to avoid blocking handlers.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pipeline.api.models import ErrorResponse, HealthResponse
from pipeline.api.routers.artists import router as artists_router
from pipeline.api.routers.pieces import router as pieces_router
from pipeline.api.routers.pipeline import router as pipeline_router
from pipeline.lib.config import get_settings

logger = logging.getLogger(__name__)

API_VERSION = "0.2.0"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Startup/shutdown lifecycle events."""
    settings = get_settings()

    if not settings.pipeline_api_secret:
        logger.warning(
            "PIPELINE_API_SECRET is not set — all mutation endpoints will be rejected. "
            "Set it in .env or environment variables."
        )
    if not settings.gemini_api_key:
        logger.warning("GEMINI_API_KEY is not set — Gemini-based generation will fail.")

    logger.info("Pipeline API v%s starting up", API_VERSION)
    yield
    logger.info("Pipeline API shutting down")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title="Noir Canvas Pipeline API",
        version=API_VERSION,
        description=(
            "API for the Noir Canvas AI art pipeline. "
            "Manages virtual artists, piece generation, curation, and gallery registration."
        ),
        lifespan=lifespan,
        responses={
            403: {"model": ErrorResponse, "description": "Authentication failed"},
            404: {"model": ErrorResponse, "description": "Resource not found"},
            422: {"description": "Validation error"},
        },
    )

    _configure_cors(app)

    app.include_router(artists_router)
    app.include_router(pieces_router)
    app.include_router(pipeline_router)

    @app.get("/", tags=["health"])
    def root() -> dict:
        return {
            "name": "Noir Canvas Pipeline API",
            "version": API_VERSION,
            "docs": "/docs",
        }

    @app.get("/health", response_model=HealthResponse, tags=["health"])
    def health() -> HealthResponse:
        return HealthResponse(version=API_VERSION)

    return app


def _configure_cors(app: FastAPI) -> None:
    """Add CORS middleware with origins from ALLOWED_ORIGINS env var."""
    settings = get_settings()
    raw = settings.allowed_origins.strip()

    if not raw:
        logger.warning(
            "ALLOWED_ORIGINS is empty — CORS will reject all cross-origin requests. "
            "Set ALLOWED_ORIGINS in .env (comma-separated)."
        )
        origins: list[str] = []
    else:
        origins = [o.strip() for o in raw.split(",") if o.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-API-Key", "Authorization"],
    )


app = create_app()
