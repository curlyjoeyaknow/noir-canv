"""Pipeline orchestration endpoints.

POST /run triggers the full pipeline (or selected phases) in the background.
GET /status reports on active tasks.
GET /tasks/{task_id} retrieves status for a specific task.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from pipeline.api.deps import verify_api_key
from pipeline.api.models import (
    PipelinePhase,
    PipelineStatusResponse,
    RunPipelineRequest,
    TaskAcceptedResponse,
    TaskStatus,
    TaskStatusResponse,
)
from pipeline.api.tasks import create_task, get_task, list_active_count, update_task
from pipeline.lib.config import load_artist_config

try:
    from pipeline.commands.generate import run_generate
except ImportError:
    run_generate = None  # type: ignore[assignment, misc]

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


@router.get("/status", response_model=PipelineStatusResponse)
def pipeline_status() -> PipelineStatusResponse:
    """Check pipeline status and active task count."""
    active = list_active_count()
    return PipelineStatusResponse(
        status="busy" if active > 0 else "idle",
        active_tasks=active,
    )


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str) -> TaskStatusResponse:
    """Get status of a specific background task."""
    task = get_task(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {task_id}",
        )
    return task


@router.post(
    "/run",
    response_model=TaskAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verify_api_key)],
)
def run_pipeline(
    req: RunPipelineRequest,
    background_tasks: BackgroundTasks,
) -> TaskAcceptedResponse:
    """Trigger pipeline run for an artist (runs in background).

    Dispatches selected phases sequentially in a background task.
    """
    try:
        load_artist_config(req.artist_slug)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artist not found: {req.artist_slug}",
        ) from exc

    phase_names = ", ".join(p.value for p in req.phases)
    task = create_task(phase=phase_names)
    background_tasks.add_task(
        _run_pipeline_phases, task.task_id, req,
    )
    return TaskAcceptedResponse(task_id=task.task_id)


def _run_pipeline_phases(task_id: str, req: RunPipelineRequest) -> None:
    """Background worker that runs pipeline phases sequentially."""
    update_task(task_id, status=TaskStatus.RUNNING)

    phase_runners = {
        PipelinePhase.CREATE_ARTIST: _phase_create_artist,
        PipelinePhase.GENERATE: _phase_generate,
    }

    completed_phases: list[str] = []
    try:
        for phase in req.phases:
            update_task(task_id, phase=phase.value)
            runner = phase_runners.get(phase)
            if runner:
                runner(req.artist_slug)
                completed_phases.append(phase.value)
            else:
                skipped = f"Phase {phase.value} not yet implemented"
                logger.warning(skipped)
                update_task(task_id, message=skipped)

        update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            message=f"Pipeline completed: {', '.join(completed_phases)}",
            result={"completed_phases": completed_phases},
        )
    except Exception:
        logger.exception("Pipeline failed at phase %s for task %s", phase.value, task_id)
        update_task(
            task_id,
            status=TaskStatus.FAILED,
            message=f"Pipeline failed during phase: {phase.value}",
            result={"completed_phases": completed_phases},
        )


def _phase_create_artist(artist_slug: str) -> None:
    """Run create-artist phase (no-op if artist already exists)."""
    try:
        load_artist_config(artist_slug)
        logger.info("Artist %s already exists, skipping create-artist", artist_slug)
    except FileNotFoundError:
        logger.info("Artist %s not found, would need base_artist to create", artist_slug)


def _phase_generate(artist_slug: str) -> None:
    """Run generate phase for an artist."""
    if run_generate is None:
        raise RuntimeError("ML dependencies not installed (pip install torch diffusers)")
    run_generate(artist_slug, count=1)
