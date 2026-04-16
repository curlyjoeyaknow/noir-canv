"""Pre-generated room templates for fast, consistent artwork mockups.

Each template is a high-quality room photo with a defined "canvas zone"
where artwork gets perspective-composited. Templates are generated once
via Gemini and reused for every piece.

Canvas zone is defined as 4 corner coordinates (top-left, top-right,
bottom-right, bottom-left) as percentages of image dimensions,
allowing perspective-correct placement.
"""

from __future__ import annotations

import io
import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from pipeline.lib.paths import OUTPUT_DIR

logger = logging.getLogger(__name__)

TEMPLATES_DIR: Path = OUTPUT_DIR / "room_templates"
TEMPLATES_INDEX: Path = TEMPLATES_DIR / "index.json"


@dataclass
class CanvasZone:
    """Four corners of the canvas placement area as percentages (0.0-1.0)."""

    top_left: tuple[float, float]
    top_right: tuple[float, float]
    bottom_right: tuple[float, float]
    bottom_left: tuple[float, float]

    def to_pixel_coords(self, width: int, height: int) -> list[tuple[int, int]]:
        corners = [self.top_left, self.top_right, self.bottom_right, self.bottom_left]
        return [(int(x * width), int(y * height)) for x, y in corners]


@dataclass
class RoomTemplate:
    """A reusable room template with canvas placement metadata."""

    slug: str
    name: str
    description: str
    image_path: str
    canvas_zone: CanvasZone
    wall_color: str = "neutral"
    lighting: str = "natural"

    @property
    def full_path(self) -> Path:
        return TEMPLATES_DIR / self.image_path


ROOM_DEFINITIONS: list[dict] = [
    {
        "slug": "modern-living",
        "name": "Modern Living Room",
        "prompt": (
            "Professional interior photograph of a modern living room. Neutral tones, "
            "warm natural light from large windows. Minimalist furniture — a low sofa, "
            "a side table. A large EMPTY white wall behind the sofa, perfectly lit, "
            "ready for hanging artwork. No art on the walls. 8K, editorial photography."
        ),
        "canvas_zone": CanvasZone((0.25, 0.12), (0.75, 0.12), (0.75, 0.55), (0.25, 0.55)),
        "wall_color": "warm-white",
        "lighting": "natural",
    },
    {
        "slug": "gallery-dark",
        "name": "Dark Gallery Wall",
        "prompt": (
            "Professional photograph of a dark museum gallery room. Dark charcoal walls, "
            "dramatic focused gallery lighting from above. Empty wall space center frame. "
            "Polished concrete floor. No art on walls. Minimal, dramatic. 8K."
        ),
        "canvas_zone": CanvasZone((0.20, 0.10), (0.80, 0.10), (0.80, 0.65), (0.20, 0.65)),
        "wall_color": "dark-charcoal",
        "lighting": "gallery-spot",
    },
    {
        "slug": "gallery-white",
        "name": "White Gallery Wall",
        "prompt": (
            "Professional photograph of a clean white gallery space. Bright white walls, "
            "even diffused lighting. Empty wall center frame. Light wood floor. "
            "No art on walls. Pristine exhibition space. 8K."
        ),
        "canvas_zone": CanvasZone((0.22, 0.08), (0.78, 0.08), (0.78, 0.62), (0.22, 0.62)),
        "wall_color": "white",
        "lighting": "diffused",
    },
    {
        "slug": "midcentury-living",
        "name": "Mid-Century Living Room",
        "prompt": (
            "Professional interior photograph of a mid-century modern living room. "
            "Warm wood paneling, Eames chair, brass floor lamp. Large empty wall space "
            "above a credenza. Warm afternoon light. No art on walls. 8K editorial."
        ),
        "canvas_zone": CanvasZone((0.20, 0.10), (0.80, 0.10), (0.80, 0.58), (0.20, 0.58)),
        "wall_color": "warm-wood",
        "lighting": "warm-afternoon",
    },
    {
        "slug": "nordic-bedroom",
        "name": "Nordic Bedroom",
        "prompt": (
            "Professional photograph of a Nordic Scandinavian bedroom. Light wood, "
            "white linen bedding, plants on nightstand. Large empty wall above the bed, "
            "soft morning light. No art on walls. Minimal, calming. 8K."
        ),
        "canvas_zone": CanvasZone((0.25, 0.08), (0.75, 0.08), (0.75, 0.52), (0.25, 0.52)),
        "wall_color": "light-grey",
        "lighting": "morning",
    },
    {
        "slug": "home-office",
        "name": "Home Office",
        "prompt": (
            "Professional interior photograph of a modern home office. Clean desk, "
            "monitor, plant. Large empty wall behind the desk. Natural light from "
            "a side window. No art on walls. Productive, minimal. 8K."
        ),
        "canvas_zone": CanvasZone((0.22, 0.08), (0.78, 0.08), (0.78, 0.55), (0.22, 0.55)),
        "wall_color": "off-white",
        "lighting": "side-natural",
    },
    {
        "slug": "penthouse",
        "name": "Penthouse Living",
        "prompt": (
            "Professional photograph of a luxury penthouse living area. Floor-to-ceiling "
            "windows with city skyline, modern furniture, dark accent wall. Large empty "
            "dark wall space for artwork. Evening ambient lighting. No art. 8K."
        ),
        "canvas_zone": CanvasZone((0.18, 0.12), (0.72, 0.12), (0.72, 0.62), (0.18, 0.62)),
        "wall_color": "dark-accent",
        "lighting": "evening-ambient",
    },
    {
        "slug": "creative-studio",
        "name": "Creative Studio",
        "prompt": (
            "Professional photograph of an artist's creative studio converted to gallery. "
            "Exposed brick, industrial lighting, concrete floor. Large empty white wall "
            "section. Some art supplies visible in corners. No art on display wall. 8K."
        ),
        "canvas_zone": CanvasZone((0.20, 0.10), (0.80, 0.10), (0.80, 0.60), (0.20, 0.60)),
        "wall_color": "brick-white",
        "lighting": "industrial",
    },
    {
        "slug": "dining-room",
        "name": "Dining Room",
        "prompt": (
            "Professional interior photograph of an elegant dining room. Long wooden "
            "table, upholstered chairs, pendant lighting above. Large empty wall behind "
            "the table head. Warm evening light. No art on walls. 8K editorial."
        ),
        "canvas_zone": CanvasZone((0.28, 0.08), (0.72, 0.08), (0.72, 0.52), (0.28, 0.52)),
        "wall_color": "warm-neutral",
        "lighting": "pendant-warm",
    },
    {
        "slug": "hallway",
        "name": "Gallery Hallway",
        "prompt": (
            "Professional photograph of a long, well-lit hallway in a modern home. "
            "Clean walls, hardwood floor, natural light from end window. Empty wall "
            "on one side, perfect for a single artwork. Minimal, elegant. 8K."
        ),
        "canvas_zone": CanvasZone((0.15, 0.15), (0.60, 0.18), (0.58, 0.65), (0.17, 0.60)),
        "wall_color": "white",
        "lighting": "end-window",
    },
]


def _find_coeffs(
    source_coords: list[tuple[float, float]],
    target_coords: list[tuple[float, float]],
) -> list[float]:
    matrix: list[list[float]] = []
    for s, t in zip(source_coords, target_coords):
        matrix.append([t[0], t[1], 1, 0, 0, 0, -s[0] * t[0], -s[0] * t[1]])
        matrix.append([0, 0, 0, t[0], t[1], 1, -s[1] * t[0], -s[1] * t[1]])
    a_mat = np.matrix(matrix, dtype=np.float64)
    b_vec = np.array(source_coords).reshape(8)
    res = np.dot(np.linalg.inv(a_mat.T @ a_mat) @ a_mat.T, b_vec)
    return list(np.array(res).reshape(8))


def composite_art_into_room(
    framed_path: Path,
    template: RoomTemplate,
    output_path: Path,
    *,
    shadow: bool = True,
) -> Path:
    """Composite framed artwork into a room template with perspective transform."""
    room_img = Image.open(template.full_path).convert("RGBA")
    framed = Image.open(framed_path).convert("RGBA")
    rw, rh = room_img.size
    fw, fh = framed.size

    target_coords = template.canvas_zone.to_pixel_coords(rw, rh)
    source_coords = [(0, 0), (fw, 0), (fw, fh), (0, fh)]
    coeffs = _find_coeffs(source_coords, target_coords)

    transformed = framed.transform(
        (rw, rh), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC,
    )
    mask = Image.new("L", (fw, fh), 255)
    mask_transformed = mask.transform(
        (rw, rh), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC,
    )

    if shadow:
        shadow_layer = Image.new("RGBA", (rw, rh), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_layer)
        shadow_offset = 6
        shadow_coords = [
            (x + shadow_offset, y + shadow_offset)
            for x, y in target_coords
        ]
        shadow_draw.polygon(shadow_coords, fill=(0, 0, 0, 40))
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=8))
        room_img = Image.alpha_composite(room_img, shadow_layer)

    room_img.paste(transformed, (0, 0), mask=mask_transformed)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    room_img.convert("RGB").save(str(output_path))
    return output_path


def load_templates() -> list[RoomTemplate]:
    """Load all available room templates from the index."""
    if not TEMPLATES_INDEX.exists():
        return []
    data = json.loads(TEMPLATES_INDEX.read_text(encoding="utf-8"))
    templates: list[RoomTemplate] = []
    for entry in data:
        cz = entry.pop("canvas_zone")
        zone = CanvasZone(**cz)
        templates.append(RoomTemplate(**entry, canvas_zone=zone))
    return templates


def save_template_index(templates: list[RoomTemplate]) -> None:
    """Save the template index to disk."""
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    data = []
    for t in templates:
        d = {
            "slug": t.slug,
            "name": t.name,
            "description": t.description,
            "image_path": t.image_path,
            "canvas_zone": asdict(t.canvas_zone),
            "wall_color": t.wall_color,
            "lighting": t.lighting,
        }
        data.append(d)
    TEMPLATES_INDEX.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8",
    )


def generate_room_templates(
    gemini_model: str = "gemini-3.1-flash-image-preview",
) -> list[RoomTemplate]:
    """Generate all room template images via Gemini API. One-time operation."""
    try:
        from google import genai
        from google.genai import types as genai_types
    except ImportError:
        raise RuntimeError("Install google-genai: pip install google-genai")

    from pipeline.lib.config import get_settings
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY required")

    client = genai.Client(api_key=settings.gemini_api_key)
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

    templates: list[RoomTemplate] = []

    for defn in ROOM_DEFINITIONS:
        slug = defn["slug"]
        image_file = f"{slug}.png"
        image_path = TEMPLATES_DIR / image_file

        if image_path.exists():
            logger.info("Template %s already exists, skipping", slug)
            templates.append(RoomTemplate(
                slug=slug,
                name=defn["name"],
                description=defn["prompt"],
                image_path=image_file,
                canvas_zone=defn["canvas_zone"],
                wall_color=defn.get("wall_color", "neutral"),
                lighting=defn.get("lighting", "natural"),
            ))
            continue

        response = client.models.generate_content(
            model=gemini_model,
            contents=[defn["prompt"]],
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
            logger.warning("Failed to generate template: %s", slug)
            continue

        img.save(str(image_path))
        logger.info("Generated template: %s (%dx%d)", slug, img.width, img.height)

        templates.append(RoomTemplate(
            slug=slug,
            name=defn["name"],
            description=defn["prompt"],
            image_path=image_file,
            canvas_zone=defn["canvas_zone"],
            wall_color=defn.get("wall_color", "neutral"),
            lighting=defn.get("lighting", "natural"),
        ))

    save_template_index(templates)
    return templates
