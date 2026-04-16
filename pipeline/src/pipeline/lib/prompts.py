"""Prompt templates for Gemini API calls and artist/piece text generation.

Templates for: artist bio, artist statement, piece description,
piece subjects, and image generation prompts.

Also provides shared Gemini text generation helpers and pseudonym generation
so both the CLI and the API layer can call them without importing private
CLI-layer functions.
"""

from __future__ import annotations

import logging
import random
import re

from pipeline.lib.config import ArtistConfig, get_settings, load_piece_override
from pipeline.lib.schemas import Piece

try:
    from google import genai
except ImportError:
    genai = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

_FIRST_NAMES: list[str] = [
    "Kai", "Elara", "Marcus", "Ivy", "Ren", "Leo", "Sienna", "Jasper",
    "Vera", "Atlas", "Luna", "Orion", "Nova", "Cedar", "Willow", "River",
]
_LAST_NAMES: list[str] = [
    "Voss", "Sato", "Chen", "Delacroix", "Nakamura", "Strand", "Blake",
    "Reed", "Cross", "Vale", "Stone", "Wilde", "Ash", "Lane", "Gray",
]


# ---------------------------------------------------------------------------
# Shared generation helpers
# ---------------------------------------------------------------------------

def generate_text_with_gemini(prompt: str) -> str | None:
    """Call Gemini for text generation. Returns None if unavailable."""
    if genai is None:
        return None
    settings = get_settings()
    if not settings.gemini_api_key:
        return None
    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[prompt],
        )
        return response.text.strip() if response.text else None
    except Exception:
        logger.warning("Gemini text generation failed, using fallback")
        return None


def generate_pseudonym(exclude_slugs: set[str]) -> tuple[str, str]:
    """Generate a random pseudonym that isn't already taken.

    Returns a (name, slug) tuple. Raises ValueError after 1000 attempts.
    """
    for _ in range(1000):
        first = random.choice(_FIRST_NAMES)
        last = random.choice(_LAST_NAMES)
        name = f"{first} {last}"
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        if slug not in exclude_slugs:
            return name, slug
    raise ValueError("Could not generate unique pseudonym after 1000 attempts")


# ---------------------------------------------------------------------------
# Image generation prompts
# ---------------------------------------------------------------------------

def build_prompt(piece: Piece, artist: ArtistConfig) -> str:
    """Build a full image generation prompt from piece metadata and artist config.

    Checks for a piece-level prompt override first. Falls back to building
    a rich prompt that combines the piece subject with the artist's style
    characteristics. When style reference images are sent alongside (Gemini
    multimodal), this prompt describes the *subject* while the images
    communicate the *style*.
    """
    override = load_piece_override(piece.slug)
    if override and override.prompt:
        return f"{artist.prompt_prefix}{override.prompt}{artist.prompt_suffix}"

    subject = f"{piece.title}: {piece.description}" if piece.description else piece.title
    style_desc = artist.style_reference if artist.style_reference else "original artwork"
    return (
        f"{artist.prompt_prefix}"
        f"Create an artwork depicting: {subject}. "
        f"Artistic style: {style_desc}. "
        f"The piece should feel like it belongs in the same portfolio and gallery exhibition "
        f"as the artist's other works — consistent palette, technique, and aesthetic sensibility."
        f"{artist.prompt_suffix}"
    )


# ---------------------------------------------------------------------------
# Artist text generation templates
# ---------------------------------------------------------------------------

def artist_bio_prompt(name: str, style: str, influences: list[str]) -> str:
    """Build a Gemini prompt to generate an artist biography."""
    influences_str = ", ".join(influences) if influences else "various contemporary movements"
    return (
        f"Write a concise 2-3 paragraph biography for a fictional contemporary artist "
        f"named {name}. Their artistic style is characterized by {style}. "
        f"Their influences include {influences_str}. "
        f"The bio should feel authentic and compelling, suitable for a premium art gallery. "
        f"Do not mention AI or generated art. Write in third person. "
        f"Return only the biography text, no headers or formatting."
    )


def artist_statement_prompt(name: str, style: str) -> str:
    """Build a Gemini prompt to generate an artist statement."""
    return (
        f"Write a first-person artist statement for {name}, a contemporary artist "
        f"whose work is characterized by {style}. "
        f"The statement should be 1-2 paragraphs, introspective and poetic. "
        f"It should convey artistic intent and creative philosophy. "
        f"Do not mention AI or digital tools. "
        f"Return only the statement text, no headers or formatting."
    )


# ---------------------------------------------------------------------------
# Piece text generation templates
# ---------------------------------------------------------------------------

def piece_description_prompt(title: str, artist_name: str, style: str) -> str:
    """Build a Gemini prompt to generate a piece description."""
    return (
        f"Write a 2-3 sentence description for an artwork titled \"{title}\" "
        f"by {artist_name}. The artist's style is characterized by {style}. "
        f"The description should be evocative and suitable for a premium art gallery listing. "
        f"Do not mention AI or generation. "
        f"Return only the description text."
    )


def piece_subjects_prompt(style: str, count: int = 8) -> str:
    """Build a Gemini prompt to suggest new piece subjects for an artist's style."""
    return (
        f"Suggest {count} original artwork subjects for an artist whose style is "
        f"characterized by {style}. Each subject should be a concise 3-8 word title "
        f"or concept that would make a compelling standalone art piece. "
        f"Return subjects as a JSON array of strings. Example format: "
        f'["Twilight Over Still Waters", "The Weight of Forgotten Letters"]. '
        f"Only return the JSON array, no other text."
    )


# ---------------------------------------------------------------------------
# Fallback template-based generation (no API needed)
# ---------------------------------------------------------------------------

def fallback_bio(name: str, style: str) -> str:
    """Generate a template-based bio when Gemini is unavailable."""
    return (
        f"{name} is an artist whose work draws on {style}. "
        "Their pieces explore the boundaries between tradition and contemporary expression, "
        "creating compositions that invite contemplation and connection."
    )


def fallback_statement() -> str:
    """Generate a generic artist statement when Gemini is unavailable."""
    return (
        "I seek to capture the in-between\u2014the moment before form settles, "
        "where possibility still breathes."
    )
