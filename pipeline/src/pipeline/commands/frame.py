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
from PIL import Image

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

FRAME_STYLES: dict[str, dict] = {
    "black": {"matte_pct": 0, "frame_pct": 0.02, "matte_color": (0, 0, 0), "frame_color": (20, 20, 20)},
    "white": {"matte_pct": 0, "frame_pct": 0.02, "matte_color": (255, 255, 255), "frame_color": (248, 248, 248)},
    "black-white-matte": {"matte_pct": 0.03, "frame_pct": 0.02, "matte_color": (250, 250, 250), "frame_color": (25, 25, 25)},
    "dark-wood": {"matte_pct": 0.025, "frame_pct": 0.02, "matte_color": (250, 248, 245), "frame_color": (45, 42, 38)},
    "gold": {"matte_pct": 0, "frame_pct": 0.02, "matte_color": (60, 50, 40), "frame_color": (180, 150, 90)},
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
    view_angle: float = 0.35,
) -> Path:
    """Create angled perspective view from flat framed image."""
    framed = Image.open(flat_framed_path).convert("RGB")
    fw, fh = framed.size
    pad = 40
    out_w, out_h = fw + pad * 2, fh + pad * 2
    shrink = int(fw * view_angle)
    src = [(0, 0), (fw, 0), (fw, fh), (0, fh)]
    tgt = [
        (pad + shrink, pad), (out_w - pad - shrink, pad),
        (out_w - pad, out_h - pad), (pad, out_h - pad),
    ]
    coeffs = _find_coeffs(src, tgt)
    angled = framed.transform(
        (out_w, out_h), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    angled.save(str(output_path))
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

    if not framed_ok:
        style = FRAME_STYLES.get(frame_style or "dark-wood", FRAME_STYLES["dark-wood"])
        run_frame_flat(
            input_path, flat_path,
            matte_pct=style["matte_pct"],
            frame_pct=style["frame_pct"],
            matte_color=tuple(style["matte_color"]),
            frame_color=tuple(style["frame_color"]),
        )

    mockup_refs = _get_mockup_refs(artist_slug) if artist_slug else []

    ref_path = flat_path
    if photorealistic:
        enhanced = output_path.parent / f"{stem}-photorealistic.png"
        if run_frame_photorealistic(flat_path, enhanced, mockup_refs=mockup_refs, angled=angled):
            ref_path = enhanced

    if angled:
        run_frame_angled(ref_path, output_path)
    else:
        shutil.copy(ref_path, output_path)

    return flat_path, output_path


@click.command("frame")
@click.option("--input", "input_path", required=True, type=click.Path(exists=True), help="Source artwork.")
@click.option("--output", "output_path", default=None, type=click.Path(), help="Output path.")
@click.option("--artist", "artist_slug", default=None, help="Artist slug for reference frames.")
@click.option("--style", "frame_style", type=click.Choice(list(FRAME_STYLES)), default="dark-wood")
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
