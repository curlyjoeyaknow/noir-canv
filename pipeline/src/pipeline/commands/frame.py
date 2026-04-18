"""Composite artwork into frames with optional photorealistic enhancement.

Supports PIL flat framing, IP-Adapter reference-based framing,
Gemini photorealistic enhancement, and perspective views.
"""

from __future__ import annotations

import io
import logging
import os
import shutil
from pathlib import Path

import click
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from pipeline.lib.config import (
    get_example_images,
    get_framed_images,
    get_mockup_images,
    get_settings,
    load_artist_config,
)
from pipeline.lib.paths import MOCKUPS_FRAMED_DIR

try:
    import torch
    from diffusers import AutoPipelineForImage2Image
    from diffusers.utils import load_image
except ImportError:
    torch = None  # type: ignore[assignment]
    AutoPipelineForImage2Image = None  # type: ignore[assignment, misc]
    load_image = None  # type: ignore[assignment]

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    genai = None  # type: ignore[assignment]
    genai_types = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

# Frame styles calibrated to match reference product-shot mockup images.
# All styles use a wide white matte (~6.5–7 %) and thin frame (~1.8–2.2 %).
FRAME_STYLES: dict[str, dict] = {
    # Thin gloss-black aluminium frame + wide white matte (refs 1 & 2)
    "black": {
        "matte_pct": 0.065, "frame_pct": 0.018,
        "matte_color": (255, 255, 255), "frame_color": (18, 18, 18),
    },
    # Thin gloss-white frame + wide white matte
    "white": {
        "matte_pct": 0.065, "frame_pct": 0.018,
        "matte_color": (255, 255, 255), "frame_color": (242, 242, 240),
    },
    # Dark charcoal/wenge wood frame + wide white matte (ref 3)
    "charcoal-wood": {
        "matte_pct": 0.07, "frame_pct": 0.022,
        "matte_color": (255, 255, 255), "frame_color": (52, 47, 43),
    },
    # Legacy alias kept for backwards compatibility
    "dark-wood": {
        "matte_pct": 0.07, "frame_pct": 0.022,
        "matte_color": (255, 255, 255), "frame_color": (52, 47, 43),
    },
    # Natural oak / light wood + off-white matte
    "natural-wood": {
        "matte_pct": 0.065, "frame_pct": 0.02,
        "matte_color": (252, 250, 246), "frame_color": (140, 110, 72),
    },
    # Brushed gold + warm cream matte
    "gold": {
        "matte_pct": 0.065, "frame_pct": 0.02,
        "matte_color": (252, 250, 244), "frame_color": (162, 132, 72),
    },
}


def _find_coeffs(
    source_coords: list[tuple[float, float]],
    target_coords: list[tuple[float, float]],
) -> list[float]:
    """Compute perspective transform coefficients from source -> target quad."""
    matrix: list[list[float]] = []
    for s, t in zip(source_coords, target_coords):
        matrix.append([t[0], t[1], 1, 0, 0, 0, -s[0] * t[0], -s[0] * t[1]])
        matrix.append([0, 0, 0, t[0], t[1], 1, -s[1] * t[0], -s[1] * t[1]])
    a_mat = np.matrix(matrix, dtype=np.float64)
    b_vec = np.array(source_coords).reshape(8)
    res = np.dot(np.linalg.inv(a_mat.T @ a_mat) @ a_mat.T, b_vec)
    return list(np.array(res).reshape(8))


def _sample_background(art: Image.Image, sample_px: int = 8) -> tuple[int, int, int]:
    """Sample corner pixels to estimate artwork background color."""
    arr = np.array(art)
    h, w = arr.shape[:2]
    s = min(sample_px, h // 4, w // 4)
    corners = [arr[:s, :s], arr[:s, -s:], arr[-s:, :s], arr[-s:, -s:]]
    avg = np.mean([c.reshape(-1, 3).mean(axis=0) for c in corners], axis=0)
    return (int(avg[0]), int(avg[1]), int(avg[2]))


def _should_skip_matte(bg: tuple[int, int, int]) -> bool:
    """Skip white matte when background is already white or warm-neutral/beige."""
    r, g, b = bg
    return (r >= 225 and g >= 225 and b >= 225) or (
        (r + g + b) >= 480 and r >= b + 15 and g >= b + 5
    )


def run_frame_flat(
    input_path: Path,
    output_path: Path,
    *,
    matte_pct: float = 0.04,
    frame_pct: float = 0.025,
    matte_color: tuple[int, int, int] = (250, 248, 245),
    frame_color: tuple[int, int, int] = (45, 42, 38),
    min_matte_px: int = 12,
    min_frame_px: int = 8,
) -> Path:
    """Add matte (inner) and frame (outer) borders to artwork."""
    art = Image.open(input_path).convert("RGB")
    w, h = art.size
    # Skip white matte for white/beige artwork backgrounds
    bg = _sample_background(art)
    if _should_skip_matte(bg):
        matte_pct = 0.0
    matte_px = 0 if matte_pct <= 0 else max(min_matte_px, int(min(w, h) * matte_pct))
    frame_px = max(min_frame_px, int(min(w, h) * frame_pct))

    if matte_px > 0:
        matte_w, matte_h = w + 2 * matte_px, h + 2 * matte_px
        matte = Image.new("RGB", (matte_w, matte_h), matte_color)
        matte.paste(art, (matte_px, matte_px))
        inner_w, inner_h, inner_img = matte_w, matte_h, matte
    else:
        inner_w, inner_h, inner_img = w, h, art

    framed = Image.new("RGB", (inner_w + 2 * frame_px, inner_h + 2 * frame_px), frame_color)
    framed.paste(inner_img, (frame_px, frame_px))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    framed.save(str(output_path))
    return output_path


def run_frame_angled(
    flat_framed_path: Path,
    output_path: Path,
    *,
    view_angle: float = 0.22,
    vertical_skew: float = 0.03,
    frame_color: tuple[int, int, int] = (18, 18, 18),
) -> Path:
    """Left-receding perspective mockup matching premium print-gallery product shots.

    The left side of the frame recedes (compressed horizontally) while the right
    stays forward. Right and bottom depth strips show frame thickness. A soft
    Gaussian drop-shadow is composited beneath the frame on a white canvas.
    """
    framed = Image.open(flat_framed_path).convert("RGB")
    fw, fh = framed.size
    short = min(fw, fh)

    depth_px = max(18, int(short * 0.035))        # visible frame edge thickness
    pad = max(40, int(short * 0.042))              # white space around frame
    shrink_x = int(fw * view_angle)               # left-side horizontal compression
    skew_y = int(fh * vertical_skew)              # right side is this many px higher
    shadow_blur = max(8, int(short * 0.018))
    shadow_offset = max(5, int(short * 0.009))

    out_w = fw + depth_px + pad * 2
    out_h = fh + depth_px + pad * 2

    # Frame face corners — left side recedes, right side is forward.
    tl = (pad + shrink_x,         pad + skew_y)
    tr = (out_w - pad - depth_px, pad)
    br = (out_w - pad - depth_px, out_h - pad - depth_px)
    bl = (pad + shrink_x,         out_h - pad - depth_px + skew_y)

    src_pts = [(0, 0), (fw, 0), (fw, fh), (0, fh)]
    tgt_pts = [tl, tr, br, bl]
    coeffs = _find_coeffs(src_pts, tgt_pts)

    # ── Shadow ────────────────────────────────────────────────────────────────
    # Build a filled polygon that covers the entire frame silhouette (face +
    # depth strips), then Gaussian-blur it and composite under the frame.
    shadow_poly = [
        (tl[0] + shadow_offset, tl[1] + shadow_offset),
        (tr[0] + shadow_offset, tr[1] + shadow_offset),
        (out_w - pad + shadow_offset, tr[1] + int(depth_px * 0.55) + shadow_offset),
        (out_w - pad + shadow_offset, out_h - pad + shadow_offset),
        (bl[0] + shadow_offset, out_h - pad + shadow_offset),
        (bl[0] + shadow_offset, bl[1] + shadow_offset),
    ]
    shadow_mask = Image.new("L", (out_w, out_h), 0)
    ImageDraw.Draw(shadow_mask).polygon(shadow_poly, fill=140)
    shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(radius=shadow_blur))

    # ── White canvas with shadow ──────────────────────────────────────────────
    canvas = Image.new("RGBA", (out_w, out_h), (255, 255, 255, 255))
    shadow_layer = Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0))
    shadow_layer.putalpha(shadow_mask)
    canvas.alpha_composite(shadow_layer)

    # ── Frame face ────────────────────────────────────────────────────────────
    transformed = framed.transform(
        (out_w, out_h), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC,
    )
    face_mask = Image.new("L", (out_w, out_h), 0)
    ImageDraw.Draw(face_mask).polygon(tgt_pts, fill=255)
    canvas.paste(transformed.convert("RGBA"), (0, 0), mask=face_mask)

    # ── Depth strips ─────────────────────────────────────────────────────────
    # Use a slightly darker shade of the frame colour for the visible edges.
    depth_color = tuple(max(0, c - 22) for c in frame_color)
    bottom_color = tuple(max(0, c - 12) for c in frame_color)
    draw = ImageDraw.Draw(canvas)

    right_strip = [
        tr,
        (out_w - pad, tr[1] + int(depth_px * 0.55)),
        (out_w - pad, out_h - pad),
        br,
    ]
    draw.polygon(right_strip, fill=(*depth_color, 255))

    bottom_strip = [
        bl,
        br,
        (out_w - pad, out_h - pad),
        (bl[0], out_h - pad),
    ]
    draw.polygon(bottom_strip, fill=(*bottom_color, 255))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(str(output_path))
    return output_path


def run_frame_ip_adapter(
    input_path: Path,
    output_path: Path,
    framed_ref_images: list[Path],
    *,
    strength: float = 0.55,
    ip_scale: float = 0.75,
    model_id: str = "stabilityai/stable-diffusion-xl-base-1.0",
) -> Path | None:
    """Frame artwork using img2img + IP-Adapter with reference frames."""
    if torch is None or not framed_ref_images:
        return None
    ref_path = framed_ref_images[0]
    if not ref_path.exists():
        return None

    device = "cuda" if torch.cuda.is_available() else "cpu"
    use_cpu_offload = os.environ.get("PIPELINE_CPU_OFFLOAD", "").lower() in ("1", "true", "yes")

    pipe = AutoPipelineForImage2Image.from_pretrained(
        model_id, torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    )
    if use_cpu_offload:
        pipe.enable_model_cpu_offload()
        gen_device = "cpu"
    else:
        pipe = pipe.to(device)
        gen_device = device
        pipe.enable_vae_slicing()

    pipe.load_ip_adapter("h94/IP-Adapter", subfolder="sdxl_models", weight_name="ip-adapter_sdxl.bin")
    pipe.set_ip_adapter_scale(ip_scale)

    art_img = load_image(str(input_path))
    ip_img = load_image(str(ref_path))
    prompt = "framed artwork, professional frame, museum quality, matte and frame border, best quality"
    neg = "bad frame, deformed, blurry, low quality, ugly"

    generator = torch.Generator(device=gen_device).manual_seed(42)
    out = pipe(
        prompt=prompt, image=art_img, ip_adapter_image=ip_img,
        strength=strength, negative_prompt=neg,
        num_inference_steps=25, guidance_scale=7.5, generator=generator,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.images[0].save(str(output_path))
    return output_path


def run_frame_photorealistic(
    flat_framed_path: Path,
    output_path: Path,
    mockup_refs: list[Path] | None = None,
    angled: bool = False,
) -> Path | None:
    """Enhance flat framed image to look photorealistic using Gemini.

    When angled=True and mockup_refs are provided, includes reference mockup
    images so Gemini can match the perspective and lighting style of real
    angled product shots (examples/{artist}/mockups/).
    """
    if genai is None:
        return None
    settings = get_settings()
    if not settings.gemini_api_key:
        return None
    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        img = Image.open(flat_framed_path).convert("RGB")

        if angled and mockup_refs:
            ref_imgs = [Image.open(str(p)).convert("RGB") for p in mockup_refs[:3]]
            instruction = (
                "Study these reference mockup images to understand the perspective angle, "
                "lighting, and shadow style. Then apply the same angled perspective and "
                "photorealistic framing to the artwork image that follows the references. "
                "Keep the artwork content exactly as-is — only add the perspective, frame, "
                "and lighting. Photorealistic product photography style.\n\nReference mockups:"
            )
            contents: list = [instruction, *ref_imgs, "Now enhance this artwork:", img]
        else:
            contents = [
                "Make this framed artwork look photorealistic. The frame should have realistic "
                "wood grain, subtle depth, and proper lighting. Keep the artwork exactly as is, "
                "only enhance the frame. Photorealistic product photography style. Return the image.",
                img,
            ]

        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents=contents,
            config=genai_types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
        )
        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                out_img = Image.open(io.BytesIO(part.inline_data.data)).convert("RGB")
                output_path.parent.mkdir(parents=True, exist_ok=True)
                out_img.save(str(output_path))
                return output_path
    except Exception:
        logger.warning("Gemini photorealistic enhancement failed")
    return None


def _get_framed_refs(artist_slug: str) -> list[Path]:
    """Front-on framed reference images (examples/{artist}/framed/).

    Non-recursive: only flat front-facing frames, not angled mockup subfolders.
    Used as IP-Adapter style references for the framing step.
    """
    try:
        artist = load_artist_config(artist_slug)
    except (FileNotFoundError, ValueError):
        return []
    return get_framed_images(artist.example_artists)


def _get_mockup_refs(artist_slug: str) -> list[Path]:
    """Angled 3-D mockup reference images (examples/{artist}/mockups/).

    Used as style references when generating perspective/angled frame views.
    """
    try:
        artist = load_artist_config(artist_slug)
    except (FileNotFoundError, ValueError):
        return []
    return get_mockup_images(artist.example_artists)


# ---------------------------------------------------------------------------
# Frame style analysis — learns from examples/framed/ and examples/mockups/
# ---------------------------------------------------------------------------

def _analyze_flat_framed(images: list[Path]) -> dict:
    """Measure frame colour, matte colour, and border proportions from front-on shots.

    Scans inward from each image edge:
      • corner pixels  → frame colour (always frame, never matte/artwork)
      • first colour-change row from the top → frame thickness
      • next colour-change (non-white) row    → matte thickness
    """
    frame_colors: list[tuple] = []
    frame_pcts: list[float] = []
    matte_pcts: list[float] = []

    for img_path in images:
        try:
            img = Image.open(img_path).convert("RGB")
            w, h = img.size
            arr = np.array(img, dtype=np.float32)

            # ── Frame colour from corners ─────────────────────────────────
            cs = max(6, min(w, h) // 30)
            corner_pixels = np.concatenate([
                arr[:cs, :cs].reshape(-1, 3),
                arr[:cs, -cs:].reshape(-1, 3),
                arr[-cs:, :cs].reshape(-1, 3),
                arr[-cs:, -cs:].reshape(-1, 3),
            ])
            frame_rgb = tuple(np.median(corner_pixels, axis=0).astype(int).tolist())
            frame_lum = float(np.mean(frame_rgb))
            frame_colors.append(frame_rgb)

            # ── Scan downward from top to measure frame thickness ─────────
            x0, x1 = w // 4, 3 * w // 4
            frame_px = int(h * 0.015)  # minimum fallback
            for row in range(1, h // 3):
                row_lum = float(np.mean(arr[row, x0:x1]))
                if abs(row_lum - frame_lum) > 28:
                    frame_px = row
                    break
            frame_pcts.append(frame_px / h)

            # ── Scan from frame edge inward to measure matte thickness ────
            # Matte is typically high-luminance (white/off-white, > 220).
            matte_end = frame_px
            for row in range(frame_px, h // 2):
                row_lum = float(np.mean(arr[row, x0:x1]))
                if row_lum < 215:  # artwork starts (significantly darker than matte)
                    matte_end = row
                    break
            matte_px = max(0, matte_end - frame_px)
            matte_pcts.append(matte_px / h)

        except Exception:
            logger.debug("Frame analysis failed for %s", img_path, exc_info=True)

    out: dict = {}
    if frame_colors:
        out["frame_color"] = list(map(int, np.median(frame_colors, axis=0).astype(int)))
    if frame_pcts:
        out["frame_pct"] = round(float(np.median(frame_pcts)), 4)
    if matte_pcts:
        raw_matte = float(np.median(matte_pcts))
        # If matte is very thin (<1 %), it's probably unmated — keep as detected.
        out["matte_pct"] = round(raw_matte, 4)
        out["matte_color"] = [255, 255, 255] if raw_matte > 0.01 else [250, 248, 245]
    return out


def _analyze_angled_mockups(images: list[Path]) -> dict:
    """Estimate perspective view_angle and vertical_skew from angled mockup shots.

    Strategy: the mockup background is white. The leftmost non-white column in
    the middle band of the image is where the frame face starts.  Comparing
    that x-position to the total frame-face width gives view_angle.  Comparing
    the y-position of the first non-white pixel in left vs right strips gives
    vertical_skew.
    """
    view_angles: list[float] = []
    vertical_skews: list[float] = []

    for img_path in images:
        try:
            img = Image.open(img_path).convert("RGB")
            w, h = img.size
            arr = np.array(img, dtype=np.uint8)

            # Middle horizontal band (avoid top/bottom padding)
            y0, y1 = h // 5, 4 * h // 5
            band = arr[y0:y1]

            # Non-white: any pixel where ALL channels < 210
            non_white_mask = band.max(axis=2) < 210   # shape (rows, cols)
            col_has_content = non_white_mask.any(axis=0)

            content_cols = np.where(col_has_content)[0]
            if len(content_cols) < 10:
                continue

            left_edge = int(content_cols[0])
            right_edge = int(content_cols[-1])
            face_width = right_edge - left_edge
            if face_width < 1:
                continue

            # view_angle ≈ left_edge / face_width (left compression vs face width)
            va = left_edge / face_width
            if 0.03 < va < 0.55:
                view_angles.append(va)

            # Vertical skew: compare y of first non-white pixel in left vs right strip
            strip_w = max(10, face_width // 12)
            left_strip = arr[:, left_edge: left_edge + strip_w]
            right_strip = arr[:, right_edge - strip_w: right_edge]

            left_nw_rows = np.where(left_strip.max(axis=(1, 2)) < 210)[0]
            right_nw_rows = np.where(right_strip.max(axis=(1, 2)) < 210)[0]
            if len(left_nw_rows) and len(right_nw_rows):
                skew_px = int(left_nw_rows[0]) - int(right_nw_rows[0])
                skew_frac = skew_px / h
                if 0.0 < skew_frac < 0.12:
                    vertical_skews.append(skew_frac)

        except Exception:
            logger.debug("Mockup angle analysis failed for %s", img_path, exc_info=True)

    out: dict = {}
    if view_angles:
        out["frame_view_angle"] = round(float(np.median(view_angles)), 3)
    if vertical_skews:
        out["frame_vertical_skew"] = round(float(np.median(vertical_skews)), 3)
    return out


def analyze_example_frame_style(
    example_artists: list[str],
    *,
    max_framed: int = 8,
    max_mockups: int = 5,
) -> dict:
    """Analyze an artist's framed/ and mockups/ reference images.

    Returns a dict suitable for updating ArtistConfig frame fields:
      frame_color, matte_color, frame_pct, matte_pct  — from framed/ images
      frame_view_angle, frame_vertical_skew            — from mockups/ images

    Falls back gracefully: any stage that yields no valid images returns no
    keys for that stage, leaving the caller free to use defaults.
    """
    result: dict = {}

    framed_imgs = get_framed_images(example_artists)
    if framed_imgs:
        flat_params = _analyze_flat_framed(framed_imgs[:max_framed])
        result.update(flat_params)
        click.echo(
            f"  Analyzed {min(len(framed_imgs), max_framed)} framed image(s): "
            f"frame={result.get('frame_color')}, matte_pct={result.get('matte_pct')}"
        )
    else:
        click.echo("  No framed/ images found — using style defaults")

    mockup_imgs = get_mockup_images(example_artists)
    if mockup_imgs:
        angled_params = _analyze_angled_mockups(mockup_imgs[:max_mockups])
        result.update(angled_params)
        click.echo(
            f"  Analyzed {min(len(mockup_imgs), max_mockups)} mockup image(s): "
            f"view_angle={result.get('frame_view_angle')}, "
            f"vertical_skew={result.get('frame_vertical_skew')}"
        )
    else:
        click.echo("  No mockups/ images found — using perspective defaults")

    return result


@click.command("analyze-frames")
@click.option("--artist", "artist_slug", required=True, help="Artist slug to analyze.")
@click.option("--save/--no-save", default=True, help="Write results back to artist YAML (default: yes).")
def analyze_frames(artist_slug: str, save: bool) -> None:
    """Analyze example framed/ and mockups/ images to auto-detect frame style.

    Reads the artist's example reference images, measures frame colour, matte
    proportions, and perspective angle, then stores the results in the artist's
    pipeline YAML for use by `pipeline frame`.
    """
    import yaml

    from pipeline.lib.paths import ARTISTS_DIR

    artist = load_artist_config(artist_slug)
    click.echo(f"Analyzing frame style for {artist.name} ({artist_slug})…")
    click.echo(f"  Example artists: {', '.join(artist.example_artists)}")

    detected = analyze_example_frame_style(artist.example_artists)

    if not detected:
        click.echo("No frame parameters could be detected. Check that framed/ or mockups/ folders have images.")
        return

    click.echo("\nDetected parameters:")
    for k, v in detected.items():
        click.echo(f"  {k}: {v}")

    if save:
        config_path = ARTISTS_DIR / f"{artist_slug}.yaml"
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        raw.update(detected)
        config_path.write_text(
            yaml.dump(raw, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )
        click.echo(f"\nSaved to {config_path}")
    else:
        click.echo("\n(--no-save: YAML not updated)")


def run_frame(
    input_path: Path,
    output_path: Path,
    *,
    artist_slug: str | None = None,
    use_ref_frames: bool = True,
    frame_style: str | None = None,
    angled: bool = False,
    photorealistic: bool = False,
) -> tuple[Path, Path]:
    """Full frame pipeline: flat → optional photorealistic → optional angled.

    Returns (flat_path, output_path). Use flat_path for room mockups.
    """
    flat_dir = output_path.parent / ".flat"
    flat_dir.mkdir(parents=True, exist_ok=True)
    stem = output_path.stem.removesuffix("-framed") or output_path.stem
    flat_path = flat_dir / f"{stem}-flat.png"

    framed_ok = False
    if use_ref_frames and artist_slug:
        framed_refs = _get_framed_refs(artist_slug)
        if framed_refs:
            try:
                artist = load_artist_config(artist_slug)
                if run_frame_ip_adapter(
                    input_path, flat_path, framed_refs,
                    ip_scale=artist.ip_adapter_scale, model_id=artist.model_id,
                ):
                    framed_ok = True
            except Exception:
                logger.warning("IP-Adapter framing failed, falling back to PIL")

    # ── Resolve frame parameters ──────────────────────────────────────────────
    # Priority order:
    #   1. Analyzed values stored in the artist YAML (from `pipeline analyze-frames`)
    #   2. Named FRAME_STYLE selected via --style
    #   3. Hard defaults ("black" style)
    base_style = FRAME_STYLES.get(frame_style or "black", FRAME_STYLES["black"])
    matte_pct: float = base_style["matte_pct"]
    frame_pct: float = base_style["frame_pct"]
    matte_color: tuple[int, int, int] = tuple(base_style["matte_color"])  # type: ignore[assignment]
    style_frame_color: tuple[int, int, int] = tuple(base_style["frame_color"])  # type: ignore[assignment]
    view_angle: float = 0.22
    vertical_skew: float = 0.03

    if artist_slug:
        try:
            cfg = load_artist_config(artist_slug)
            if cfg.frame_color:
                style_frame_color = tuple(cfg.frame_color)  # type: ignore[assignment]
            if cfg.matte_color:
                matte_color = tuple(cfg.matte_color)  # type: ignore[assignment]
            if cfg.matte_pct is not None:
                matte_pct = cfg.matte_pct
            if cfg.frame_pct is not None:
                frame_pct = cfg.frame_pct
            if cfg.frame_view_angle is not None:
                view_angle = cfg.frame_view_angle
            if cfg.frame_vertical_skew is not None:
                vertical_skew = cfg.frame_vertical_skew
        except (FileNotFoundError, ValueError):
            pass

    if not framed_ok:
        run_frame_flat(
            input_path, flat_path,
            matte_pct=matte_pct,
            frame_pct=frame_pct,
            matte_color=matte_color,
            frame_color=style_frame_color,
        )

    mockup_refs = _get_mockup_refs(artist_slug) if artist_slug else []

    ref_path = flat_path
    if photorealistic:
        enhanced = output_path.parent / f"{stem}-photorealistic.png"
        if run_frame_photorealistic(flat_path, enhanced, mockup_refs=mockup_refs, angled=angled):
            ref_path = enhanced

    if angled:
        run_frame_angled(
            ref_path, output_path,
            frame_color=style_frame_color,
            view_angle=view_angle,
            vertical_skew=vertical_skew,
        )
    else:
        shutil.copy(ref_path, output_path)

    return flat_path, output_path


@click.command("frame")
@click.option("--input", "input_path", required=True, type=click.Path(exists=True), help="Source artwork.")
@click.option("--output", "output_path", default=None, type=click.Path(), help="Output path.")
@click.option("--artist", "artist_slug", default=None, help="Artist slug for reference frames.")
@click.option("--style", "frame_style", type=click.Choice(list(FRAME_STYLES)), default="black")
@click.option("--angled", is_flag=True, help="Create angled perspective view.")
@click.option("--photorealistic", is_flag=True, help="Enhance frame with Gemini.")
@click.option("--no-ref-frames", is_flag=True, help="Skip IP-Adapter reference frames.")
def frame(
    input_path: str,
    output_path: str | None,
    artist_slug: str | None,
    frame_style: str,
    angled: bool,
    photorealistic: bool,
    no_ref_frames: bool,
) -> None:
    """Frame artwork with matte and frame borders."""
    inp = Path(input_path)
    if output_path:
        out = Path(output_path)
    else:
        MOCKUPS_FRAMED_DIR.mkdir(parents=True, exist_ok=True)
        out = MOCKUPS_FRAMED_DIR / f"{inp.stem}-framed.png"

    flat_path, out_path = run_frame(
        inp, out,
        artist_slug=artist_slug,
        use_ref_frames=not no_ref_frames,
        frame_style=frame_style,
        angled=angled,
        photorealistic=photorealistic,
    )
    click.echo(f"Flat: {flat_path}")
    click.echo(f"Output: {out_path}")
