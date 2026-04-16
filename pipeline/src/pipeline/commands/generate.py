"""Generate images with Gemini API, IP-Adapter + SDXL, or FLUX.

Primary path: Gemini API (when artist.model_type == "gemini")
Fallback: SDXL or FLUX with IP-Adapter style transfer
"""

from __future__ import annotations

import io
import json
import logging
import os
import random
from datetime import datetime, timezone
from pathlib import Path

import click

from pipeline.lib.config import (
    ArtistConfig,
    get_example_images,
    get_settings,
    load_artist_config,
    load_pieces,
)
from pipeline.lib.paths import OUTPUT_DIR, raw_dir
from pipeline.lib.prompts import build_prompt
from pipeline.lib.schemas import Piece

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
    from diffusers import (
        AutoPipelineForText2Image,
        EulerDiscreteScheduler,
        FluxPipeline,
        StableDiffusionXLPipeline,
        UNet2DConditionModel,
    )
    from diffusers.utils import load_image
    from huggingface_hub import hf_hub_download
    from safetensors.torch import load_file as safetensors_load_file
    from transformers import CLIPVisionModelWithProjection
except ImportError:
    torch = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


def _use_gemini(artist: ArtistConfig) -> bool:
    return artist.model_type == "gemini"


def _use_flux(artist: ArtistConfig) -> bool:
    if artist.model_type == "flux":
        return True
    return "flux" in (artist.model_id or "").lower()


def _build_prompt_for_piece(
    piece: Piece | None,
    artist: ArtistConfig,
    prompt_override: str | None,
) -> str:
    """Build generation prompt from piece metadata or artist style."""
    if prompt_override:
        return prompt_override
    if piece:
        return build_prompt(piece, artist)
    content = f"{artist.style_reference}. Original artwork."
    return f"{artist.prompt_prefix}{content}{artist.prompt_suffix}"


def _save_config_json(
    out_path: Path,
    artist_slug: str,
    piece_slug: str,
    seed_val: int,
    model_type: str,
    extra: dict | None = None,
) -> None:
    """Write generation metadata alongside the image."""
    data = {
        "artist_slug": artist_slug,
        "piece_slug": piece_slug,
        "seed": seed_val,
        "model_type": model_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        data.update(extra)
    out_path.with_suffix(".json").write_text(json.dumps(data, indent=2))


def _load_style_references(artist: ArtistConfig, max_refs: int = 5) -> list[Path]:
    """Load style reference images for the artist, capped at max_refs.

    Selects references evenly spaced across the full set to ensure diversity
    (not just the first N alphabetically, which could all be crops from
    one piece). Deterministic so every piece in a batch gets the same set.
    """
    example_images = get_example_images(
        artist.example_artists, ref_folder=artist.example_ref_folder,
    )
    if not example_images:
        return []

    all_sorted = sorted(example_images)
    if len(all_sorted) <= max_refs:
        return all_sorted

    step = len(all_sorted) / max_refs
    return [all_sorted[int(i * step)] for i in range(max_refs)]


def _build_gemini_content(
    prompt: str,
    style_refs: list[Path],
    artist: ArtistConfig,
) -> list:
    """Build multimodal Gemini content: style reference images + text prompt.

    When style references are available, prepends them with an instruction
    to study the visual style and generate a NEW piece that maintains it.
    """
    if not style_refs or Image is None:
        return [prompt]

    parts: list = []

    style_instruction = (
        f"You are generating a COMPLETE, FULL artwork — not a detail, not a crop, "
        f"not a close-up. The output must be a finished piece suitable for framing "
        f"and display in a gallery.\n\n"
        f"Study the visual style of these {len(style_refs)} reference artworks carefully. "
        f"Analyze: color palette, brushwork and texture, composition and layout, "
        f"how subjects are framed within the canvas, level of detail and abstraction, "
        f"and overall mood and atmosphere.\n\n"
        f"The artist's style: {artist.style_reference}\n\n"
        f"Reference artworks:\n"
    )
    parts.append(style_instruction)

    for ref_path in style_refs:
        ref_img = Image.open(str(ref_path)).convert("RGB")
        parts.append(ref_img)

    generation_instruction = (
        f"\n\nGenerate a NEW, COMPLETE original artwork as a FULL composition. "
        f"Requirements:\n"
        f"- FULL canvas composition, not a close-up or detail crop\n"
        f"- Show the complete subject with appropriate negative space\n"
        f"- Match the visual style, palette, and technique of the references\n"
        f"- Different subject matter but same artistic DNA\n"
        f"- Gallery-quality finished piece, suitable for printing at large scale\n"
        f"- No text, no watermarks, no signatures\n\n"
        f"Subject: {prompt}"
    )
    parts.append(generation_instruction)

    return parts


def _generate_gemini(
    artist_slug: str,
    artist: ArtistConfig,
    pieces: list[Piece],
    piece: Piece | None,
    count: int,
    prompt_override: str | None,
    batch_suffix: str | None,
    output_dir: Path | None,
    save_config: bool,
    max_style_refs: int = 5,
) -> list[Path]:
    """Generate images via Gemini API with style reference images."""
    if genai is None:
        raise click.ClickException("Install google-genai: pip install google-genai")
    if Image is None:
        raise click.ClickException("Install Pillow: pip install Pillow")
    settings = get_settings()
    if not settings.gemini_api_key:
        raise click.ClickException(
            "GEMINI_API_KEY required for Gemini generation. Set it in .env or environment."
        )

    client = genai.Client(api_key=settings.gemini_api_key)
    gemini_model = artist.gemini_model or "gemini-3.1-flash-image-preview"

    style_refs = _load_style_references(artist, max_refs=max_style_refs)
    if style_refs:
        click.echo(f"Loaded {len(style_refs)} style references for {artist_slug}")
    else:
        click.echo(
            f"Warning: No style reference images found for {artist_slug}. "
            f"Check examples/{'/'.join(artist.example_artists)}/ directory. "
            f"Falling back to text-only generation (style will be weak)."
        )

    saved_paths: list[Path] = []

    for i in range(count):
        prompt_piece = random.choice(pieces) if pieces else piece
        prompt = _build_prompt_for_piece(prompt_piece, artist, prompt_override)
        seed_val = random.randint(0, 2**32)
        batch = batch_suffix or f"gem{i}"

        contents = _build_gemini_content(prompt, style_refs, artist)

        response = client.models.generate_content(
            model=gemini_model,
            contents=contents,
            config=genai_types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
            ),
        )

        img = None
        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                img = Image.open(io.BytesIO(part.inline_data.data)).convert("RGB")
                break

        if img is None:
            click.echo("Gemini did not return an image, skipping")
            continue

        piece_slug = prompt_piece.slug if prompt_piece else artist_slug
        base_dir = output_dir if output_dir else raw_dir(artist_slug, piece_slug)
        base_dir.mkdir(parents=True, exist_ok=True)
        name = f"{piece_slug}-{batch}-{seed_val}" if batch_suffix else f"{piece_slug}-{seed_val}"
        out_path = base_dir / f"{name}.png"
        img.save(str(out_path))
        saved_paths.append(out_path)

        if save_config:
            _save_config_json(
                out_path, artist_slug, piece_slug, seed_val,
                "gemini", {
                    "gemini_model": gemini_model,
                    "style_refs": [str(p) for p in style_refs],
                    "style_ref_count": len(style_refs),
                },
            )
        click.echo(f"Saved {out_path}")

    return saved_paths


def _generate_diffusers(
    artist_slug: str,
    artist: ArtistConfig,
    pieces: list[Piece],
    piece: Piece | None,
    count: int,
    prompt_override: str | None,
    batch_suffix: str | None,
    output_dir: Path | None,
    save_config: bool,
    seed: int | None,
    cfg_scale: float | None,
    steps: int | None,
    ip_adapter_scale: float | None,
    ip_adapter_blend_count: int | None,
    reference_path: Path | None,
) -> list[Path]:
    """Generate images via SDXL or FLUX with optional IP-Adapter."""
    if torch is None:
        raise click.ClickException("Install ML deps: pip install torch diffusers transformers")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    use_flux = _use_flux(artist)
    force_offload = os.environ.get("PIPELINE_CPU_OFFLOAD", "").lower() in ("1", "true", "yes")
    force_no_offload = os.environ.get("PIPELINE_NO_CPU_OFFLOAD", "").lower() in ("1", "true", "yes")
    use_cpu_offload = device == "cuda" and (force_offload or (use_flux and not force_no_offload))
    use_lightning = artist.lightning_steps is not None and not use_flux
    torch_dtype = (
        torch.bfloat16 if (device == "cuda" and use_flux)
        else (torch.float16 if device == "cuda" else torch.float32)
    )

    example_images = get_example_images(
        artist.example_artists, ref_folder=artist.example_ref_folder,
    )

    blend_count = ip_adapter_blend_count if ip_adapter_blend_count is not None else artist.ip_adapter_blend_count

    if reference_path:
        if not reference_path.exists():
            raise click.ClickException(f"Reference image not found: {reference_path}")
        fixed_refs = [reference_path]
    elif example_images:
        n = min(blend_count, len(example_images))
        fixed_refs = sorted(example_images)[:n]
        click.echo(f"Using {len(fixed_refs)} consistent style references for all {count} images")
    else:
        fixed_refs = []

    pipe, gen_device, steps_val, cfg_val, ip_scale = _build_pipeline(
        artist, device, torch_dtype, use_flux, use_lightning, use_cpu_offload,
        example_images, reference_path, steps, cfg_scale, ip_adapter_scale,
    )

    ref_images = [load_image(str(p)) for p in fixed_refs] if fixed_refs else []
    ref_paths_used = [str(p) for p in fixed_refs]

    saved_paths: list[Path] = []
    for _ in range(count):
        prompt_piece = random.choice(pieces) if pieces else piece
        prompt = _build_prompt_for_piece(prompt_piece, artist, prompt_override)
        neg = artist.negative_prompt
        piece_slug = prompt_piece.slug if prompt_piece else artist_slug

        kwargs: dict = {"prompt": prompt, "negative_prompt": neg}
        if ref_images:
            kwargs["ip_adapter_image"] = ref_images[0] if len(ref_images) == 1 else [ref_images]

        seed_val = seed if seed is not None else random.randint(0, 2**32)
        generator = torch.Generator(device=gen_device).manual_seed(seed_val)
        kwargs["generator"] = generator

        out = pipe(**kwargs, num_inference_steps=steps_val, guidance_scale=cfg_val)
        img = out.images[0]
        base_dir = output_dir if output_dir else raw_dir(artist_slug, piece_slug)
        base_dir.mkdir(parents=True, exist_ok=True)
        name = f"{piece_slug}-{batch_suffix}-{seed_val}" if batch_suffix else f"{piece_slug}-{seed_val}"
        out_path = base_dir / f"{name}.png"
        img.save(str(out_path))
        saved_paths.append(out_path)

        if save_config:
            _save_config_json(
                out_path, artist_slug, piece_slug, seed_val,
                "flux" if use_flux else "sdxl",
                {
                    "cfg_scale": cfg_val, "steps": steps_val,
                    "ip_adapter_scale": ip_scale, "model_id": artist.model_id,
                    "reference_paths": ref_paths_used,
                },
            )
        click.echo(f"Saved {out_path}")
        if device == "cuda" and not use_cpu_offload and count > 1:
            torch.cuda.empty_cache()

    return saved_paths


def _build_pipeline(
    artist: ArtistConfig,
    device: str,
    torch_dtype: "torch.dtype",
    use_flux: bool,
    use_lightning: bool,
    use_cpu_offload: bool,
    example_images: list[Path],
    reference_path: Path | None,
    steps_override: int | None,
    cfg_override: float | None,
    ip_scale_override: float | None,
) -> tuple:
    """Build and configure the diffusers pipeline. Returns (pipe, gen_device, steps, cfg, ip_scale)."""
    has_refs = bool(example_images or reference_path)
    ip_scale = ip_scale_override if ip_scale_override is not None else artist.ip_adapter_scale

    if use_flux:
        pipe = FluxPipeline.from_pretrained(artist.model_id, torch_dtype=torch_dtype)
        if use_cpu_offload:
            pipe.enable_model_cpu_offload()
            gen_device = "cpu"
        else:
            pipe = pipe.to(device)
            gen_device = device
        pipe.enable_vae_slicing()
        if has_refs:
            flux_repo = artist.flux_ip_adapter_repo or "XLabs-AI/flux-ip-adapter-v2"
            flux_weight = artist.flux_ip_adapter_weight or "ip_adapter.safetensors"
            pipe.load_ip_adapter(
                flux_repo, weight_name=flux_weight,
                image_encoder_pretrained_model_name_or_path="openai/clip-vit-large-patch14",
            )
            pipe.set_ip_adapter_scale(ip_scale)
        is_schnell = "schnell" in (artist.model_id or "").lower()
        steps_val = 4 if is_schnell else (steps_override or 50)
        cfg_val = 0.0 if is_schnell else (cfg_override or artist.cfg_scale or 3.5)
    else:
        image_encoder = None
        if has_refs and artist.ip_adapter_image_encoder_folder:
            image_encoder = CLIPVisionModelWithProjection.from_pretrained(
                "h94/IP-Adapter",
                subfolder=artist.ip_adapter_image_encoder_folder,
                torch_dtype=torch_dtype,
            )

        if use_lightning:
            n = artist.lightning_steps
            ckpt = f"sdxl_lightning_{n}step_unet.safetensors"
            unet = UNet2DConditionModel.from_pretrained(
                artist.model_id, subfolder="unet", torch_dtype=torch_dtype,
            )
            unet.load_state_dict(
                safetensors_load_file(hf_hub_download("ByteDance/SDXL-Lightning", ckpt), device="cpu"),
                strict=False,
            )
            kw: dict = {"unet": unet, "torch_dtype": torch_dtype}
            if device == "cuda":
                kw["variant"] = "fp16"
            if image_encoder is not None:
                kw["image_encoder"] = image_encoder
            pipe = StableDiffusionXLPipeline.from_pretrained(artist.model_id, **kw)
            pipe.scheduler = EulerDiscreteScheduler.from_config(
                pipe.scheduler.config, timestep_spacing="trailing",
            )
        else:
            kw = {"torch_dtype": torch_dtype}
            if image_encoder is not None:
                kw["image_encoder"] = image_encoder
            pipe = AutoPipelineForText2Image.from_pretrained(artist.model_id, **kw)

        if use_cpu_offload:
            pipe.enable_model_cpu_offload()
            gen_device = "cpu"
        else:
            pipe = pipe.to(device)
            gen_device = device
        pipe.enable_vae_slicing()

        if has_refs:
            weight_name = artist.ip_adapter_weight or "ip-adapter_sdxl.bin"
            load_kw: dict = {"subfolder": "sdxl_models", "weight_name": weight_name}
            if image_encoder is None and artist.ip_adapter_image_encoder_folder:
                load_kw["image_encoder_folder"] = artist.ip_adapter_image_encoder_folder
            elif image_encoder is not None:
                load_kw["image_encoder_folder"] = None
            pipe.load_ip_adapter("h94/IP-Adapter", **load_kw)
            pipe.set_ip_adapter_scale(ip_scale)

        if use_lightning:
            steps_val = artist.lightning_steps or 4
            cfg_val = 0.0
        else:
            steps_val = steps_override if steps_override is not None else artist.steps
            cfg_val = cfg_override if cfg_override is not None else artist.cfg_scale

    return pipe, gen_device, steps_val, cfg_val, ip_scale


def run_generate(
    artist_slug: str,
    piece_slug: str | None = None,
    count: int = 1,
    **kwargs: object,
) -> list[Path]:
    """Top-level entry point for image generation."""
    artist = load_artist_config(artist_slug)

    pieces: list[Piece] = []
    target_piece: Piece | None = None
    try:
        all_pieces = load_pieces()
        if piece_slug:
            pieces = [p for p in all_pieces if p.slug == piece_slug and p.artist_slug == artist_slug]
            if not pieces:
                raise click.ClickException(f"Piece {piece_slug} not found for artist {artist_slug}")
            target_piece = pieces[0]
        else:
            pieces = [p for p in all_pieces if p.artist_slug == artist_slug]
    except FileNotFoundError:
        if piece_slug:
            raise click.ClickException(f"No pieces data found (data/pieces.json missing)")

    if not pieces and not kwargs.get("prompt_override"):
        click.echo("Warning: No pieces found. Using artist style for generation.")

    if _use_gemini(artist):
        return _generate_gemini(
            artist_slug, artist, pieces, target_piece, count,
            prompt_override=kwargs.get("prompt_override"),  # type: ignore[arg-type]
            batch_suffix=kwargs.get("batch_suffix"),  # type: ignore[arg-type]
            output_dir=kwargs.get("output_dir"),  # type: ignore[arg-type]
            save_config=not kwargs.get("no_config_json", False),
            max_style_refs=kwargs.get("max_style_refs") or 5,  # type: ignore[arg-type]
        )

    return _generate_diffusers(
        artist_slug, artist, pieces, target_piece, count,
        prompt_override=kwargs.get("prompt_override"),  # type: ignore[arg-type]
        batch_suffix=kwargs.get("batch_suffix"),  # type: ignore[arg-type]
        output_dir=kwargs.get("output_dir"),  # type: ignore[arg-type]
        save_config=not kwargs.get("no_config_json", False),
        seed=kwargs.get("seed"),  # type: ignore[arg-type]
        cfg_scale=kwargs.get("cfg_scale"),  # type: ignore[arg-type]
        steps=kwargs.get("steps"),  # type: ignore[arg-type]
        ip_adapter_scale=kwargs.get("ip_adapter_scale"),  # type: ignore[arg-type]
        ip_adapter_blend_count=kwargs.get("ip_adapter_blend_count"),  # type: ignore[arg-type]
        reference_path=kwargs.get("reference_path"),  # type: ignore[arg-type]
    )


@click.command("generate")
@click.option("--artist", "artist_slug", required=True, help="Artist slug.")
@click.option("--piece", "piece_slug", default=None, help="Specific piece slug.")
@click.option("--count", default=1, type=int, help="Number of images to generate.")
@click.option("--seed", default=None, type=int, help="Random seed.")
@click.option("--prompt", "prompt_override", default=None, help="Override generation prompt.")
@click.option("--output-dir", default=None, type=click.Path(), help="Custom output directory.")
@click.option("--cfg-scale", default=None, type=float, help="CFG scale override.")
@click.option("--steps", default=None, type=int, help="Inference steps override.")
@click.option("--batch-suffix", default=None, help="Suffix for batch naming.")
@click.option("--reference", "reference_path", default=None, type=click.Path(exists=True))
@click.option("--no-config-json", is_flag=True, help="Skip writing config JSON alongside images.")
@click.option("--max-style-refs", default=5, type=int, help="Max style reference images to send to Gemini (default 5).")
def generate(
    artist_slug: str,
    piece_slug: str | None,
    count: int,
    seed: int | None,
    prompt_override: str | None,
    output_dir: str | None,
    cfg_scale: float | None,
    steps: int | None,
    batch_suffix: str | None,
    reference_path: str | None,
    no_config_json: bool,
    max_style_refs: int,
) -> None:
    """Generate images for an artist using Gemini, SDXL, or FLUX."""
    run_generate(
        artist_slug,
        piece_slug=piece_slug,
        count=count,
        seed=seed,
        prompt_override=prompt_override,
        output_dir=Path(output_dir) if output_dir else None,
        cfg_scale=cfg_scale,
        steps=steps,
        batch_suffix=batch_suffix,
        reference_path=Path(reference_path) if reference_path else None,
        no_config_json=no_config_json,
        max_style_refs=max_style_refs,
    )
