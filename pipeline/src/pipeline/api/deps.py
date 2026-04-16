"""Shared FastAPI dependencies: auth, settings, path validation."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from fastapi import Header, HTTPException, status

from pipeline.lib.config import PipelineSettings, get_settings
from pipeline.lib.paths import validate_output_path

logger = logging.getLogger(__name__)

_SAFE_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]*$")


def get_pipeline_settings() -> PipelineSettings:
    """Dependency that provides validated pipeline settings."""
    return get_settings()


def verify_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
) -> str:
    """Validate X-API-Key header against pipeline_api_secret.

    Rejects ALL mutations when the secret is not configured (empty string),
    preventing accidental auth bypass on misconfigured deployments.
    """
    settings = get_settings()

    if not settings.pipeline_api_secret:
        logger.warning("Mutation rejected: pipeline_api_secret is not configured")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API mutations are disabled — pipeline_api_secret is not configured.",
        )

    if x_api_key != settings.pipeline_api_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )

    return x_api_key


def validate_slug(slug: str) -> str:
    """Validate that a slug is safe for filesystem path construction."""
    if not _SAFE_SLUG_RE.match(slug):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid slug format: {slug!r}",
        )
    return slug


def sandbox_path(path: Path) -> Path:
    """Validate that a path is within allowed output directories.

    Wraps paths.validate_output_path and converts ValueError to HTTP 400.
    """
    try:
        return validate_output_path(path)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from None
