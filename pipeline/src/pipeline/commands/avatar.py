"""Generate photorealistic artist avatars for gallery profiles.

Primary path: Gemini API (no GPU required)
Fallback: Realistic Vision V6 (SD 1.5, requires local GPU)
"""

from __future__ import annotations

import io
import logging
import random
from pathlib import Path

import click

from pipeline.lib.config import get_settings, load_artist_config
from pipeline.lib.paths import OUTPUT_DIR, PROJECT_ROOT

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore[assignment, misc]

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    genai = None  # type: ignore[assignment]
    genai_types = None  # type: ignore[assignment]

try:
    import torch
    from diffusers import StableDiffusionPipeline
    from transformers import CLIPTextModel, CLIPTokenizer
except ImportError:
    torch = None  # type: ignore[assignment]
    StableDiffusionPipeline = None  # type: ignore[assignment, misc]
    CLIPTextModel = None  # type: ignore[assignment, misc]
    CLIPTokenizer = None  # type: ignore[assignment, misc]

try:
    from huggingface_hub import hf_hub_download
except ImportError:
    hf_hub_download = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

AVATAR_MODEL_HF = "SG161222/Realistic_Vision_V6.0_B1"
AVATAR_MODEL_FILE = "Realistic_Vision_V6.0_B1.safetensors"


def _build_avatar_prompt(artist_name: str, style_desc: str) -> str:
    """Build a detailed prompt for photorealistic artist portrait."""
    return (
        f"Professional portrait photograph of a contemporary artist named {artist_name}. "
        f"They are a creative professional whose artistic style is {style_desc}. "
        "Head and shoulders portrait, natural lighting, subtle creative personality, "
        "wearing understated artistic attire. Neutral studio background with soft bokeh. "
        "Photorealistic, 8K, sharp focus, real person, editorial photography quality. "
        "The person should look authentic and compelling — not a stock photo."
    )


def _generate_avatar_gemini(
    artist_slug: str,
    artist_name: str,
    style_desc: str,
    out_dir: Path,
    count: int,
    gemini_model: str,
) -> list[Path]:
    """Generate avatar(s) via Gemini API."""
    if genai is None:
        raise click.ClickException("Install google-genai: pip install google-genai")
    if Image is None:
        raise click.ClickException("Install Pillow: pip install Pillow")

    settings = get_settings()
    if not settings.gemini_api_key:
        raise click.ClickException("GEMINI_API_KEY required. Set it in .env or environment.")

    client = genai.Client(api_key=settings.gemini_api_key)
    prompt = _build_avatar_prompt(artist_name, style_desc)
    saved: list[Path] = []

    for i in range(count):
        seed_val = random.randint(0, 2**32)

        response = client.models.generate_content(
            model=gemini_model,
            contents=[prompt],
            config=genai_types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            ),
        )

        img = None
        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                img = Image.open(io.BytesIO(part.inline_data.data)).convert("RGB")
                break

        if img is None:
            click.echo(f"Gemini did not return an image for avatar {i+1}, skipping")
            continue

        p = out_dir / f"{artist_slug}-portrait-{seed_val}.png"
        img.save(str(p))
        saved.append(p)
        click.echo(f"Saved {p}")

    return saved


def _generate_avatar_diffusers(
    artist_slug: str,
    artist_name: str,
    out_dir: Path,
    count: int,
    seed: int | None,
    steps: int,
    cfg_scale: float,
) -> list[Path]:
    """Generate avatar(s) via Realistic Vision V6 (requires local GPU)."""
    if torch is None:
        raise click.ClickException(
            "Install ML deps: pip install torch diffusers transformers huggingface_hub"
        )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if device == "cuda" else torch.float32

    model_path = PROJECT_ROOT / "pipeline" / "content" / "models" / AVATAR_MODEL_FILE
    if not model_path.exists():
        if hf_hub_download is None:
            raise click.ClickException(f"Model not found at {model_path}.")
        click.echo("Downloading Realistic Vision (first run)...")
        model_path.parent.mkdir(parents=True, exist_ok=True)
        downloaded = hf_hub_download(
            AVATAR_MODEL_HF, AVATAR_MODEL_FILE,
            local_dir=str(model_path.parent), local_dir_use_symlinks=False,
        )
        model_path = Path(downloaded)

    text_encoder = CLIPTextModel.from_pretrained(
        "openai/clip-vit-large-patch14", torch_dtype=torch_dtype,
    )
    tokenizer = CLIPTokenizer.from_pretrained("openai/clip-vit-large-patch14")
    pipe = StableDiffusionPipeline.from_single_file(
        str(model_path), text_encoder=text_encoder,
        tokenizer=tokenizer, torch_dtype=torch_dtype,
    )
    pipe = pipe.to(device)
    pipe.enable_vae_slicing()

    prompt = (
        f"professional portrait photograph of {artist_name}, "
        "artistic person, creative professional, natural lighting, "
        "head and shoulders, neutral background, studio quality, "
        "photorealistic, 8k, sharp focus, real face, real person"
    )
    neg = (
        "cartoon, anime, illustration, painting, drawing, fake, deformed, "
        "ugly, bad anatomy, bad quality, blurry"
    )

    saved: list[Path] = []
    for _ in range(count):
        s = seed if seed is not None else random.randint(0, 2**32)
        generator = torch.Generator(device=device).manual_seed(s)
        out_img = pipe(
            prompt=prompt, negative_prompt=neg,
            num_inference_steps=steps, guidance_scale=cfg_scale,
            generator=generator, height=768, width=512,
        ).images[0]
        p = out_dir / f"{artist_slug}-portrait-{s}.png"
        out_img.save(str(p))
        saved.append(p)
        click.echo(f"Saved {p}")

    return saved


def run_avatar(
    artist_slug: str,
    output_path: Path | None = None,
    *,
    count: int = 1,
    seed: int | None = None,
    steps: int = 30,
    cfg_scale: float = 7.5,
    use_gemini: bool = True,
    gemini_model: str = "gemini-3.1-flash-image-preview",
) -> list[Path]:
    """Generate photorealistic avatar(s) for an artist."""
    artist = load_artist_config(artist_slug)
    out_dir = output_path if output_path else (OUTPUT_DIR / "avatars" / artist_slug)
    if out_dir.suffix:
        out_dir = out_dir.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    if use_gemini:
        return _generate_avatar_gemini(
            artist_slug, artist.name, artist.style_reference,
            out_dir, count, gemini_model,
        )
    return _generate_avatar_diffusers(
        artist_slug, artist.name, out_dir, count, seed, steps, cfg_scale,
    )


@click.command("avatar")
@click.option("--artist", "artist_slug", required=True, help="Artist slug.")
@click.option("--output", "output_path", default=None, type=click.Path(), help="Output directory.")
@click.option("--count", default=1, type=int, help="Number of avatars to generate.")
@click.option("--seed", default=None, type=int, help="Random seed (diffusers only).")
@click.option("--steps", default=30, type=int, help="Inference steps (diffusers only).")
@click.option("--cfg", "cfg_scale", default=7.5, type=float, help="CFG scale (diffusers only).")
@click.option("--use-gemini/--use-diffusers", default=True, help="Use Gemini API (default) or local GPU.")
@click.option("--gemini-model", default="gemini-3.1-flash-image-preview", help="Gemini model for avatar generation.")
def avatar(
    artist_slug: str,
    output_path: str | None,
    count: int,
    seed: int | None,
    steps: int,
    cfg_scale: float,
    use_gemini: bool,
    gemini_model: str,
) -> None:
    """Generate photorealistic artist portrait(s)."""
    run_avatar(
        artist_slug,
        output_path=Path(output_path) if output_path else None,
        count=count, seed=seed, steps=steps, cfg_scale=cfg_scale,
        use_gemini=use_gemini, gemini_model=gemini_model,
    )
