"""Interactive and programmatic selection of best images from raw batches.

Copies selected images to pipeline/output/selected/{artist}/
and optionally removes them from raw/.
"""

from __future__ import annotations

import re
import shutil
import uuid
from pathlib import Path

import click

from pipeline.lib.paths import OUTPUT_DIR, selected_dir


def _next_selected_index(sel_dir: Path, piece_slug: str) -> int:
    """Return the next 1-based index for a piece in selected/."""
    existing = list(sel_dir.glob(f"{piece_slug}*.png"))
    max_n = 0
    for f in existing:
        if f.name == f"{piece_slug}.png":
            max_n = max(max_n, 1)
        else:
            m = re.match(rf"{re.escape(piece_slug)}-(\d+)\.png", f.name)
            if m:
                max_n = max(max_n, int(m.group(1)))
    return max_n + 1


def run_curate_programmatic(
    artist_slug: str,
    piece_slug: str,
    selected_indices: list[int],
) -> list[Path]:
    """Copy selected raw images to selected/. Returns paths of copied files."""
    raw_dir = OUTPUT_DIR / "raw" / artist_slug / piece_slug
    if not raw_dir.exists() or not raw_dir.is_dir():
        raise ValueError(f"No raw images for piece '{piece_slug}'. Run generate first.")
    images = sorted(raw_dir.glob("*.png"))
    if not images:
        raise ValueError(f"No images in {raw_dir}")
    indices = list(dict.fromkeys(selected_indices))
    valid = [i for i in indices if 0 <= i < len(images)]
    if not valid:
        raise ValueError(f"Invalid indices. Use 0\u2013{len(images) - 1}")
    sel_dir = selected_dir(artist_slug)
    start = _next_selected_index(sel_dir, piece_slug)
    copied: list[Path] = []
    to_remove: list[Path] = []
    for idx, i in enumerate(valid):
        src = images[i]
        dest = sel_dir / f"{piece_slug}-{start + idx}.png"
        shutil.copy(src, dest)
        copied.append(dest)
        to_remove.append(src)
    for src in to_remove:
        src.unlink(missing_ok=True)
    return copied


def _piece_from_filename(name: str) -> str:
    """Extract piece slug from selected filename (e.g. foo-1.png -> foo)."""
    m = re.match(r"^(.+)-(\d+)\.png$", name)
    if m:
        return m.group(1)
    if name.endswith(".png"):
        return name[:-4]
    return name


def run_uncurate(
    artist_slug: str,
    filenames: list[str],
) -> list[Path]:
    """Move selected images back to raw/. Returns paths of moved files."""
    sel_dir = selected_dir(artist_slug)
    if not sel_dir.exists():
        raise ValueError(f"No selected dir for {artist_slug}")
    moved: list[Path] = []
    for name in filenames:
        if not name.endswith(".png"):
            continue
        src = sel_dir / name
        if not src.exists() or not src.is_file():
            continue
        piece = _piece_from_filename(name)
        raw_dir = OUTPUT_DIR / "raw" / artist_slug / piece
        raw_dir.mkdir(parents=True, exist_ok=True)
        dest = raw_dir / f"{piece}-returned-{uuid.uuid4().hex[:8]}.png"
        shutil.move(str(src), dest)
        moved.append(dest)
    return moved


@click.command("curate")
@click.option("--artist", "artist_slug", required=True, help="Artist slug.")
@click.option("--piece", "piece_slug", default=None, help="Specific piece slug (curate all if omitted).")
def curate(artist_slug: str, piece_slug: str | None) -> None:
    """Interactively select the best images from raw generation batches."""
    raw_base = OUTPUT_DIR / "raw" / artist_slug
    if not raw_base.exists():
        raise click.ClickException(f"No raw images for {artist_slug}")

    if piece_slug:
        piece_dir = raw_base / piece_slug
        if not piece_dir.exists() or not piece_dir.is_dir():
            raise click.ClickException(
                f"No raw images for piece '{piece_slug}'. Run generate first."
            )
        dirs = [piece_dir]
    else:
        dirs = sorted(d for d in raw_base.iterdir() if d.is_dir())

    for d in dirs:
        images = sorted(d.glob("*.png"))
        if not images:
            continue
        click.echo(f"\n{d.name}: {len(images)} images")
        for i, img in enumerate(images, 1):
            click.echo(f"  {i}. {img.name}")
        sel = click.prompt("Enter numbers to keep (comma-separated)", default="1")
        try:
            indices = [int(x.strip()) - 1 for x in sel.split(",") if x.strip()]
        except ValueError:
            raise click.ClickException(
                "Invalid input: enter comma-separated numbers (e.g. 1,3,5)"
            )
        indices = list(dict.fromkeys(indices))
        valid_indices = [i for i in indices if 0 <= i < len(images)]
        if not valid_indices:
            raise click.ClickException(
                f"No valid indices. Enter numbers 1\u2013{len(images)}"
            )
        if len(valid_indices) > 3:
            click.echo(
                f"Design recommends 1\u20133 per piece; continuing with {len(valid_indices)} selections."
            )
        sel_out = selected_dir(artist_slug)
        for idx, i in enumerate(valid_indices):
            src = images[i]
            dest = (
                sel_out / f"{d.name}.png"
                if len(valid_indices) == 1
                else sel_out / f"{d.name}-{idx + 1}.png"
            )
            shutil.copy(src, dest)
            click.echo(f"Copied to {dest}")
