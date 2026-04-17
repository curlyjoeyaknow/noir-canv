"""Output paths for pipeline stages.

All paths use pathlib.Path for cross-platform compatibility.
Helper functions create directories on demand and return the Path.
"""

from __future__ import annotations

import re
from pathlib import Path

_SAFE_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]*$")


# ---------------------------------------------------------------------------
# Root directories (derived from file location in the package tree)
# pipeline/src/pipeline/lib/paths.py → parents[4] = project root
# ---------------------------------------------------------------------------

PROJECT_ROOT: Path = Path(__file__).resolve().parents[4]
OUTPUT_DIR: Path = PROJECT_ROOT / "pipeline" / "output"
DATA_DIR: Path = PROJECT_ROOT / "data"
PUBLIC_DIR: Path = PROJECT_ROOT / "apps" / "web" / "public"
PUBLIC_IMAGES_DIR: Path = PUBLIC_DIR / "images"

CONTENT_DIR: Path = PROJECT_ROOT / "pipeline" / "content"
ARTISTS_DIR: Path = CONTENT_DIR / "artists"
EXAMPLES_DIR: Path = PROJECT_ROOT / "examples"

# ---------------------------------------------------------------------------
# Example subfolder names — canonical names used at every pipeline stage.
# Each artist folder (examples/{Artist_Name}/) contains these subfolders:
#   artwork/       — flat artwork images; used as style references for generation
#   framed/        — front-on framed images; used as IP-Adapter framing references
#   mockups/       — angled 3-D framed images; used as reference for angled mockups
#   print_quality/ — high-res reference images; used as quality targets for upscaling
# ---------------------------------------------------------------------------

EXAMPLES_ARTWORK_SUBDIR: str = "artwork"
EXAMPLES_FRAMED_SUBDIR: str = "framed"
EXAMPLES_MOCKUPS_SUBDIR: str = "mockups"
EXAMPLES_PRINT_QUALITY_SUBDIR: str = "print_quality"


# ---------------------------------------------------------------------------
# Output subdirectory constants
# ---------------------------------------------------------------------------

MOCKUPS_DIR: Path = OUTPUT_DIR / "mockups"
MOCKUPS_FRAMED_DIR: Path = MOCKUPS_DIR / "framed"
MOCKUPS_ROOMS_DIR: Path = MOCKUPS_DIR / "rooms"


# ---------------------------------------------------------------------------
# Directory builders (create on access)
# ---------------------------------------------------------------------------

def _validate_slug(slug: str) -> None:
    """Reject slugs that could escape the intended directory."""
    if not _SAFE_SLUG_RE.match(slug):
        raise ValueError(f"Invalid slug for path construction: {slug!r}")


def raw_dir(artist_slug: str, piece_slug: str) -> Path:
    """Return (and create) raw generation output dir for a piece."""
    _validate_slug(artist_slug)
    _validate_slug(piece_slug)
    d = OUTPUT_DIR / "raw" / artist_slug / piece_slug
    d.mkdir(parents=True, exist_ok=True)
    return d


def selected_dir(artist_slug: str) -> Path:
    """Return (and create) selected/curated output dir for an artist."""
    _validate_slug(artist_slug)
    d = OUTPUT_DIR / "selected" / artist_slug
    d.mkdir(parents=True, exist_ok=True)
    return d


def print_dir() -> Path:
    """Return (and create) print-resolution output dir."""
    d = OUTPUT_DIR / "print"
    d.mkdir(parents=True, exist_ok=True)
    return d


def public_pieces_dir() -> Path:
    """Return (and create) public images dir for gallery pieces."""
    d = PUBLIC_IMAGES_DIR / "pieces"
    d.mkdir(parents=True, exist_ok=True)
    return d


def public_artists_dir(artist_slug: str) -> Path:
    """Return (and create) public images dir for an artist."""
    _validate_slug(artist_slug)
    d = PUBLIC_IMAGES_DIR / "artists" / artist_slug
    d.mkdir(parents=True, exist_ok=True)
    return d


def mockups_framed_dir() -> Path:
    """Return (and create) framed mockup output dir."""
    MOCKUPS_FRAMED_DIR.mkdir(parents=True, exist_ok=True)
    return MOCKUPS_FRAMED_DIR


def mockups_rooms_dir() -> Path:
    """Return (and create) room mockup output dir."""
    MOCKUPS_ROOMS_DIR.mkdir(parents=True, exist_ok=True)
    return MOCKUPS_ROOMS_DIR


def artist_content_dir(artist_slug: str) -> Path:
    """Return path to an artist's YAML config (does not create)."""
    _validate_slug(artist_slug)
    return ARTISTS_DIR / f"{artist_slug}.yaml"


# ---------------------------------------------------------------------------
# Path validation / sandboxing
# ---------------------------------------------------------------------------

_ALLOWED_ROOTS: tuple[Path, ...] = (OUTPUT_DIR, PUBLIC_DIR, DATA_DIR)


def validate_output_path(path: Path) -> Path:
    """Ensure a path is within one of the allowed output directories.

    Resolves the path and checks it starts with OUTPUT_DIR, PUBLIC_DIR,
    or DATA_DIR.  Raises ValueError if the path escapes the sandbox.
    """
    resolved = path.resolve()
    for root in _ALLOWED_ROOTS:
        try:
            resolved.relative_to(root.resolve())
            return resolved
        except ValueError:
            continue
    allowed = ", ".join(str(r) for r in _ALLOWED_ROOTS)
    raise ValueError(f"Path {resolved} is outside allowed directories: {allowed}")
