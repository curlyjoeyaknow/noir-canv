"""Request and response models for the Pipeline API.

All request models use extra="forbid" to reject unknown fields.
Response models wrap the shared schema types from pipeline.lib.schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelinePhase(str, Enum):
    CREATE_ARTIST = "create-artist"
    ARTIST_MEDIA = "artist-media"
    GENERATE = "generate"
    CURATE = "curate"
    MOCKUPS = "mockups"
    REGISTER = "register"


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class CreateArtistRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_artist: str = Field(..., min_length=1, description="Example folder name for style reference.")
    pseudonym: str | None = Field(None, min_length=1, description="Custom artist name.")
    slug: str | None = Field(None, pattern=r"^[a-z][a-z0-9-]*$", description="Custom URL slug.")
    use_gemini: bool = Field(True, description="Use Gemini API for bio/statement generation.")
    pricing_tier: str = Field("mid-range", pattern=r"^(affordable|mid-range|premium)$")
    edition_size: int = Field(25, ge=1, le=1000)


class GeneratePiecesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artist_slug: str = Field(..., pattern=r"^[a-z][a-z0-9-]*$")
    piece_slug: str | None = Field(None, pattern=r"^[a-z][a-z0-9]*(?:-[a-z][a-z0-9]*)*-[0-9]{3}$")
    count: int = Field(1, ge=1, le=50)
    seed: int | None = Field(None, ge=0)
    cfg_scale: float | None = Field(None, ge=0.0, le=30.0)
    steps: int | None = Field(None, ge=1, le=200)
    prompt_override: str | None = Field(None, max_length=2000)


class RunPipelineRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artist_slug: str = Field(..., pattern=r"^[a-z][a-z0-9-]*$")
    phases: list[PipelinePhase] = Field(
        default_factory=lambda: list(PipelinePhase),
        min_length=1,
        description="Phases to run (default: all).",
    )


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class TaskAcceptedResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: TaskStatus = TaskStatus.PENDING
    message: str = "Task accepted and queued for processing."


class TaskStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    status: TaskStatus
    phase: str | None = None
    message: str | None = None
    result: dict | None = None
    created_at: datetime
    updated_at: datetime


class ArtistSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    name: str


class ArtistListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artists: list[ArtistSummary]
    count: int


class PieceSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    slug: str
    title: str
    artist_slug: str = Field(..., alias="artistSlug")


class PieceListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pieces: list[PieceSummary]
    count: int


class PipelineStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = "idle"
    active_tasks: int = 0


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detail: str


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = "ok"
    version: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
