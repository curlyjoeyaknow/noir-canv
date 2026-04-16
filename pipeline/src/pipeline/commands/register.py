"""Register pipeline output to the gallery data files and public assets.

Phase 6 of the artist creation pipeline:
1. Validates artist data against shared schemas
2. Validates piece data against shared schemas
3. Copies selected images to apps/web/public/images/
4. Writes validated JSON to data/
"""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path

import click

from pipeline.lib.config import load_artist_configs, load_pieces
from pipeline.lib.paths import (
    DATA_DIR,
    OUTPUT_DIR,
    public_artists_dir,
    public_pieces_dir,
    selected_dir,
)
from pipeline.lib.schemas import Artist, Collection, Piece

logger = logging.getLogger(__name__)


def _load_json_list(path: Path) -> list[dict]:
    """Load a JSON array from file, returning [] if missing."""
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"Expected JSON array in {path}")
    return raw


def _write_json_list(path: Path, data: list[dict]) -> None:
    """Write a JSON array to file with consistent formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _validate_artists(artists_path: Path) -> list[Artist]:
    """Load and validate all artists against the Artist schema."""
    raw = _load_json_list(artists_path)
    validated: list[Artist] = []
    for i, entry in enumerate(raw):
        try:
            validated.append(Artist.model_validate(entry))
        except Exception as exc:
            slug = entry.get("slug", f"<index {i}>") if isinstance(entry, dict) else f"<index {i}>"
            raise click.ClickException(
                f"Artist validation failed for '{slug}': {exc}"
            ) from exc
    return validated


def _validate_pieces(pieces_path: Path) -> list[Piece]:
    """Load and validate all pieces against the Piece schema."""
    raw = _load_json_list(pieces_path)
    validated: list[Piece] = []
    for i, entry in enumerate(raw):
        try:
            validated.append(Piece.model_validate(entry))
        except Exception as exc:
            slug = entry.get("slug", f"<index {i}>") if isinstance(entry, dict) else f"<index {i}>"
            raise click.ClickException(
                f"Piece validation failed for '{slug}': {exc}"
            ) from exc
    return validated


def _copy_selected_images(artist_slug: str) -> list[Path]:
    """Copy selected/curated images to public/images/pieces/."""
    sel_dir = selected_dir(artist_slug)
    if not sel_dir.exists():
        return []
    dest_dir = public_pieces_dir()
    copied: list[Path] = []
    for img in sorted(sel_dir.glob("*.png")):
        dest = dest_dir / img.name
        shutil.copy2(img, dest)
        copied.append(dest)
    return copied


def _copy_artist_media(artist_slug: str) -> list[Path]:
    """Copy generated artist media (avatars, studio) to public/images/artists/."""
    dest_dir = public_artists_dir(artist_slug)
    copied: list[Path] = []

    avatars_dir = OUTPUT_DIR / "avatars" / artist_slug
    if avatars_dir.exists():
        avatar_imgs = sorted(avatars_dir.glob("*.png"))
        for idx, img in enumerate(avatar_imgs):
            dest = dest_dir / img.name
            shutil.copy2(img, dest)
            copied.append(dest)
            if idx == 0:
                portrait = dest_dir / "portrait.png"
                shutil.copy2(img, portrait)
                copied.append(portrait)

    studio_dir = OUTPUT_DIR / "artist_studio" / artist_slug
    if studio_dir.exists():
        for img in sorted(studio_dir.glob("*.png")):
            dest = dest_dir / img.name
            shutil.copy2(img, dest)
            copied.append(dest)

    return copied


@click.command("register")
@click.option("--artist", "artist_slug", default=None,
              help="Register a specific artist's assets.")
@click.option("--validate-only", is_flag=True,
              help="Only validate data, don't copy files.")
@click.option("--dry-run", is_flag=True,
              help="Show what would be done without making changes.")
def register(
    artist_slug: str | None,
    validate_only: bool,
    dry_run: bool,
) -> None:
    """Validate gallery data and publish pipeline assets to the frontend.

    Validates all data in data/*.json against shared schemas.
    Copies selected images and artist media to apps/web/public/images/.
    """
    artists_path = DATA_DIR / "artists.json"
    pieces_path = DATA_DIR / "pieces.json"
    collections_path = DATA_DIR / "collections.json"

    click.echo("Validating artists...")
    artists = _validate_artists(artists_path)
    click.echo(f"  {len(artists)} artist(s) valid")

    click.echo("Validating pieces...")
    if pieces_path.exists():
        pieces = _validate_pieces(pieces_path)
        click.echo(f"  {len(pieces)} piece(s) valid")
    else:
        pieces = []
        click.echo("  No pieces.json found (will be created on first piece registration)")

    if collections_path.exists():
        click.echo("Validating collections...")
        raw_collections = _load_json_list(collections_path)
        for i, entry in enumerate(raw_collections):
            try:
                Collection.model_validate(entry)
            except Exception as exc:
                slug = entry.get("slug", f"<index {i}>") if isinstance(entry, dict) else f"<index {i}>"
                raise click.ClickException(
                    f"Collection validation failed for '{slug}': {exc}"
                ) from exc
        click.echo(f"  {len(raw_collections)} collection(s) valid")

    artist_slugs_valid = {a.slug for a in artists}
    for p in pieces:
        if p.artist_slug not in artist_slugs_valid:
            click.echo(f"  WARNING: piece '{p.slug}' references unknown artist '{p.artist_slug}'")

    if validate_only:
        click.echo("Validation complete (--validate-only mode)")
        return

    if artist_slug:
        slugs_to_register = [artist_slug]
    else:
        slugs_to_register = [a.slug for a in artists]

    total_copied = 0
    for slug in slugs_to_register:
        if dry_run:
            click.echo(f"Would register assets for {slug}")
            continue

        copied_pieces = _copy_selected_images(slug)
        copied_media = _copy_artist_media(slug)
        total_copied += len(copied_pieces) + len(copied_media)
        if copied_pieces:
            click.echo(f"  Copied {len(copied_pieces)} piece image(s) for {slug}")
        if copied_media:
            click.echo(f"  Copied {len(copied_media)} media file(s) for {slug}")

    if dry_run:
        click.echo("Dry run complete")
    else:
        click.echo(f"Registration complete: {total_copied} file(s) copied")
