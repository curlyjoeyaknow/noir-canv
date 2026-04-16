"""Upscale images with Real-ESRGAN for print resolution.

Requires torch + realesrgan + basicsr.
"""

from __future__ import annotations

import logging
from pathlib import Path

import click
import numpy as np
from PIL import Image

from pipeline.lib.paths import print_dir, public_pieces_dir, selected_dir

try:
    import torch
except ImportError:
    torch = None  # type: ignore[assignment]

try:
    from basicsr.archs.rrdbnet_arch import RRDBNet
    from realesrgan import RealESRGANer
except ImportError:
    RRDBNet = None  # type: ignore[assignment, misc]
    RealESRGANer = None  # type: ignore[assignment, misc]

logger = logging.getLogger(__name__)

REALESRGAN_MODEL_PATH = Path.home() / ".cache" / "realesrgan" / "RealESRGAN_x4plus.pth"


def run_upscale_single(
    input_path: Path,
    output_path: Path,
    use_cpu: bool = False,
) -> Path:
    """Upscale a single image with Real-ESRGAN x4. Returns output_path."""
    if RRDBNet is None or RealESRGANer is None:
        raise click.ClickException("Install upscale deps: pip install realesrgan basicsr")
    if torch is None:
        raise click.ClickException("Install torch: pip install torch")
    if not input_path.exists():
        raise click.ClickException(f"Input file not found: {input_path}")
    if not REALESRGAN_MODEL_PATH.exists():
        raise click.ClickException(
            f"Real-ESRGAN model not found at {REALESRGAN_MODEL_PATH}. "
            "Download it first."
        )

    use_cuda = torch.cuda.is_available() and not use_cpu
    model = RRDBNet(num_in_ch=3, num_out_ch=3, scale=4, num_feat=64, num_block=23, num_grow_ch=32)
    upsampler = RealESRGANer(
        scale=4,
        model_path=str(REALESRGAN_MODEL_PATH),
        model=model,
        tile=256,
        tile_pad=10,
        half=use_cuda,
        device=torch.device("cpu") if use_cpu else None,
    )
    img = np.array(Image.open(input_path).convert("RGB"))
    output, _ = upsampler.enhance(img)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(output).save(str(output_path))
    return output_path


def run_upscale(
    input_path: Path | None,
    artist_slug: str | None,
    output_dir: Path | None,
    use_cpu: bool = False,
) -> list[Path]:
    """Upscale one or more images. Returns list of output paths."""
    if RRDBNet is None or RealESRGANer is None:
        raise click.ClickException("Install upscale deps: pip install realesrgan basicsr")
    if torch is None:
        raise click.ClickException("Install torch: pip install torch")

    if input_path:
        if not input_path.exists():
            raise click.ClickException(f"Input file not found: {input_path}")
        inputs = [input_path]
    elif artist_slug:
        sel_dir = selected_dir(artist_slug)
        inputs = sorted(sel_dir.glob("*.png"))
    else:
        raise click.ClickException("Provide --input or --artist")

    if not inputs:
        msg = (
            f"No images found for artist {artist_slug}. Run curate first."
            if artist_slug
            else "No images found."
        )
        raise click.ClickException(msg)

    out_dir = output_dir or print_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not REALESRGAN_MODEL_PATH.exists():
        raise click.ClickException(
            f"Real-ESRGAN model not found at {REALESRGAN_MODEL_PATH}. Download it first."
        )

    use_cuda = torch.cuda.is_available() and not use_cpu
    model = RRDBNet(num_in_ch=3, num_out_ch=3, scale=4, num_feat=64, num_block=23, num_grow_ch=32)
    upsampler = RealESRGANer(
        scale=4,
        model_path=str(REALESRGAN_MODEL_PATH),
        model=model,
        tile=256,
        tile_pad=10,
        half=use_cuda,
        device=torch.device("cpu") if use_cpu else None,
    )

    results: list[Path] = []
    for p in inputs:
        img = np.array(Image.open(p).convert("RGB"))
        output, _ = upsampler.enhance(img)
        out_path = out_dir / p.name
        Image.fromarray(output).save(str(out_path))
        click.echo(f"Upscaled {p} -> {out_path}")
        results.append(out_path)
    return results


@click.command("upscale")
@click.option("--input", "input_path", default=None, type=click.Path(exists=True),
              help="Single image to upscale.")
@click.option("--artist", "artist_slug", default=None, help="Upscale all selected images for artist.")
@click.option("--output-dir", default=None, type=click.Path(), help="Output directory.")
@click.option("--public", "to_public", is_flag=True, help="Output to public/images/pieces/.")
@click.option("--cpu", "use_cpu", is_flag=True, help="Force CPU mode.")
def upscale(
    input_path: str | None,
    artist_slug: str | None,
    output_dir: str | None,
    to_public: bool,
    use_cpu: bool,
) -> None:
    """Upscale images with Real-ESRGAN x4 for print resolution."""
    inp = Path(input_path) if input_path else None
    if to_public:
        out = public_pieces_dir()
    elif output_dir:
        out = Path(output_dir)
    else:
        out = None
    run_upscale(inp, artist_slug, out, use_cpu=use_cpu)
