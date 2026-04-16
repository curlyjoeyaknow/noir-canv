"""Orchestrate mockup generation: frame + room mockups for gallery pieces.

Combines the frame and room_mockup commands into a single workflow.
"""

from __future__ import annotations

import logging
from pathlib import Path

import click

from pipeline.commands.frame import run_frame
from pipeline.commands.room_mockup import run_room_mockup
from pipeline.lib.config import load_pieces
from pipeline.lib.paths import PUBLIC_IMAGES_DIR, mockups_framed_dir, mockups_rooms_dir

logger = logging.getLogger(__name__)


def _get_registered_pieces() -> list[tuple[str, Path, str | None]]:
    """Return (slug, image_path, artist_slug) for pieces in public/images/pieces/."""
    pieces_dir = PUBLIC_IMAGES_DIR / "pieces"
    if not pieces_dir.exists():
        return []

    slug_to_artist: dict[str, str] = {}
    try:
        for p in load_pieces():
            slug_to_artist[p.slug] = p.artist_slug
    except (FileNotFoundError, ValueError):
        pass

    result: list[tuple[str, Path, str | None]] = []
    for p in sorted(pieces_dir.glob("*.png")):
        artist = slug_to_artist.get(p.stem)
        result.append((p.stem, p, artist))
    return result


def run_mockup(
    piece_slug: str | None = None,
    *,
    all_pieces: bool = False,
    flat_frame: bool = False,
    room_mockups: bool = True,
    use_gemini_rooms: bool = True,
    frame_style: str = "dark-wood",
) -> list[Path]:
    """Generate mockups for piece(s).

    If piece_slug: single piece. If all_pieces: all in public/images/pieces/.
    """
    if piece_slug:
        piece_path = PUBLIC_IMAGES_DIR / "pieces" / f"{piece_slug}.png"
        if not piece_path.exists():
            raise ValueError(f"Piece image not found: {piece_path}")
        artist_slug: str | None = None
        try:
            for p in load_pieces():
                if p.slug == piece_slug:
                    artist_slug = p.artist_slug
                    break
        except (FileNotFoundError, ValueError):
            pass
        pieces = [(piece_slug, piece_path, artist_slug)]
    elif all_pieces:
        pieces = _get_registered_pieces()
        if not pieces:
            raise ValueError("No pieces in public/images/pieces/")
    else:
        raise ValueError("Provide piece_slug or all_pieces=True")

    framed_out = mockups_framed_dir()
    rooms_out = mockups_rooms_dir()
    all_out: list[Path] = []

    for slug, art_path, art_slug in pieces:
        framed_path = framed_out / f"{slug}-framed.png"
        flat_path, _ = run_frame(
            art_path, framed_path,
            artist_slug=art_slug,
            use_ref_frames=True,
            frame_style=frame_style,
            angled=not flat_frame,
        )
        all_out.append(framed_path)

        if room_mockups:
            room_out = run_room_mockup(
                flat_path, rooms_out, slug,
                use_gemini=use_gemini_rooms,
            )
            all_out.extend(room_out)

    return all_out


@click.command("mockup")
@click.option("--piece", "piece_slug", default=None, help="Piece slug.")
@click.option("--all", "all_pieces", is_flag=True, help="Process all registered pieces.")
@click.option("--flat", is_flag=True, help="Use flat frame (no perspective).")
@click.option("--no-gemini-rooms", is_flag=True, help="Skip Gemini for room mockups.")
@click.option("--frame-style", type=click.Choice([
    "black", "white", "black-white-matte", "dark-wood", "gold",
]), default="dark-wood")
def mockup(
    piece_slug: str | None,
    all_pieces: bool,
    flat: bool,
    no_gemini_rooms: bool,
    frame_style: str,
) -> None:
    """Generate framed + room mockups for gallery pieces."""
    if not piece_slug and not all_pieces:
        raise click.ClickException("Provide --piece or --all")
    try:
        paths_out = run_mockup(
            piece_slug=piece_slug,
            all_pieces=all_pieces,
            flat_frame=flat,
            room_mockups=True,
            use_gemini_rooms=not no_gemini_rooms,
            frame_style=frame_style,
        )
        for p in paths_out:
            click.echo(f"  {p}")
        click.echo(f"Generated {len(paths_out)} mockup(s)")
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
