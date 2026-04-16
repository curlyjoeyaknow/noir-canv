"""Create virtual artist profiles from example reference folders.

Generates a pipeline YAML config and a gallery-facing JSON entry.
Optionally uses Gemini API for bio/statement text generation.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import click
import yaml

from pipeline.lib.config import (
    ArtistConfig,
    list_example_folders,
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
from pipeline.lib.schemas import Artist, ArtistStyle, PricingTier

logger = logging.getLogger(__name__)

_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]*$")


STYLE_DESCRIPTIONS: dict[str, str] = {
    "ANDY_KEHOE": "dreamlike forest scenes with soft luminous colors, ethereal cloaked figures, layered transparency effects, romantic atmospheric lighting, and enchanted woodland settings",
    "JAMES_JEAN": "intricate flowing linework with Art Nouveau influences, surreal figurative compositions, muted pastel palettes with organic flowing forms, layered botanical and anatomical motifs",
    "AUDREY_KAWASAKI": "delicate female figures on wood panel, Japanese-inspired linework, ethereal skin tones, flowing hair, minimalist backgrounds with gold leaf accents",
    "MARK_RYDEN": "pop surrealism with porcelain-skinned figures, wide-eyed characters, Victorian and carnival imagery, hyper-detailed oil painting technique, candy-colored palettes",
    "SHEPARD_FAIREY": "bold graphic propaganda-style posters, high-contrast red/black/cream palettes, geometric patterns, political iconography, screen-print aesthetic",
    "JEREMY_GEDDES": "hyperrealistic astronaut figures in surreal zero-gravity scenarios, photorealistic oil painting technique, cosmic isolation, muted earth tones with dramatic lighting",
    "JOAN_CORNELLA": "minimalist comic-style illustration, bright flat colors, dark humor, simple geometric characters, clean lines, satirical absurdist scenarios",
    "SHAG": "mid-century modern illustration, retro cocktail culture, geometric stylized figures, bold saturated colors, tiki and space-age aesthetics",
    "TIM_DOYLE": "detailed black-and-white architectural illustrations, urban landscapes, pop culture landmarks reimagined, intricate cross-hatching, night scenes with dramatic contrast",
}


def _folder_to_style(folder_name: str) -> str:
    """Convert folder name to a detailed style description."""
    if folder_name in STYLE_DESCRIPTIONS:
        return STYLE_DESCRIPTIONS[folder_name]
    readable = folder_name.replace("_", " ").title()
    return f"{readable}-inspired contemporary art with distinctive visual style and technique"


@click.command("create-artist")
@click.option("--base-artist", required=True, help="Example folder name for style reference.")
@click.option("--pseudonym", default=None, help="Custom artist name (auto-generated if omitted).")
@click.option("--slug", "slug_override", default=None, help="Custom URL slug.")
@click.option("--use-gemini/--no-gemini", default=True, help="Use Gemini API for bio/statement.")
@click.option(
    "--pricing-tier",
    type=click.Choice(["affordable", "mid-range", "premium"]),
    default="mid-range",
)
@click.option("--edition-size", type=int, default=25, help="Default edition size.")
def create_artist(
    base_artist: str,
    pseudonym: str | None,
    slug_override: str | None,
    use_gemini: bool,
    pricing_tier: str,
    edition_size: int,
) -> None:
    """Create a new virtual artist from an example reference folder."""
    available = list_example_folders()
    if base_artist not in available:
        available_str = ", ".join(available) if available else "(none found)"
        raise click.ClickException(
            f"Example folder not found: {base_artist}. Available: {available_str}"
        )

    existing_slugs = {a.slug for a in load_artist_configs()}

    if pseudonym and slug_override:
        name, slug_val = pseudonym, slug_override
    elif pseudonym:
        name = pseudonym
        slug_val = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    else:
        name, slug_val = generate_pseudonym(existing_slugs)

    if not _SLUG_RE.match(slug_val):
        raise click.ClickException(f"Invalid slug: {slug_val}")
    if slug_val in existing_slugs:
        raise click.ClickException(f"Artist slug already exists: {slug_val}")

    style = _folder_to_style(base_artist)

    bio: str | None = None
    statement: str | None = None
    if use_gemini:
        bio = generate_text_with_gemini(
            artist_bio_prompt(name, style, [base_artist.replace("_", " ")])
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
        example_artists=[base_artist],
        example_ref_folder="main",
        style_reference=style,
        model_type="gemini",
        prompt_prefix="Fine art, gallery quality, ",
        prompt_suffix=f", inspired by {style.lower()}, cohesive portfolio aesthetic",
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
    click.echo(f"Created pipeline config: {config_path}")

    gallery_artist = Artist.model_validate({
        "slug": slug_val,
        "name": name,
        "bio": bio,
        "artistStatement": statement,
        "portraitUrl": f"/images/artists/{slug_val}/portrait.png",
        "influences": [base_artist.replace("_", " ")],
        "style": {
            "medium": "mixed media",
            "palette": "varied",
            "subjects": style,
        },
        "pricingTier": pricing_tier,
        "defaultEditionSize": edition_size,
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
    click.echo(f"Added {name} ({slug_val}) to {artists_path}")
