"""Generate artist-in-studio mockups: artist working on canvas, holding canvas.

Primary path: Gemini API (no GPU required)
Fallback: SDXL/FLUX with IP-Adapter (requires local GPU)
"""

from __future__ import annotations

import io
import random
from pathlib import Path

import click

from pipeline.lib import paths
from pipeline.lib.config import ArtistConfig, get_example_images, get_settings, load_artist_config

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
    from diffusers import AutoPipelineForText2Image, FluxPipeline
    from diffusers.utils import load_image
except ImportError:
    torch = None  # type: ignore[assignment]
    AutoPipelineForText2Image = None  # type: ignore[assignment, misc]
    FluxPipeline = None  # type: ignore[assignment, misc]
    load_image = None  # type: ignore[assignment]


STUDIO_PROMPTS = {
    "working": (
        "Photorealistic editorial photograph of {name}, a contemporary artist, "
        "working in their art studio. They are painting on a large canvas at an easel. "
        "Creative workspace with natural light from a window, paint supplies visible. "
        "Artistic atmosphere, warm natural lighting. The artist's style is {style}. "
        "8K, sharp focus, editorial photography quality, real person."
    ),
    "holding": (
        "Photorealistic editorial photograph of {name}, a contemporary artist, "
        "proudly holding their framed artwork in a gallery setting. "
        "Professional artist portrait, clean gallery background with subtle lighting. "
        "The artwork they hold reflects their style: {style}. "
        "8K, sharp focus, editorial photography quality, real person."
    ),
    "creative-space": (
        "Photorealistic editorial photograph of {name}'s art studio. "
        "A creative workspace filled with canvases, art supplies, and works in progress. "
        "Natural light streaming in. The works visible reflect the style: {style}. "
        "Interior photography, 8K, sharp focus, warm atmospheric lighting."
    ),
}


def _generate_studio_gemini(
    artist_slug: str,
    artist: ArtistConfig,
    mode: str,
    out_dir: Path,
    gemini_model: str,
) -> list[Path]:
    """Generate artist-studio image via Gemini API."""
    if genai is None:
        raise click.ClickException("Install google-genai: pip install google-genai")
    if Image is None:
        raise click.ClickException("Install Pillow: pip install Pillow")

    settings = get_settings()
    if not settings.gemini_api_key:
        raise click.ClickException("GEMINI_API_KEY required. Set it in .env or environment.")

    client = genai.Client(api_key=settings.gemini_api_key)

    template = STUDIO_PROMPTS.get(mode, STUDIO_PROMPTS["working"])
    prompt = template.format(name=artist.name, style=artist.style_reference)
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
        click.echo("Gemini did not return an image, skipping")
        return []

    p = out_dir / f"{artist_slug}-studio-{mode}-{seed_val}.png"
    img.save(str(p))
    click.echo(f"Saved {p}")
    return [p]


def _generate_studio_diffusers(
    artist_slug: str,
    artist: ArtistConfig,
    mode: str,
    out_dir: Path,
    seed: int | None,
    steps: int,
    cfg_scale: float,
) -> list[Path]:
    """Generate artist-studio image via SDXL/FLUX (requires local GPU)."""
    if torch is None:
        raise click.ClickException(
            "Install ML deps: pip install torch diffusers transformers"
        )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    use_flux = artist.model_type == "flux" or "flux" in (artist.model_id or "").lower()

    if use_flux:
        pipe = FluxPipeline.from_pretrained(
            artist.model_id or "black-forest-labs/FLUX.1-dev",
            torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
        )
        pipe.enable_model_cpu_offload()
        pipe.enable_vae_slicing()
        gen_device = "cpu"
    else:
        pipe = AutoPipelineForText2Image.from_pretrained(
            artist.model_id or "stabilityai/stable-diffusion-xl-base-1.0",
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        )
        pipe = pipe.to(device)
        pipe.enable_vae_slicing()
        gen_device = device

    template = STUDIO_PROMPTS.get(mode, STUDIO_PROMPTS["working"])
    prompt = template.format(name=artist.name, style=artist.style_reference)
    neg = artist.negative_prompt or "cartoon, anime, blurry, low quality"

    example_images = get_example_images(
        artist.example_artists, ref_folder=artist.example_ref_folder or "main",
    )
    if example_images:
        _try_load_ip_adapter(pipe, artist, use_flux)

    s = seed if seed is not None else random.randint(0, 2**32)
    generator = torch.Generator(device=gen_device).manual_seed(s)

    gen_kwargs: dict = {
        "prompt": prompt, "negative_prompt": neg,
        "generator": generator, "num_inference_steps": steps,
        "guidance_scale": cfg_scale if not use_flux else (cfg_scale or 3.5),
    }
    if example_images:
        gen_kwargs["ip_adapter_image"] = load_image(str(example_images[0]))

    out_img = pipe(**gen_kwargs).images[0]
    p = out_dir / f"{artist_slug}-studio-{mode}-{s}.png"
    out_img.save(str(p))
    click.echo(f"Saved {p}")
    return [p]


def _try_load_ip_adapter(pipe: object, artist: ArtistConfig, use_flux: bool) -> None:
    """Attempt to load IP-Adapter; silently skip on failure."""
    try:
        if use_flux:
            pipe.load_ip_adapter(  # type: ignore[attr-defined]
                artist.flux_ip_adapter_repo or "XLabs-AI/flux-ip-adapter-v2",
                weight_name=artist.flux_ip_adapter_weight or "ip_adapter.safetensors",
                image_encoder_pretrained_model_name_or_path="openai/clip-vit-large-patch14",
            )
        else:
            pipe.load_ip_adapter(  # type: ignore[attr-defined]
                "h94/IP-Adapter", subfolder="sdxl_models",
                weight_name=artist.ip_adapter_weight or "ip-adapter_sdxl.bin",
            )
        pipe.set_ip_adapter_scale(artist.ip_adapter_scale or 0.6)  # type: ignore[attr-defined]
    except Exception:
        pass


def run_artist_studio(
    artist_slug: str,
    canvas_path: Path | None = None,
    output_path: Path | None = None,
    *,
    mode: str = "working",
    seed: int | None = None,
    steps: int = 35,
    cfg_scale: float = 7.5,
    use_gemini: bool = True,
    gemini_model: str = "gemini-3.1-flash-image-preview",
) -> list[Path]:
    """Generate photorealistic mockup of artist in their studio."""
    artist = load_artist_config(artist_slug)
    out_dir = output_path or paths.public_artists_dir(artist_slug)
    if out_dir.suffix:
        out_dir = out_dir.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    if use_gemini:
        return _generate_studio_gemini(artist_slug, artist, mode, out_dir, gemini_model)
    return _generate_studio_diffusers(
        artist_slug, artist, mode, out_dir, seed, steps, cfg_scale,
    )


@click.command("artist-studio")
@click.option("--artist", "-a", required=True, help="Artist slug")
@click.option("--canvas", "-c", type=click.Path(path_type=Path), help="Canvas image (for holding mode)")
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output path or directory")
@click.option(
    "--mode", "-m", default="working",
    type=click.Choice(["working", "holding", "creative-space"]),
    help="working=at easel, holding=with canvas, creative-space=studio interior",
)
@click.option("--seed", "-s", type=int, help="Random seed (diffusers only)")
@click.option("--steps", default=35, help="Inference steps (diffusers only)")
@click.option("--use-gemini/--use-diffusers", default=True, help="Use Gemini API (default) or local GPU.")
@click.option("--gemini-model", default="gemini-3.1-flash-image-preview", help="Gemini model for generation.")
def artist_studio(
    artist: str,
    canvas: Path | None,
    output: Path | None,
    mode: str,
    seed: int | None,
    steps: int,
    use_gemini: bool,
    gemini_model: str,
) -> None:
    """Generate artist-in-studio mockup (working, holding canvas, or creative space)."""
    run_artist_studio(
        artist, canvas_path=canvas, output_path=output,
        mode=mode, seed=seed, steps=steps,
        use_gemini=use_gemini, gemini_model=gemini_model,
    )
