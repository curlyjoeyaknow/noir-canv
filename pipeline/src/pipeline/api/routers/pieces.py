"""Piece endpoints.

GET endpoints are public. POST /generate requires X-API-Key auth.
Generation is dispatched as a background task.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from pipeline.api.deps import validate_slug, verify_api_key
from pipeline.api.models import (
    GeneratePiecesRequest,
    PieceListResponse,
    PieceSummary,
    TaskAcceptedResponse,
    TaskStatus,
)
from pipeline.api.tasks import create_task, update_task
from pipeline.commands.generate import run_generate
from pipeline.lib.config import load_artist_config, load_pieces

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pieces", tags=["pieces"])


@router.get("", response_model=PieceListResponse)
def list_pieces(artist_slug: str | None = None) -> PieceListResponse:
    """List all pieces, optionally filtered by artist slug."""
    try:
        all_pieces = load_pieces()
    except FileNotFoundError:
        return PieceListResponse(pieces=[], count=0)

    if artist_slug:
        all_pieces = [p for p in all_pieces if p.artist_slug == artist_slug]

    summaries = [
        PieceSummary(slug=p.slug, title=p.title, artistSlug=p.artist_slug)
        for p in all_pieces
    ]
    return PieceListResponse(pieces=summaries, count=len(summaries))


@router.get("/{slug}", response_model=PieceSummary)
def get_piece(slug: str = Depends(validate_slug)) -> PieceSummary:
    """Get a single piece by slug."""
    try:
        all_pieces = load_pieces()
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Piece not found: {slug}",
        )

    for piece in all_pieces:
        if piece.slug == slug:
            return PieceSummary(slug=piece.slug, title=piece.title, artistSlug=piece.artist_slug)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Piece not found: {slug}",
    )


@router.post(
    "/generate",
    response_model=TaskAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verify_api_key)],
)
def generate_pieces(
    req: GeneratePiecesRequest,
    background_tasks: BackgroundTasks,
) -> TaskAcceptedResponse:
    """Trigger image generation for an artist (runs in background)."""
    try:
        load_artist_config(req.artist_slug)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artist not found: {req.artist_slug}",
        ) from exc

    task = create_task(phase="generate")
    background_tasks.add_task(
        _run_generate, task.task_id, req,
    )
    return TaskAcceptedResponse(task_id=task.task_id)


def _run_generate(task_id: str, req: GeneratePiecesRequest) -> None:
    """Background worker for image generation."""
    update_task(task_id, status=TaskStatus.RUNNING)
    try:
        saved = run_generate(
            req.artist_slug,
            piece_slug=req.piece_slug,
            count=req.count,
            seed=req.seed,
            cfg_scale=req.cfg_scale,
            steps=req.steps,
            prompt_override=req.prompt_override,
        )

        update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            message=f"Generated {len(saved)} image(s)",
            result={"count": len(saved)},
        )
    except Exception:
        logger.exception("Background generate failed for task %s", task_id)
        update_task(
            task_id,
            status=TaskStatus.FAILED,
            message="Image generation failed. Check server logs.",
        )
