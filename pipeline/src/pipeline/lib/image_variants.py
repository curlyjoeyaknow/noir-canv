"""Generate multiple image size variants from a base image.

Variant sizes:
  - print:       4096px long edge (for canvas printing)
  - gallery:     1600px long edge (piece detail page hero)
  - card:         800px long edge (grid cards, carousel)
  - thumb:        400px long edge (small thumbnails, lightbox grid)
  - placeholder:   40px long edge (blur-up placeholder, inline base64)

All downscales use Lanczos resampling for maximum quality.
Print upscale uses PIL Lanczos by default; Gemini 4K re-generation optional.
"""

from __future__ import annotations

import base64
import io
import logging
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageFilter

logger = logging.getLogger(__name__)

VARIANT_SIZES: dict[str, int] = {
    "print": 4096,
    "gallery": 1600,
    "card": 800,
    "thumb": 400,
    "placeholder": 40,
}


@dataclass
class ImageVariants:
    """Paths to all generated size variants."""

    source: Path
    print_path: Path | None = None
    gallery: Path | None = None
    card: Path | None = None
    thumb: Path | None = None
    placeholder: Path | None = None
    placeholder_base64: str | None = None


def _resize_to_long_edge(img: Image.Image, long_edge: int) -> Image.Image:
    """Resize image so its longest edge equals long_edge, preserving aspect ratio."""
    w, h = img.size
    if max(w, h) <= long_edge:
        if long_edge <= 100:
            return img.copy()
        return img.copy()

    if w >= h:
        new_w = long_edge
        new_h = int(h * (long_edge / w))
    else:
        new_h = long_edge
        new_w = int(w * (long_edge / h))

    return img.resize((new_w, new_h), Image.LANCZOS)


def _upscale_to_long_edge(img: Image.Image, long_edge: int) -> Image.Image:
    """Upscale image so its longest edge equals long_edge using Lanczos."""
    w, h = img.size
    if max(w, h) >= long_edge:
        return img.copy()

    if w >= h:
        new_w = long_edge
        new_h = int(h * (long_edge / w))
    else:
        new_h = long_edge
        new_w = int(w * (long_edge / h))

    return img.resize((new_w, new_h), Image.LANCZOS)


def _make_placeholder_base64(img: Image.Image) -> str:
    """Create a tiny blurred placeholder and return as data URI."""
    tiny = _resize_to_long_edge(img, 40)
    blurred = tiny.filter(ImageFilter.GaussianBlur(radius=2))
    buf = io.BytesIO()
    blurred.save(buf, format="WEBP", quality=20)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/webp;base64,{b64}"


def generate_variants(
    source_path: Path,
    output_dir: Path,
    slug: str,
    *,
    variants: list[str] | None = None,
    quality: int = 90,
    format_ext: str = "webp",
) -> ImageVariants:
    """Generate all size variants from a source image.

    Args:
        source_path: Path to the base image.
        output_dir: Root output directory (variants go into subdirectories).
        slug: Filename stem (e.g. 'kai-voss-001').
        variants: Which variants to generate (default: all).
        quality: Output quality for lossy formats (default 90).
        format_ext: Output format extension (default 'webp').

    Returns:
        ImageVariants with paths to all generated files.
    """
    img = Image.open(source_path).convert("RGB")
    wanted = variants or list(VARIANT_SIZES.keys())
    result = ImageVariants(source=source_path)

    for variant_name in wanted:
        target_size = VARIANT_SIZES[variant_name]
        var_dir = output_dir / variant_name
        var_dir.mkdir(parents=True, exist_ok=True)
        out_path = var_dir / f"{slug}.{format_ext}"

        w, h = img.size
        is_upscale = target_size > max(w, h)

        if is_upscale:
            resized = _upscale_to_long_edge(img, target_size)
        else:
            resized = _resize_to_long_edge(img, target_size)

        pil_format = "WEBP" if format_ext == "webp" else format_ext.upper()
        save_kwargs: dict = {"quality": quality}
        if pil_format == "WEBP":
            save_kwargs["method"] = 6
        resized.save(str(out_path), format=pil_format, **save_kwargs)

        setattr(result, variant_name.replace("-", "_"), out_path)
        logger.debug("Generated %s (%dx%d) -> %s", variant_name, resized.width, resized.height, out_path)

    if "placeholder" in wanted:
        result.placeholder_base64 = _make_placeholder_base64(img)

    return result


def generate_variants_batch(
    source_dir: Path,
    output_dir: Path,
    *,
    variants: list[str] | None = None,
    quality: int = 90,
    format_ext: str = "webp",
) -> list[ImageVariants]:
    """Generate variants for all PNG/JPG images in a directory."""
    results: list[ImageVariants] = []
    globs = ("*.png", "*.jpg", "*.jpeg", "*.webp")
    sources: list[Path] = []
    for g in globs:
        sources.extend(source_dir.glob(g))

    for src in sorted(sources):
        slug = src.stem
        result = generate_variants(
            src, output_dir, slug,
            variants=variants, quality=quality, format_ext=format_ext,
        )
        results.append(result)

    return results
