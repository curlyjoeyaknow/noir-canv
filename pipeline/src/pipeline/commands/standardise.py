"""Standardise artwork images to a single canonical canvas size.

Every piece image is centred on a 1200x1800 (2:3 portrait) canvas with a
warm off-white background. This guarantees consistent framing across the
entire gallery regardless of the original generation output size.

Usage:
    pipeline standardise --public          # all public pieces in-place
    pipeline standardise --input img.png   # single file
    pipeline standardise --input-dir dir/  # all images in a directory
    pipeline standardise --artist kai-vale # artist's selected output
"""

from __future__ import annotations

import glob
import logging
from pathlib import Path

import click
from PIL import Image

from pipeline.lib.paths import OUTPUT_DIR, public_pieces_dir, selected_dir

logger = logging.getLogger(__name__)

# Canonical canvas dimensions (2:3 portrait — maps to 8×12", 12×18", 20×30")
CANVAS_W = 1200
CANVAS_H = 1800
# Warm off-white to match the gallery aesthetic
BACKGROUND_RGB = (250, 249, 247)


def standardise_image(src: Path, dest: Path) -> tuple[int, int]:
    """Centre-fit src onto a 1200×1800 canvas and save to dest.

    Returns the (width, height) of the artwork within the canvas.
    """
    img = Image.open(src).convert("RGB")
    art_w, art_h = img.size

    scale = min(CANVAS_W / art_w, CANVAS_H / art_h)
    new_w = int(art_w * scale)
    new_h = int(art_h * scale)

    resized = img.resize((new_w, new_h), Image.LANCZOS)

    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), BACKGROUND_RGB)
    offset_x = (CANVAS_W - new_w) // 2
    offset_y = (CANVAS_H - new_h) // 2
    canvas.paste(resized, (offset_x, offset_y))

    dest.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(str(dest), format="PNG", optimize=True)
    return new_w, new_h


def _process_list(images: list[Path], in_place: bool, output_dir: Path | None) -> int:
    """Standardise a list of images. Returns count processed."""
    count = 0
    for src in sorted(images):
        if in_place:
            dest = src
        elif output_dir:
            dest = output_dir / src.name
        else:
            dest = src  # default to in-place

        art_w, art_h = standardise_image(src, dest)
        label = "(in-place)" if dest == src else str(dest)
        click.echo(f"  {src.name}: {art_w}x{art_h} on {CANVAS_W}x{CANVAS_H} {label}")
        count += 1
    return count


@click.command("standardise")
@click.option("--input", "input_path", default=None, type=click.Path(exists=True),
              help="Single image file to standardise.")
@click.option("--input-dir", default=None, type=click.Path(exists=True),
              help="Directory of images to standardise.")
@click.option("--artist", "artist_slug", default=None,
              help="Standardise selected images for a specific artist slug.")
@click.option("--public", "do_public", is_flag=True,
              help="Standardise all images in apps/web/public/images/pieces/ (in-place).")
@click.option("--output-dir", default=None, type=click.Path(),
              help="Output directory (default: in-place). Ignored with --public.")
@click.option("--canvas-w", default=CANVAS_W, type=int, show_default=True,
              help="Canvas width in pixels.")
@click.option("--canvas-h", default=CANVAS_H, type=int, show_default=True,
              help="Canvas height in pixels.")
def standardise(
    input_path: str | None,
    input_dir: str | None,
    artist_slug: str | None,
    do_public: bool,
    output_dir: str | None,
    canvas_w: int,
    canvas_h: int,
) -> None:
    """Standardise artwork images to a canonical 1200x1800 (2:3) canvas.

    Centres each artwork on a warm off-white background. Overwrites the
    source file in-place (or writes to --output-dir if specified).
    """
    # Allow canvas override
    import pipeline.commands.standardise as _self
    _self.CANVAS_W = canvas_w
    _self.CANVAS_H = canvas_h

    out_dir = Path(output_dir) if output_dir else None
    images: list[Path] = []

    if do_public:
        pub = public_pieces_dir()
        for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
            images.extend(pub.glob(ext))
        click.echo(f"Standardising {len(images)} public piece images to {canvas_w}×{canvas_h}...")
        count = _process_list(images, in_place=True, output_dir=None)
        click.echo(f"Done — {count} image(s) standardised.")

    elif input_path:
        src = Path(input_path)
        dest = (out_dir / src.name) if out_dir else src
        art_w, art_h = standardise_image(src, dest)
        click.echo(f"{src.name}: {art_w}x{art_h} artwork on {canvas_w}x{canvas_h} canvas -> {dest}")

    elif input_dir:
        src_dir = Path(input_dir)
        for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
            images.extend(src_dir.glob(ext))
        click.echo(f"Standardising {len(images)} images in {src_dir}...")
        count = _process_list(images, in_place=out_dir is None, output_dir=out_dir)
        click.echo(f"Done — {count} image(s) standardised.")

    elif artist_slug:
        sel = selected_dir(artist_slug)
        if not sel.exists():
            raw = OUTPUT_DIR / "raw" / artist_slug
            if raw.exists():
                click.echo(f"No selected images; using raw output from {raw}")
                sel = raw
            else:
                raise click.ClickException(
                    f"No images found for {artist_slug}. Run generate first."
                )
        for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
            images.extend(sel.rglob(ext))
        click.echo(f"Standardising {len(images)} image(s) for {artist_slug}...")
        count = _process_list(images, in_place=out_dir is None, output_dir=out_dir)
        click.echo(f"Done — {count} image(s) standardised.")

    else:
        raise click.ClickException(
            "Provide one of: --public, --input, --input-dir, --artist"
        )
