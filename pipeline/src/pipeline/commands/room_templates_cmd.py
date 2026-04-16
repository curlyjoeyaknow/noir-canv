"""Generate and manage reusable room templates for artwork mockups.

Templates are generated once via Gemini and reused for every piece.
Compositing is instant (PIL perspective transform, no API calls).
"""

from __future__ import annotations

from pathlib import Path

import click

from pipeline.lib.room_templates import (
    composite_art_into_room,
    generate_room_templates,
    load_templates,
)


@click.group("room-templates")
def room_templates_group() -> None:
    """Manage reusable room templates for artwork mockups."""


@room_templates_group.command("generate")
@click.option("--gemini-model", default="gemini-3.1-flash-image-preview", help="Gemini model.")
def generate_templates(gemini_model: str) -> None:
    """Generate all room template images (one-time operation)."""
    click.echo("Generating room templates via Gemini API...")
    templates = generate_room_templates(gemini_model=gemini_model)
    click.echo(f"Generated {len(templates)} room template(s)")
    for t in templates:
        click.echo(f"  {t.slug}: {t.name}")


@room_templates_group.command("list")
def list_templates() -> None:
    """List all available room templates."""
    templates = load_templates()
    if not templates:
        click.echo("No templates generated yet. Run: pipeline room-templates generate")
        return
    click.echo(f"{len(templates)} template(s):")
    for t in templates:
        exists = t.full_path.exists()
        status = "OK" if exists else "MISSING"
        click.echo(f"  [{status}] {t.slug}: {t.name} ({t.wall_color}, {t.lighting})")


@room_templates_group.command("composite")
@click.option("--input", "input_path", required=True, type=click.Path(exists=True),
              help="Framed artwork image.")
@click.option("--piece-slug", required=True, help="Piece slug for output naming.")
@click.option("--output-dir", default=None, type=click.Path(), help="Output directory.")
@click.option("--template", "template_slug", default=None, help="Specific template (default: all).")
def composite(
    input_path: str,
    piece_slug: str,
    output_dir: str | None,
    template_slug: str | None,
) -> None:
    """Composite framed artwork into room template(s)."""
    templates = load_templates()
    if not templates:
        raise click.ClickException("No templates. Run: pipeline room-templates generate")

    if template_slug:
        templates = [t for t in templates if t.slug == template_slug]
        if not templates:
            raise click.ClickException(f"Template not found: {template_slug}")

    from pipeline.lib.paths import mockups_rooms_dir
    out_dir = Path(output_dir) if output_dir else mockups_rooms_dir()

    framed = Path(input_path)
    for t in templates:
        if not t.full_path.exists():
            click.echo(f"  Skipping {t.slug} (template image missing)")
            continue
        out_path = out_dir / f"{piece_slug}-{t.slug}.png"
        composite_art_into_room(framed, t, out_path)
        click.echo(f"  {t.slug}: {out_path}")

    click.echo(f"Composited into {len(templates)} room(s)")


def run_composite_all(
    framed_path: Path,
    piece_slug: str,
    output_dir: Path | None = None,
) -> list[Path]:
    """Composite framed art into all available templates. Returns output paths."""
    templates = load_templates()
    if not templates:
        return []

    from pipeline.lib.paths import mockups_rooms_dir
    out_dir = output_dir or mockups_rooms_dir()
    results: list[Path] = []

    for t in templates:
        if not t.full_path.exists():
            continue
        out_path = out_dir / f"{piece_slug}-{t.slug}.png"
        composite_art_into_room(framed_path, t, out_path)
        results.append(out_path)

    return results
