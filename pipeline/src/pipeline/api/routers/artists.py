"""Artist endpoints.

GET endpoints are public. POST requires X-API-Key auth.
Artist creation is dispatched as a background task — the handler
returns immediately with a task ID.
"""

from __future__ import annotations

import json
import logging
import re

import yaml

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from pipeline.api.deps import validate_slug, verify_api_key
from pipeline.api.models import (
    ArtistListResponse,
    ArtistSummary,
    CreateArtistRequest,
    TaskAcceptedResponse,
    TaskStatus,
)
from pipeline.api.tasks import create_task, update_task
from pipeline.lib.config import (
    ArtistConfig,
    list_example_folders,
    load_artist_config,
    load_artist_configs,
)
from pipeline.lib.paths import ARTISTS_DIR, DATA_DIR
from pipeline.lib.prompts import (
    artist_bio_prompt,
    artist_statement_prompt,
    fallback_bio,
    fallback_statement,
    generate_pseudonym,
    generate_text_with_gemini,
)
from pipeline.lib.schemas import Artist, ArtistStyle

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/artists", tags=["artists"])


@router.get("", response_model=ArtistListResponse)
def list_artists() -> ArtistListResponse:
    """List all artists from pipeline configs."""
    configs = load_artist_configs()
    artists = [ArtistSummary(slug=a.slug, name=a.name) for a in configs]
    return ArtistListResponse(artists=artists, count=len(artists))


@router.get("/{slug}", response_model=ArtistSummary)
def get_artist(slug: str = Depends(validate_slug)) -> ArtistSummary:
    """Get a single artist's pipeline config by slug."""
    try:
        config = load_artist_config(slug)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artist not found: {slug}",
        ) from exc
    return ArtistSummary(slug=config.slug, name=config.name)


@router.post(
    "",
    response_model=TaskAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verify_api_key)],
)
def create_artist_endpoint(
    req: CreateArtistRequest,
    background_tasks: BackgroundTasks,
) -> TaskAcceptedResponse:
    """Create a new virtual artist (runs in background)."""
    available = list_example_folders()
    if req.base_artist not in available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown example folder: {req.base_artist}",
        )

    if req.slug:
        validate_slug(req.slug)

    existing_slugs = {a.slug for a in load_artist_configs()}
    if req.slug and req.slug in existing_slugs:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Artist slug already exists: {req.slug}",
        )

    task = create_task(phase="create-artist")
    background_tasks.add_task(
        _run_create_artist, task.task_id, req,
    )
    return TaskAcceptedResponse(task_id=task.task_id)


def _run_create_artist(task_id: str, req: CreateArtistRequest) -> None:
    """Background worker for artist creation."""
    update_task(task_id, status=TaskStatus.RUNNING)
    try:
        existing_slugs = {a.slug for a in load_artist_configs()}

        if req.pseudonym and req.slug:
            name, slug_val = req.pseudonym, req.slug
        elif req.pseudonym:
            name = req.pseudonym
            slug_val = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        else:
            name, slug_val = generate_pseudonym(existing_slugs)

        style = f"{req.base_artist.replace('_', ' ')} style"

        bio: str | None = None
        statement: str | None = None
        if req.use_gemini:
            bio = generate_text_with_gemini(
                artist_bio_prompt(name, style, [req.base_artist.replace("_", " ")])
            )
            statement = generate_text_with_gemini(
                artist_statement_prompt(name, style)
            )
        if not bio:
            bio = fallback_bio(name, style)
        if not statement:
            statement = fallback_statement()

        artist_config = ArtistConfig(
            name=name,
            slug=slug_val,
            example_artists=[req.base_artist],
            style_reference=style,
            prompt_prefix="Fine art, gallery quality, ",
            prompt_suffix=f", {style.lower()}",
            bio=bio,
            statement=statement,
        )
        ARTISTS_DIR.mkdir(parents=True, exist_ok=True)
        config_path = ARTISTS_DIR / f"{slug_val}.yaml"
        config_path.write_text(
            yaml.dump(
                artist_config.model_dump(exclude_none=True),
                default_flow_style=False,
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        gallery_artist = Artist.model_validate({
            "slug": slug_val,
            "name": name,
            "bio": bio,
            "artistStatement": statement,
            "portraitUrl": f"/images/artists/{slug_val}/portrait.png",
            "influences": [req.base_artist.replace("_", " ")],
            "style": {
                "medium": "mixed media",
                "palette": "varied",
                "subjects": style,
            },
            "pricingTier": req.pricing_tier,
            "defaultEditionSize": req.edition_size,
        })

        artists_path = DATA_DIR / "artists.json"
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        existing_artists: list[dict] = []
        if artists_path.exists():
            existing_artists = json.loads(artists_path.read_text(encoding="utf-8"))
        existing_artists.append(gallery_artist.model_dump(by_alias=True))
        artists_path.write_text(
            json.dumps(existing_artists, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            message=f"Created artist {name} ({slug_val})",
            result={"slug": slug_val, "name": name},
        )
    except Exception:
        logger.exception("Background create-artist failed for task %s", task_id)
        update_task(
            task_id,
            status=TaskStatus.FAILED,
            message="Artist creation failed. Check server logs.",
        )
