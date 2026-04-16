"""Pipeline FastAPI application.

Import the app instance for uvicorn:
    uvicorn pipeline.api.main:app --reload
"""

from pipeline.api.main import app

__all__ = ["app"]
