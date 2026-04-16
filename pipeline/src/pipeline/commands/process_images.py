"""Process generated images into multiple size variants for gallery use.

Takes raw generation output and produces:
  - print/     4096px (canvas printing)
  - gallery/   1600px (detail page hero)
  - card/       800px (grid cards, carousel)
  - thumb/      400px (thumbnails)
  - placeholder/ 40px (blur-up placeholders)
"""

from __future__ import annotations

from pathlib import Path

import click

from pipeline.lib.image_variants import (
    VARIANT_SIZES,
    generate_variants,
    generate_variants_batch,
)
from pipeline.lib.paths import OUTPUT_DIR, public_pieces_dir


@click.command("process-images")
@click.option("--input", "input_path", required=False, type=click.Path(exists=True),
              help="Single image file to process.")
@click.option("--input-dir", required=False, type=click.Path(exists=True),
              help="Directory of images to process (batch mode).")
@click.option("--artist", "artist_slug", default=None,
              help="Process all selected images for an artist.")
@click.option("--output-dir", default=None, type=click.Path(),
              help="Output root (default: pipeline/output/processed/).")
@click.option("--public", "to_public", is_flag=True,
              help="Output directly to apps/web/public/images/pieces/.")
@click.option("--format", "format_ext", default="webp",
              type=click.Choice(["webp", "png", "jpg"]),
              help="Output image format (default: webp).")
@click.option("--quality", default=90, type=int, help="Output quality 1-100 (default: 90).")
@click.option("--variants", default=None, help="Comma-separated variant names to generate (default: all).")
def process_images(
    input_path: str | None,
    input_dir: str | None,
    artist_slug: str | None,
    output_dir: str | None,
    to_public: bool,
    format_ext: str,
    quality: int,
    variants: str | None,
) -> None:
    """Process images into multiple size variants for the gallery.

    Generates: print (4096px), gallery (1600px), card (800px),
    thumb (400px), and placeholder (40px blur-up) from each source image.
    """
    variant_list = variants.split(",") if variants else None
    if variant_list:
        invalid = [v for v in variant_list if v not in VARIANT_SIZES]
        if invalid:
            raise click.ClickException(
                f"Unknown variant(s): {', '.join(invalid)}. "
                f"Valid: {', '.join(VARIANT_SIZES.keys())}"
            )

    if to_public:
        out_root = public_pieces_dir()
    elif output_dir:
        out_root = Path(output_dir)
    else:
        out_root = OUTPUT_DIR / "processed"

    if input_path:
        src = Path(input_path)
        result = generate_variants(
            src, out_root, src.stem,
            variants=variant_list, quality=quality, format_ext=format_ext,
        )
        _print_result(result)

    elif input_dir:
        src_dir = Path(input_dir)
        results = generate_variants_batch(
            src_dir, out_root,
            variants=variant_list, quality=quality, format_ext=format_ext,
        )
        click.echo(f"Processed {len(results)} image(s)")
        for r in results:
            _print_result(r)

    elif artist_slug:
        from pipeline.lib.paths import selected_dir
        sel_dir = selected_dir(artist_slug)
        if not sel_dir.exists() or not list(sel_dir.glob("*.png")):
            raw_dir = OUTPUT_DIR / "raw" / artist_slug
            if raw_dir.exists():
                click.echo(f"No selected images; using raw output from {raw_dir}")
                sel_dir = raw_dir
            else:
                raise click.ClickException(
                    f"No images found for {artist_slug}. Run generate first."
                )

        all_images: list[Path] = []
        for ext in ("*.png", "*.jpg", "*.webp"):
            all_images.extend(sel_dir.rglob(ext))

        if not all_images:
            raise click.ClickException(f"No images found in {sel_dir}")

        click.echo(f"Processing {len(all_images)} image(s) for {artist_slug}")
        for src in sorted(all_images):
            result = generate_variants(
                src, out_root, src.stem,
                variants=variant_list, quality=quality, format_ext=format_ext,
            )
            _print_result(result)

    else:
        raise click.ClickException("Provide --input, --input-dir, or --artist")


def _print_result(result: "ImageVariants") -> None:
    """Print generated variant paths."""
    from pipeline.lib.image_variants import ImageVariants
    click.echo(f"  {result.source.name}:")
    for field in ("print_path", "gallery", "card", "thumb", "placeholder"):
        path = getattr(result, field, None)
        if path and isinstance(path, Path):
            from PIL import Image
            img = Image.open(path)
            click.echo(f"    {field:12s} {img.width}x{img.height}  {path}")
