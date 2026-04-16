"""In-memory background task tracking.

Stores task metadata so the API can report status for long-running
pipeline operations dispatched via FastAPI BackgroundTasks.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from threading import Lock

from pipeline.api.models import TaskStatus, TaskStatusResponse

logger = logging.getLogger(__name__)

_tasks: dict[str, TaskStatusResponse] = {}
_lock = Lock()

MAX_STORED_TASKS = 200


def create_task(phase: str | None = None) -> TaskStatusResponse:
    """Register a new pending task and return its status object."""
    now = datetime.now(timezone.utc)
    task = TaskStatusResponse(
        task_id=str(uuid.uuid4()),
        status=TaskStatus.PENDING,
        phase=phase,
        created_at=now,
        updated_at=now,
    )
    with _lock:
        _tasks[task.task_id] = task
        _evict_old()
    return task


def get_task(task_id: str) -> TaskStatusResponse | None:
    """Look up a task by ID. Returns None if not found."""
    with _lock:
        return _tasks.get(task_id)


def update_task(
    task_id: str,
    *,
    status: TaskStatus | None = None,
    phase: str | None = None,
    message: str | None = None,
    result: dict | None = None,
) -> None:
    """Update fields on an existing task."""
    with _lock:
        task = _tasks.get(task_id)
        if task is None:
            logger.warning("Attempted to update unknown task %s", task_id)
            return
        now = datetime.now(timezone.utc)
        updates: dict = {"updated_at": now}
        if status is not None:
            updates["status"] = status
        if phase is not None:
            updates["phase"] = phase
        if message is not None:
            updates["message"] = message
        if result is not None:
            updates["result"] = result
        _tasks[task_id] = task.model_copy(update=updates)


def list_active_count() -> int:
    """Return count of tasks in PENDING or RUNNING state."""
    with _lock:
        return sum(
            1 for t in _tasks.values()
            if t.status in (TaskStatus.PENDING, TaskStatus.RUNNING)
        )


def _evict_old() -> None:
    """Remove oldest completed/failed tasks when over capacity."""
    if len(_tasks) <= MAX_STORED_TASKS:
        return
    completed = sorted(
        (tid for tid, t in _tasks.items()
         if t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)),
        key=lambda tid: _tasks[tid].updated_at,
    )
    to_remove = len(_tasks) - MAX_STORED_TASKS
    for tid in completed[:to_remove]:
        del _tasks[tid]
