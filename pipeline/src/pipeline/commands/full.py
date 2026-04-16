"""Run the full artist creation pipeline end-to-end.

Phases: create-artist -> avatar -> artist-studio -> generate pieces ->
        frame mockups -> image variants
All using Gemini API (no local GPU required).
"""

from __future__ import annotations

from pathlib import Path

import click

from pipeline.commands.artist_studio import run_artist_studio
from pipeline.commands.avatar import run_avatar
from pipeline.commands.create_artist import create_artist as create_artist_cmd
from pipeline.commands.generate import run_generate
from pipeline.lib.config import load_artist_config
from pipeline.lib.image_variants import generate_variants
from pipeline.lib.mockup import FRAME_STYLES, generate_mockups
from pipeline.lib.paths import OUTPUT_DIR, PUBLIC_IMAGES_DIR


@click.command("full")
@click.option("--base-artist", required=True, help="Example folder name for style reference.")
@click.option("--pseudonym", default=None, help="Custom artist name (auto-generated if omitted).")
@click.option("--slug", "slug_override", default=None, help="Custom URL slug.")
@click.option("--pieces", "piece_count", default=6, type=int, help="Number of art pieces to generate.")
@click.option("--max-style-refs", default=5, type=int, help="Style reference images for piece generation.")
@click.option(
    "--pricing-tier",
    type=click.Choice(["affordable", "mid-range", "premium"]),
    default="mid-range",
)
@click.option("--edition-size", type=int, default=25, help="Default edition size.")
@click.option("--gemini-model", default="gemini-3.1-flash-image-preview", help="Gemini model for image generation.")
@click.option("--skip-avatar", is_flag=True, help="Skip portrait generation.")
@click.option("--skip-studio", is_flag=True, help="Skip studio shots.")
@click.option("--skip-pieces", is_flag=True, help="Skip piece generation.")
def full(
    base_artist: str,
    pseudonym: str | None,
    slug_override: str | None,
    piece_count: int,
    max_style_refs: int,
    pricing_tier: str,
    edition_size: int,
    gemini_model: str,
    skip_avatar: bool,
    skip_studio: bool,
    skip_pieces: bool,
) -> None:
    """Run the full artist creation pipeline (all phases, Gemini API only).

    Creates: artist profile, portrait, studio shots, art pieces,
    framed mockups (flat + angled), and all size variants.
    """
    click.echo("=" * 60)
    click.echo("NOIR CANVAS -- Full Artist Pipeline")
    click.echo("=" * 60)

    # Phase 1: Create Artist
    click.echo("\n--- Phase 1: Create Artist ---")
    ctx = click.Context(create_artist_cmd)
    ctx.invoke(
        create_artist_cmd,
        base_artist=base_artist,
        pseudonym=pseudonym,
        slug_override=slug_override,
        use_gemini=True,
        pricing_tier=pricing_tier,
        edition_size=edition_size,
    )

    artist_slug = slug_override
    if not artist_slug:
        import re
        if pseudonym:
            artist_slug = re.sub(r"[^a-z0-9]+", "-", pseudonym.lower()).strip("-")
        else:
            artist_slug = _find_latest_artist(base_artist)

    if not artist_slug:
        raise click.ClickException("Could not determine artist slug")

    click.echo(f"\nArtist created: {artist_slug}")

    # Phase 2a: Generate Portrait
    artist_media_paths: list[Path] = []
    if not skip_avatar:
        click.echo("\n--- Phase 2a: Generate Portrait ---")
        portrait_dir = OUTPUT_DIR / "avatars" / artist_slug
        portrait_dir.mkdir(parents=True, exist_ok=True)
        portraits = run_avatar(
            artist_slug, output_path=portrait_dir, count=1,
            use_gemini=True, gemini_model=gemini_model,
        )
        artist_media_paths.extend(portraits)
        if portraits:
            click.echo(f"Portrait: {portraits[0]}")
    else:
        click.echo("\n--- Phase 2a: Portrait SKIPPED ---")

    # Phase 2b: Generate Studio Shots
    if not skip_studio:
        click.echo("\n--- Phase 2b: Generate Studio Shots ---")
        studio_dir = OUTPUT_DIR / "artist_studio" / artist_slug
        studio_dir.mkdir(parents=True, exist_ok=True)
        for mode in ("working", "holding", "creative-space"):
            click.echo(f"  Generating: {mode}...")
            studio_paths = run_artist_studio(
                artist_slug, output_path=studio_dir, mode=mode,
                use_gemini=True, gemini_model=gemini_model,
            )
            artist_media_paths.extend(studio_paths)
    else:
        click.echo("\n--- Phase 2b: Studio Shots SKIPPED ---")

    # Phase 2c: Process artist media into size variants
    if artist_media_paths:
        click.echo("\n--- Phase 2c: Process Artist Media Variants ---")
        artist_processed = PUBLIC_IMAGES_DIR / "artists" / artist_slug
        for media_path in artist_media_paths:
            generate_variants(
                media_path, artist_processed, media_path.stem,
                variants=["gallery", "card", "thumb"],
            )
        click.echo(f"Artist media variants saved to {artist_processed}")

    # Phase 3: Generate Pieces
    saved_pieces: list[Path] = []
    if not skip_pieces:
        click.echo(f"\n--- Phase 3: Generate {piece_count} Pieces ---")
        saved_pieces = run_generate(
            artist_slug, count=piece_count, max_style_refs=max_style_refs,
        )
        click.echo(f"Generated {len(saved_pieces)} pieces")

        # Phase 3b: Piece size variants
        click.echo("\n--- Phase 3b: Generate Piece Variants ---")
        processed_dir = OUTPUT_DIR / "processed" / artist_slug / "pieces"
        for piece_path in saved_pieces:
            generate_variants(piece_path, processed_dir, piece_path.stem)
            click.echo(f"  {piece_path.stem}: print, gallery, card, thumb, placeholder")
        click.echo(f"All variants saved to {processed_dir}")
    else:
        click.echo("\n--- Phase 3: Pieces SKIPPED ---")

    # Phase 4: Frame mockups (flat + angled, multiple frame styles)
    if saved_pieces:
        click.echo("\n--- Phase 4: Frame Mockups ---")
        mockup_dir = OUTPUT_DIR / "mockups" / artist_slug
        mockup_styles = ["natural-wood", "black", "white", "dark-wood"]
        all_mockup_paths: list[Path] = []

        for piece_path in saved_pieces:
            slug = piece_path.stem
            paths = generate_mockups(
                piece_path, mockup_dir, slug, styles=mockup_styles,
            )
            all_mockup_paths.extend(paths)
            click.echo(
                f"  {slug}: {len(mockup_styles)} styles x 2 views = {len(paths)} mockups"
            )
        click.echo(f"Total: {len(all_mockup_paths)} mockups")

        # Phase 4b: Mockup size variants
        click.echo("\n--- Phase 4b: Generate Mockup Variants ---")
        mockup_processed = OUTPUT_DIR / "processed" / artist_slug / "mockups"
        for img_path in all_mockup_paths:
            generate_variants(
                img_path, mockup_processed, img_path.stem,
                variants=["gallery", "card", "thumb"],
            )
        click.echo(f"  Processed {len(all_mockup_paths)} mockup images into variants")

    # Summary
    click.echo("\n" + "=" * 60)
    click.echo(f"COMPLETE: {artist_slug}")
    click.echo(f"  Config:  pipeline/content/artists/{artist_slug}.yaml")
    click.echo(f"  Data:    data/artists.json (updated)")
    if not skip_avatar:
        click.echo(f"  Portrait: pipeline/output/avatars/{artist_slug}/")
    if not skip_studio:
        click.echo(f"  Studio:   pipeline/output/artist_studio/{artist_slug}/")
    if saved_pieces:
        click.echo(f"  Pieces:   pipeline/output/raw/{artist_slug}/")
        click.echo(f"  Mockups:  pipeline/output/mockups/{artist_slug}/")
        click.echo(f"  Variants: pipeline/output/processed/{artist_slug}/")
    click.echo("=" * 60)
    click.echo("\nNext steps:")
    click.echo(f"  1. Review & curate:  pipeline curate --artist {artist_slug}")
    click.echo(f"  2. Register to gallery: pipeline register --artist {artist_slug}")


def _find_latest_artist(base_artist: str) -> str | None:
    """Find the most recently created artist that uses the given base artist."""
    from pipeline.lib.config import load_artist_configs

    matching = [
        a for a in load_artist_configs()
        if base_artist in a.example_artists
    ]
    if matching:
        return matching[-1].slug
    return None
