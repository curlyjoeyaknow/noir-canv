"""ComfyUI API client for advanced image generation workflows.

When ComfyUI is running (python main.py --listen --port 8188), this client
can execute workflows for inpainting, avatars, room mockups, etc.

The requests library is required at runtime.  The ComfyUI server URL
is read from PipelineSettings.comfyui_url (env var COMFYUI_URL).
"""

from __future__ import annotations

import logging
import re
import time
from pathlib import Path
from typing import Any

import requests

from pipeline.lib.config import get_settings

_SAFE_FILENAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT: int = 300
_POLL_INTERVAL_SECS: float = 2.0
_MAX_POLL_ITERATIONS: int = 120


def _base_url() -> str:
    """Return the ComfyUI server base URL from settings."""
    return get_settings().comfyui_url


# ---------------------------------------------------------------------------
# Server connectivity
# ---------------------------------------------------------------------------

def is_comfyui_available() -> bool:
    """Check if the ComfyUI server is reachable."""
    try:
        r = requests.get(f"{_base_url()}/system_stats", timeout=5)
        return r.status_code == 200
    except requests.RequestException:
        return False


# ---------------------------------------------------------------------------
# Prompt queue
# ---------------------------------------------------------------------------

def queue_prompt(
    workflow: dict[str, Any],
    timeout: int = DEFAULT_TIMEOUT,
) -> str | None:
    """Submit a workflow to ComfyUI. Returns prompt_id or None on failure."""
    try:
        r = requests.post(
            f"{_base_url()}/prompt",
            json={"prompt": workflow},
            timeout=timeout,
        )
        if r.status_code != 200:
            logger.warning("ComfyUI queue_prompt returned %d", r.status_code)
            return None
        data: dict[str, Any] = r.json()
        return data.get("prompt_id")
    except requests.RequestException:
        logger.exception("Failed to queue prompt on ComfyUI")
        return None


# ---------------------------------------------------------------------------
# History / results
# ---------------------------------------------------------------------------

def get_history(prompt_id: str) -> dict[str, Any] | None:
    """Get execution history for a prompt_id."""
    try:
        r = requests.get(f"{_base_url()}/history/{prompt_id}", timeout=30)
        if r.status_code != 200:
            return None
        return r.json().get(prompt_id)
    except requests.RequestException:
        return None


def get_output_images(
    prompt_id: str,
    output_dir: Path | None = None,
) -> list[Path]:
    """Poll for completion and return paths to output images.

    If output_dir is given, downloads images there via the ComfyUI /view
    endpoint.  Otherwise returns bare Path(filename) handles that the
    caller must resolve.
    """
    base = _base_url()
    for _ in range(_MAX_POLL_ITERATIONS):
        hist = get_history(prompt_id)
        if hist is None:
            time.sleep(1)
            continue

        if "outputs" in hist:
            images = _download_output_images(hist["outputs"], base, output_dir)
            if images:
                return images

        status_str = hist.get("status", {}).get("status_str", "")
        if status_str == "error":
            logger.error("ComfyUI execution error for prompt %s", prompt_id)
            return []

        time.sleep(_POLL_INTERVAL_SECS)

    logger.warning("Timed out waiting for ComfyUI prompt %s", prompt_id)
    return []


def _download_output_images(
    outputs: dict[str, Any],
    base: str,
    output_dir: Path | None,
) -> list[Path]:
    """Iterate over node outputs and download images."""
    images: list[Path] = []
    for _node_id, out in outputs.items():
        if "images" not in out:
            continue
        for img in out["images"]:
            filename: str = img["filename"]
            if not _SAFE_FILENAME_RE.match(filename):
                logger.warning("Skipping unsafe filename from ComfyUI: %s", filename)
                continue
            subdir: str = img.get("subfolder", "")
            try:
                r = requests.get(
                    f"{base}/view",
                    params={"filename": filename, "subfolder": subdir},
                    timeout=30,
                )
                if r.status_code != 200:
                    continue
                if output_dir:
                    output_dir.mkdir(parents=True, exist_ok=True)
                    out_path = output_dir / filename
                    out_path.write_bytes(r.content)
                    images.append(out_path)
                else:
                    images.append(Path(filename))
            except requests.RequestException:
                logger.exception("Failed to download image %s", filename)
    return images


# ---------------------------------------------------------------------------
# Image upload
# ---------------------------------------------------------------------------

def upload_image(path: Path, allowed_roots: list[Path] | None = None) -> str | None:
    """Upload an image to ComfyUI's input folder. Returns the stored filename.

    If allowed_roots is provided, path must reside within one of them.
    """
    if allowed_roots:
        resolved = path.resolve()
        if not any(resolved.is_relative_to(root.resolve()) for root in allowed_roots):
            raise ValueError(f"Path {path} is not within any allowed root")
    try:
        with path.open("rb") as f:
            r = requests.post(
                f"{_base_url()}/upload/image",
                files={"image": (path.name, f, "image/png")},
                timeout=60,
            )
        if r.status_code != 200:
            return None
        data: dict[str, Any] = r.json()
        return data.get("name", path.name)
    except requests.RequestException:
        logger.exception("Failed to upload image %s", path)
        return None


# ---------------------------------------------------------------------------
# Workflow builder
# ---------------------------------------------------------------------------

def build_txt2img_workflow(
    prompt: str,
    negative_prompt: str = "",
    width: int = 1024,
    height: int = 1024,
    steps: int = 30,
    cfg: float = 7.5,
    seed: int = 0,
    checkpoint: str = "sdxl_base_1.0.safetensors",
) -> dict[str, Any]:
    """Build a basic txt2img workflow dict for ComfyUI."""
    return {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "cfg": cfg,
                "denoise": 1,
                "latent_image": ["5", 0],
                "model": ["4", 0],
                "negative": ["7", 0],
                "positive": ["6", 0],
                "sampler_name": "euler",
                "scheduler": "normal",
                "seed": seed,
                "steps": steps,
            },
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": checkpoint},
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"batch_size": 1, "height": height, "width": width},
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["4", 1], "text": prompt},
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["4", 1], "text": negative_prompt},
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": "noir", "images": ["8", 0]},
        },
    }
