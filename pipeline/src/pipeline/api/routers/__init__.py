"""API routers package."""

from pipeline.api.routers.artists import router as artists_router
from pipeline.api.routers.pieces import router as pieces_router
from pipeline.api.routers.pipeline import router as pipeline_router

__all__ = ["artists_router", "pieces_router", "pipeline_router"]
