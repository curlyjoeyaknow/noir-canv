"""Product-style frame mockups on white background.

Two output types per piece:
  1. Flat front-facing: framed art centered on white background
  2. Angled perspective: 3D angled view showing frame depth, with shadow

Frame styles define matte width, frame width, and colors.
The artwork fills the frame edge-to-edge -- no extra borders added to
the source image. The frame adds its own matte.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


FRAME_STYLES: dict[str, dict] = {
    "natural-wood": {
        "matte_pct": 0.04,
        "frame_pct": 0.025,
        "matte_color": (255, 255, 255),
        "frame_color": (140, 110, 75),
        "frame_edge_color": (120, 92, 60),
    },
    "black": {
        "matte_pct": 0.04,
        "frame_pct": 0.02,
        "matte_color": (255, 255, 255),
        "frame_color": (30, 30, 30),
        "frame_edge_color": (20, 20, 20),
    },
    "white": {
        "matte_pct": 0.0,
        "frame_pct": 0.025,
        "matte_color": (255, 255, 255),
        "frame_color": (248, 248, 248),
        "frame_edge_color": (235, 235, 235),
    },
    "dark-wood": {
        "matte_pct": 0.04,
        "frame_pct": 0.025,
        "matte_color": (252, 250, 248),
        "frame_color": (55, 45, 35),
        "frame_edge_color": (40, 32, 24),
    },
    "gold": {
        "matte_pct": 0.035,
        "frame_pct": 0.022,
        "matte_color": (252, 250, 248),
        "frame_color": (185, 155, 95),
        "frame_edge_color": (160, 130, 70),
    },
}

DEFAULT_STYLE = "natural-wood"


def frame_flat(
    art_path: Path,
    output_path: Path,
    style_name: str = DEFAULT_STYLE,
) -> Path:
    """Create a flat front-facing framed artwork on white background."""
    style = FRAME_STYLES.get(style_name, FRAME_STYLES[DEFAULT_STYLE])
    art = Image.open(art_path).convert("RGB")
    aw, ah = art.size
    short_edge = min(aw, ah)

    matte_px = max(12, int(short_edge * style["matte_pct"])) if style["matte_pct"] > 0 else 0
    frame_px = max(8, int(short_edge * style["frame_pct"]))

    framed_w = aw + 2 * (matte_px + frame_px)
    framed_h = ah + 2 * (matte_px + frame_px)

    framed = Image.new("RGB", (framed_w, framed_h), style["frame_color"])

    if matte_px > 0:
        matte_box = (frame_px, frame_px, framed_w - frame_px, framed_h - frame_px)
        draw = ImageDraw.Draw(framed)
        draw.rectangle(matte_box, fill=style["matte_color"])

    art_x = frame_px + matte_px
    art_y = frame_px + matte_px
    framed.paste(art, (art_x, art_y))

    pad = int(short_edge * 0.08)
    canvas_w = framed_w + pad * 2
    canvas_h = framed_h + pad * 2
    canvas = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
    canvas.paste(framed, (pad, pad))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(str(output_path), quality=95)
    return output_path


def _find_coeffs(
    source: list[tuple[float, float]],
    target: list[tuple[float, float]],
) -> list[float]:
    matrix: list[list[float]] = []
    for s, t in zip(source, target):
        matrix.append([t[0], t[1], 1, 0, 0, 0, -s[0] * t[0], -s[0] * t[1]])
        matrix.append([0, 0, 0, t[0], t[1], 1, -s[1] * t[0], -s[1] * t[1]])
    a = np.matrix(matrix, dtype=np.float64)
    b = np.array(source).reshape(8)
    res = np.dot(np.linalg.inv(a.T @ a) @ a.T, b)
    return list(np.array(res).reshape(8))


def frame_angled(
    art_path: Path,
    output_path: Path,
    style_name: str = DEFAULT_STYLE,
    *,
    angle_strength: float = 0.12,
    depth_px_ratio: float = 0.02,
) -> Path:
    """Create a 3D angled framed artwork with depth and shadow on white bg.

    Mimics product photography: slight perspective showing frame edge,
    with a soft drop shadow.
    """
    style = FRAME_STYLES.get(style_name, FRAME_STYLES[DEFAULT_STYLE])
    art = Image.open(art_path).convert("RGB")
    aw, ah = art.size
    short_edge = min(aw, ah)

    matte_px = max(12, int(short_edge * style["matte_pct"])) if style["matte_pct"] > 0 else 0
    frame_px = max(8, int(short_edge * style["frame_pct"]))

    framed_w = aw + 2 * (matte_px + frame_px)
    framed_h = ah + 2 * (matte_px + frame_px)

    framed = Image.new("RGB", (framed_w, framed_h), style["frame_color"])
    if matte_px > 0:
        draw = ImageDraw.Draw(framed)
        draw.rectangle(
            (frame_px, frame_px, framed_w - frame_px, framed_h - frame_px),
            fill=style["matte_color"],
        )
    framed.paste(art, (frame_px + matte_px, frame_px + matte_px))

    depth = max(6, int(short_edge * depth_px_ratio))
    shrink_top = int(framed_h * angle_strength)
    shrink_bot = int(framed_h * angle_strength * 0.6)

    pad_x = depth + 60
    pad_y = shrink_top + 60
    out_w = framed_w + pad_x * 2
    out_h = framed_h + pad_y * 2

    src = [(0, 0), (framed_w, 0), (framed_w, framed_h), (0, framed_h)]
    tgt = [
        (pad_x, pad_y + shrink_top),
        (out_w - pad_x, pad_y),
        (out_w - pad_x, out_h - pad_y),
        (pad_x, out_h - pad_y - shrink_bot),
    ]

    coeffs = _find_coeffs(src, tgt)
    face = framed.transform(
        (out_w, out_h), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC,
    )
    face_mask = Image.new("L", (framed_w, framed_h), 255)
    face_mask = face_mask.transform(
        (out_w, out_h), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC,
    )

    edge_color = style.get("frame_edge_color", style["frame_color"])
    edge_strip = Image.new("RGB", (depth, framed_h), edge_color)
    edge_src = [(0, 0), (depth, 0), (depth, framed_h), (0, framed_h)]
    edge_tgt = [
        (pad_x - depth, pad_y + shrink_top),
        (pad_x, pad_y + shrink_top),
        (pad_x, out_h - pad_y - shrink_bot),
        (pad_x - depth, out_h - pad_y - shrink_bot - int(depth * 0.3)),
    ]
    edge_coeffs = _find_coeffs(edge_src, edge_tgt)
    edge_transformed = edge_strip.transform(
        (out_w, out_h), Image.Transform.PERSPECTIVE, edge_coeffs, Image.Resampling.BICUBIC,
    )
    edge_mask = Image.new("L", (depth, framed_h), 255)
    edge_mask = edge_mask.transform(
        (out_w, out_h), Image.Transform.PERSPECTIVE, edge_coeffs, Image.Resampling.BICUBIC,
    )

    shadow_layer = Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    shadow_offset = 10
    shadow_poly = [
        (tgt[0][0] + shadow_offset, tgt[0][1] + shadow_offset),
        (tgt[1][0] + shadow_offset, tgt[1][1] + shadow_offset),
        (tgt[2][0] + shadow_offset, tgt[2][1] + shadow_offset),
        (tgt[3][0] + shadow_offset, tgt[3][1] + shadow_offset),
    ]
    shadow_draw.polygon(shadow_poly, fill=(0, 0, 0, 50))
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=18))

    canvas = Image.new("RGBA", (out_w, out_h), (255, 255, 255, 255))
    canvas = Image.alpha_composite(canvas, shadow_layer)
    canvas_rgb = canvas.convert("RGB")

    canvas_rgb.paste(edge_transformed, (0, 0), mask=edge_mask)
    canvas_rgb.paste(face, (0, 0), mask=face_mask)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas_rgb.save(str(output_path), quality=95)
    return output_path


def generate_mockups(
    art_path: Path,
    output_dir: Path,
    slug: str,
    *,
    styles: list[str] | None = None,
) -> list[Path]:
    """Generate flat + angled mockups for each frame style.

    Returns list of all output paths.
    """
    style_list = styles or list(FRAME_STYLES.keys())
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[Path] = []

    for style_name in style_list:
        if style_name not in FRAME_STYLES:
            continue

        flat_path = output_dir / f"{slug}-{style_name}-flat.png"
        frame_flat(art_path, flat_path, style_name)
        results.append(flat_path)

        angled_path = output_dir / f"{slug}-{style_name}-angled.png"
        frame_angled(art_path, angled_path, style_name)
        results.append(angled_path)

    return results
