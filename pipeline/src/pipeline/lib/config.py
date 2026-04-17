"""Application settings and artist/piece data loading.

Settings are loaded from environment variables via pydantic-settings.
Data loading functions read YAML configs and JSON data files,
returning validated Pydantic models.

Pipeline-internal models (ArtistConfig, PieceOverride) live here
because they represent pipeline YAML configs — not the gallery-facing
schemas in schemas.py which mirror packages/shared/schemas/.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from pipeline.lib.paths import (
    ARTISTS_DIR,
    CONTENT_DIR,
    DATA_DIR,
    EXAMPLES_DIR,
    EXAMPLES_ARTWORK_SUBDIR,
    EXAMPLES_FRAMED_SUBDIR,
    EXAMPLES_MOCKUPS_SUBDIR,
    EXAMPLES_PRINT_QUALITY_SUBDIR,
)
from pipeline.lib.schemas import Piece

logger = logging.getLogger(__name__)

_SAFE_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]*$")
# Ref-folder names may contain underscores (e.g. print_quality).
_SAFE_REF_FOLDER_RE = re.compile(r"^[a-z][a-z0-9_-]*$")
_SAFE_FOLDER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_&' -]*$")


# ---------------------------------------------------------------------------
# Pipeline-internal models (YAML configs, not gallery schemas)
# ---------------------------------------------------------------------------

class ArtistConfig(BaseModel):
    """Artist generation config from pipeline/content/artists/{slug}.yaml.

    This is the pipeline-side config used during generation.  The gallery-
    facing Artist schema lives in schemas.py and is written to data/.
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    slug: str
    example_artists: list[str] = Field(default_factory=list)
    style_reference: str = ""
    prompt_prefix: str = ""
    prompt_suffix: str = ""
    negative_prompt: str = "busy, cluttered, photorealistic, text, watermark"
    model_id: str = "stabilityai/stable-diffusion-xl-base-1.0"
    model_type: str = "sdxl"
    ip_adapter_scale: float = 0.7
    ip_adapter_blend_count: int = 1
    ip_adapter_weight: str | None = None
    ip_adapter_image_encoder_folder: str | None = None
    flux_ip_adapter_repo: str | None = None
    flux_ip_adapter_weight: str | None = None
    gemini_model: str | None = None
    lightning_steps: int | None = None
    example_ref_folder: str | None = None
    steps: int = 30
    cfg_scale: float = 7.5
    bio: str | None = None
    statement: str | None = None


class PieceOverride(BaseModel):
    """Optional per-piece override (pipeline/content/pieces/{slug}.yaml)."""

    model_config = ConfigDict(extra="forbid")

    prompt: str | None = None


# ---------------------------------------------------------------------------
# Settings (environment variables)
# ---------------------------------------------------------------------------

class PipelineSettings(BaseSettings):
    """Pipeline configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        extra="forbid",
        env_file=str(Path(__file__).resolve().parents[4] / ".env"),
        env_file_encoding="utf-8",
    )

    gemini_api_key: str = Field(default="", description="Google Gemini API key.")
    pipeline_api_secret: str = Field(
        default="",
        description="Shared secret for mutation endpoints. API rejects mutations when empty.",
    )
    comfyui_url: str = Field(default="", description="ComfyUI server base URL (e.g. http://127.0.0.1:8188).")
    allowed_origins: str = Field(default="", description="Comma-separated CORS origins from environment.")


_settings: PipelineSettings | None = None


def get_settings() -> PipelineSettings:
    """Return cached singleton settings instance."""
    global _settings  # noqa: PLW0603
    if _settings is None:
        _settings = PipelineSettings()
    return _settings


_IMAGE_GLOBS: tuple[str, ...] = ("*.jpg", "*.jpeg", "*.png", "*.webp")


# ---------------------------------------------------------------------------
# Data loading — artist configs
# ---------------------------------------------------------------------------

def load_artist_config(slug: str) -> ArtistConfig:
    """Load and validate a single artist pipeline config by slug."""
    _validate_slug(slug)
    path = ARTISTS_DIR / f"{slug}.yaml"
    _assert_within(path, ARTISTS_DIR)
    if not path.exists():
        raise FileNotFoundError(f"Artist config missing: {path}")
    data = _read_yaml(path)
    if data is None:
        raise ValueError(f"Artist config is empty: {path}")
    return ArtistConfig.model_validate(data)


def load_artist_configs() -> list[ArtistConfig]:
    """Load all artist pipeline configs from content/artists/."""
    if not ARTISTS_DIR.exists():
        return []
    result: list[ArtistConfig] = []
    for path in sorted(ARTISTS_DIR.glob("*.yaml")):
        try:
            result.append(load_artist_config(path.stem))
        except (FileNotFoundError, ValueError) as exc:
            logger.warning("Skipping invalid artist config %s: %s", path.name, exc)
    return result


# ---------------------------------------------------------------------------
# Data loading — pieces
# ---------------------------------------------------------------------------

def load_pieces() -> list[Piece]:
    """Load and validate pieces from data/pieces.json."""
    path = DATA_DIR / "pieces.json"
    if not path.exists():
        raise FileNotFoundError(f"Pieces file missing: {path}")
    raw = _read_json(path)
    if not isinstance(raw, list):
        raise ValueError(f"Expected list of pieces in {path}, got {type(raw).__name__}")
    result: list[Piece] = []
    for i, entry in enumerate(raw):
        if entry is None:
            continue
        slug = _safe_slug(entry, i)
        try:
            result.append(Piece.model_validate(entry))
        except Exception as exc:
            raise ValueError(f"Invalid piece at index {i} (slug={slug}): {exc}") from exc
    return result


# ---------------------------------------------------------------------------
# Data loading — piece overrides
# ---------------------------------------------------------------------------

def load_piece_override(slug: str) -> PieceOverride | None:
    """Load optional piece override YAML. Returns None if missing or empty."""
    _validate_slug(slug)
    pieces_dir = CONTENT_DIR / "pieces"
    path = pieces_dir / f"{slug}.yaml"
    _assert_within(path, pieces_dir)
    if not path.exists():
        return None
    data = _read_yaml(path)
    if data is None:
        return None
    return PieceOverride.model_validate(data)


# ---------------------------------------------------------------------------
# Example images
# ---------------------------------------------------------------------------

def list_example_folders() -> list[str]:
    """Return sorted list of example artist folder names."""
    if not EXAMPLES_DIR.exists():
        return []
    return sorted(
        d.name
        for d in EXAMPLES_DIR.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    )


def get_example_images(
    example_artists: list[str],
    ref_folder: str | None = None,
    recursive: bool = False,
) -> list[Path]:
    """Return image paths from example artist folders.

    If ref_folder is set (e.g. 'main'), prefer {artist}/main/ over root.
    If recursive, glob from ref_folder and all subdirs.
    Falls back to root when subfolder is missing or empty.
    """
    images: list[Path] = []
    for name in example_artists:
        if not _SAFE_FOLDER_RE.match(name):
            raise ValueError(f"Invalid example artist folder name: {name!r}")
        base = EXAMPLES_DIR / name
        _assert_within(base, EXAMPLES_DIR)
        if not base.exists():
            continue
        if ref_folder:
            if not _SAFE_REF_FOLDER_RE.match(ref_folder):
                raise ValueError(f"Invalid ref folder name: {ref_folder!r}")
        folder = base / ref_folder if ref_folder else base
        if not folder.exists() or not folder.is_dir():
            folder = base
        artist_images: list[Path] = []
        for ext in _IMAGE_GLOBS:
            if recursive:
                artist_images.extend(folder.rglob(ext))
            else:
                artist_images.extend(folder.glob(ext))
        if not artist_images and ref_folder and folder != base:
            for ext in _IMAGE_GLOBS:
                artist_images.extend(base.glob(ext))
        images.extend(artist_images)
    return sorted(images)


# ---------------------------------------------------------------------------
# Per-stage example image helpers
# Each wraps get_example_images with the canonical subfolder for that stage.
# ---------------------------------------------------------------------------

def get_artwork_images(example_artists: list[str]) -> list[Path]:
    """Style reference images for generation (examples/{artist}/artwork/)."""
    return get_example_images(example_artists, ref_folder=EXAMPLES_ARTWORK_SUBDIR)


def get_framed_images(example_artists: list[str]) -> list[Path]:
    """Front-on framed reference images (examples/{artist}/framed/).

    Non-recursive: only the flat framed images, not angled subfolders.
    """
    return get_example_images(
        example_artists, ref_folder=EXAMPLES_FRAMED_SUBDIR, recursive=False,
    )


def get_mockup_images(example_artists: list[str]) -> list[Path]:
    """Angled 3-D mockup reference images (examples/{artist}/mockups/)."""
    return get_example_images(example_artists, ref_folder=EXAMPLES_MOCKUPS_SUBDIR)


def get_print_quality_images(example_artists: list[str]) -> list[Path]:
    """High-resolution print-quality reference images (examples/{artist}/print_quality/)."""
    return get_example_images(example_artists, ref_folder=EXAMPLES_PRINT_QUALITY_SUBDIR)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _read_json(path: Path) -> Any:
    """Read and parse a JSON file."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc


def _read_yaml(path: Path) -> Any:
    """Read and parse a YAML file."""
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc


def _safe_slug(entry: Any, index: int) -> str:
    """Extract slug from a dict entry, or return a positional placeholder."""
    if isinstance(entry, dict):
        return str(entry.get("slug", f"<index {index}>"))
    return f"<index {index}>"


def _validate_slug(slug: str) -> None:
    """Ensure slug is safe for filesystem path construction."""
    if not _SAFE_SLUG_RE.match(slug):
        raise ValueError(f"Invalid slug: {slug!r}")


def _assert_within(resolved: Path, root: Path) -> None:
    """Assert that resolved path stays within the expected root directory."""
    try:
        resolved.resolve().relative_to(root.resolve())
    except ValueError:
        raise ValueError(f"Path {resolved} escapes root {root}") from None
