"""Place framed artwork onto room walls via Gemini API or PIL compositing.

Primary: Gemini API for photorealistic room placement.
Secondary: SDXL inpainting with IP-Adapter.
Fallback: PIL perspective-transform composite onto solid-color walls.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path

import click
import numpy as np
from PIL import Image

from pipeline.lib.config import get_settings
from pipeline.lib.paths import PROJECT_ROOT, mockups_rooms_dir

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    genai = None  # type: ignore[assignment]
    genai_types = None  # type: ignore[assignment]

try:
    import torch
    from diffusers import AutoPipelineForInpainting, AutoPipelineForText2Image
    from diffusers.utils import load_image
except ImportError:
    torch = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

GEMINI_ROOM_TYPES: list[tuple[str, str, str]] = [
    ("modern-living", "Modern Living Room",
     "a modern living room with neutral tones, soft natural light, minimalist furniture"),
    ("gallery-room", "Dark Gallery Room",
     "a dark gallery or museum room with dramatic lighting, white or dark walls"),
    ("midcentury", "Mid-Century Apartment",
     "a mid-century modern apartment interior with warm wood, clean lines"),
    ("nordic-dining", "Nordic Dining Area",
     "a Nordic or Scandinavian dining area with light wood, plants, natural light"),
    ("penthouse", "Penthouse Living",
     "a luxurious penthouse living room with floor-to-ceiling windows, city skyline view"),
]

ROOM_TEMPLATES: list[tuple[str, list[tuple[float, float]]]] = [
    ("living-room", [(0.15, 0.25), (0.85, 0.22), (0.88, 0.72), (0.12, 0.75)]),
    ("bedroom", [(0.12, 0.28), (0.82, 0.25), (0.85, 0.78), (0.15, 0.82)]),
    ("office", [(0.18, 0.30), (0.88, 0.28), (0.90, 0.75), (0.20, 0.78)]),
    ("gallery", [(0.20, 0.20), (0.80, 0.18), (0.82, 0.70), (0.18, 0.72)]),
]

ROOM_PROMPTS: dict[str, str] = {
    "living-room": "modern living room with neutral tones, soft natural light, minimalist furniture, empty wall",
    "bedroom": "modern bedroom interior, soft lighting, neutral palette, empty wall above headboard",
    "office": "modern home office, natural light from window, minimalist desk, empty wall",
    "gallery": "dark gallery or museum room with dramatic lighting, white or dark walls, empty wall space",
}

WALL_COLORS: list[tuple[int, int, int]] = [
    (245, 242, 238), (235, 230, 222), (220, 215, 205), (45, 42, 38),
]


def _find_coeffs(
    source_coords: list[tuple[float, float]],
    target_coords: list[tuple[float, float]],
) -> list[float]:
    """Compute perspective transform coefficients."""
    matrix: list[list[float]] = []
    for s, t in zip(source_coords, target_coords):
        matrix.append([t[0], t[1], 1, 0, 0, 0, -s[0] * t[0], -s[0] * t[1]])
        matrix.append([0, 0, 0, t[0], t[1], 1, -s[1] * t[0], -s[1] * t[1]])
    a_mat = np.matrix(matrix, dtype=np.float64)
    b_vec = np.array(source_coords).reshape(8)
    res = np.dot(np.linalg.inv(a_mat.T @ a_mat) @ a_mat.T, b_vec)
    return list(np.array(res).reshape(8))


def run_room_mockup_gemini(
    framed_path: Path,
    output_dir: Path,
    piece_slug: str,
) -> list[Path] | None:
    """Generate photorealistic room mockups using Gemini API."""
    if genai is None:
        return None
    settings = get_settings()
    if not settings.gemini_api_key:
        return None

    framed_img = Image.open(framed_path).convert("RGB")
    output_dir.mkdir(parents=True, exist_ok=True)
    out_paths: list[Path] = []

    client = genai.Client(api_key=settings.gemini_api_key)

    for room_key, _room_label, room_desc in GEMINI_ROOM_TYPES:
        prompt = (
            f"Place this framed artwork hanging on the wall in {room_desc}. "
            "Photorealistic interior photography. The artwork must appear exactly as shown\u2014"
            "do not modify, reimagine, or alter it. Show it in a realistic room setting with "
            "proper lighting, perspective, and shadows. Professional product mockup quality."
        )
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-image-preview",
                contents=[prompt, framed_img],
                config=genai_types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                ),
            )
            img_data = None
            for c in getattr(response, "candidates", []) or []:
                for part in getattr(getattr(c, "content", None), "parts", []) or []:
                    if hasattr(part, "inline_data") and part.inline_data:
                        img_data = part.inline_data.data
                        break
                if img_data:
                    break
            if img_data:
                out_img = Image.open(io.BytesIO(img_data)).convert("RGB")
                out_path = output_dir / f"{piece_slug}-{room_key}.png"
                out_img.save(str(out_path), format="PNG")
                out_paths.append(out_path)
        except Exception:
            logger.warning("Gemini room mockup failed for %s", room_key)

    return out_paths if len(out_paths) == len(GEMINI_ROOM_TYPES) else None


def _run_room_mockup_inpaint(
    framed_path: Path,
    output_dir: Path,
    piece_slug: str,
    room_name: str,
    room_desc: str,
    seed: int,
) -> Path | None:
    """Inpaint framed artwork onto a generated room via SDXL inpainting."""
    if torch is None:
        return None

    device = "cuda" if torch.cuda.is_available() else "cpu"
    t_dtype = torch.float16 if device == "cuda" else torch.float32
    size = 1024

    try:
        room_pipe = AutoPipelineForText2Image.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0", torch_dtype=t_dtype,
        )
        room_pipe = room_pipe.to(device)
        room_pipe.enable_vae_slicing()
        room_gen = torch.Generator(device=device).manual_seed(seed)
        room_img = room_pipe(
            prompt=f"{room_desc}, empty wall, photorealistic interior, 8k",
            negative_prompt="artwork, painting, frame, busy, cluttered",
            num_inference_steps=25, guidance_scale=7.5, generator=room_gen,
            height=size, width=size,
        ).images[0]
        del room_pipe
        torch.cuda.empty_cache()
    except Exception:
        return None

    mask = Image.new("L", (size, size), 0)
    x0, x1 = int(size * 0.28), int(size * 0.72)
    y0, y1 = int(size * 0.28), int(size * 0.68)
    for y in range(y0, y1):
        for x in range(x0, x1):
            mask.putpixel((x, y), 255)

    pipe = AutoPipelineForInpainting.from_pretrained(
        "diffusers/stable-diffusion-xl-1.0-inpainting-0.1", torch_dtype=t_dtype,
    )
    pipe = pipe.to(device)
    pipe.enable_vae_slicing()
    pipe.load_ip_adapter(
        "h94/IP-Adapter", subfolder="sdxl_models",
        weight_name="ip-adapter_sdxl.safetensors",
    )
    pipe.set_ip_adapter_scale(0.85)

    framed_ref = load_image(str(framed_path)).convert("RGB").resize((512, 512))
    prompt = (
        "framed artwork hanging on wall, photorealistic, proper perspective, "
        "canvas mounted on wall, cast shadow, natural lighting, museum quality"
    )
    gen = torch.Generator(device=device).manual_seed(seed + 1)
    result = pipe(
        prompt=prompt, image=room_img, mask_image=mask,
        ip_adapter_image=framed_ref, strength=0.92,
        num_inference_steps=30, guidance_scale=7.5, generator=gen,
    ).images[0]

    out_path = output_dir / f"{piece_slug}-{room_name}.png"
    output_dir.mkdir(parents=True, exist_ok=True)
    result.save(str(out_path))
    return out_path


def _composite_fallback(
    framed_path: Path,
    output_dir: Path,
    piece_slug: str,
) -> list[Path]:
    """Simple PIL perspective-composite onto solid-color walls."""
    framed = Image.open(framed_path).convert("RGB")
    fw, fh = framed.size
    room_size = (1200, 800)
    rw, rh = room_size
    out_paths: list[Path] = []

    for i, (room_name, quad_pct) in enumerate(ROOM_TEMPLATES):
        room_img = Image.new("RGB", room_size, WALL_COLORS[i % len(WALL_COLORS)])
        target_quad = [(int(q[0] * rw), int(q[1] * rh)) for q in quad_pct]
        src_quad = [(0, 0), (fw, 0), (fw, fh), (0, fh)]
        coeffs = _find_coeffs(src_quad, target_quad)
        transformed = framed.transform(
            room_size, Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC,
        )
        mask_img = Image.new("L", (fw, fh), 255)
        mask_transformed = mask_img.transform(
            room_size, Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC,
        )
        room_img.paste(transformed, (0, 0), mask=mask_transformed)
        out_path = output_dir / f"{piece_slug}-{room_name}.png"
        output_dir.mkdir(parents=True, exist_ok=True)
        room_img.save(str(out_path))
        out_paths.append(out_path)

    return out_paths


def run_room_mockup(
    framed_path: Path,
    output_dir: Path,
    piece_slug: str,
    *,
    use_gemini: bool = True,
    gemini_only: bool = False,
) -> list[Path]:
    """Generate room mockups. Tries Gemini first, then inpainting, then PIL composite."""
    if use_gemini:
        gemini_out = run_room_mockup_gemini(framed_path, output_dir, piece_slug)
        if gemini_out:
            return gemini_out
        if gemini_only:
            return []

    base_seed = hash(piece_slug) % (2**32)
    out_paths: list[Path] = []
    for i, (room_name, _) in enumerate(ROOM_TEMPLATES):
        room_desc = ROOM_PROMPTS.get(room_name, "modern living room, empty wall")
        out = _run_room_mockup_inpaint(
            framed_path, output_dir, piece_slug, room_name, room_desc,
            seed=base_seed + i,
        )
        if out:
            out_paths.append(out)

    if out_paths:
        return out_paths

    return _composite_fallback(framed_path, output_dir, piece_slug)


@click.command("room-mockup")
@click.option("--input", "input_path", required=True, type=click.Path(exists=True),
              help="Framed artwork image.")
@click.option("--piece-slug", required=True, help="Piece slug for output naming.")
@click.option("--output-dir", default=None, type=click.Path(), help="Output directory.")
@click.option("--no-gemini", is_flag=True, help="Skip Gemini API.")
@click.option("--gemini-only", is_flag=True, help="Only use Gemini (no fallback).")
def room_mockup(
    input_path: str,
    piece_slug: str,
    output_dir: str | None,
    no_gemini: bool,
    gemini_only: bool,
) -> None:
    """Generate room setting mockups with framed artwork on walls."""
    inp = Path(input_path)
    out = Path(output_dir) if output_dir else mockups_rooms_dir()
    results = run_room_mockup(
        inp, out, piece_slug,
        use_gemini=not no_gemini,
        gemini_only=gemini_only,
    )
    for p in results:
        click.echo(f"  {p}")
    click.echo(f"Generated {len(results)} room mockup(s)")
