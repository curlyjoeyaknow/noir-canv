"""
Publish pipeline-generated pieces to the gallery.

For each artist:
1. Find all raw PNG images
2. Generate title + description via Gemini
3. Add piece records to data/pieces.json
4. Copy gallery-size images to apps/web/public/images/pieces/
"""
from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    print("ERROR: pip install google-genai")
    raise

try:
    from PIL import Image
except ImportError:
    print("ERROR: pip install Pillow")
    raise

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PUBLIC_PIECES = ROOT / "apps" / "web" / "public" / "images" / "pieces"
PUBLIC_ARTISTS = ROOT / "apps" / "web" / "public" / "images" / "artists"
RAW_DIR = ROOT / "pipeline" / "output" / "raw"

ARTISTS = ["ren-vale", "kai-vale", "river-strand", "ren-cross", "elara-nakamura", "nova-ash", "elara-chen", "vera-voss"]

GALLERY_SIZE = 1600
CARD_SIZE = 800

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def slug_from_title(title: str) -> str:
    s = title.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:60]


def gemini_title_description(img_path: Path, artist_name: str, style_ref: str) -> tuple[str, str]:
    """Generate a title and one-sentence description for a piece using Gemini."""
    img = Image.open(img_path).convert("RGB")
    # Resize to 512 for API efficiency
    img.thumbnail((512, 512))
    import io
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    img_bytes = buf.getvalue()

    prompt = (
        f"You are naming and describing original art for a premium gallery.\n"
        f"Artist: {artist_name}\nStyle: {style_ref}\n\n"
        f"Look at this artwork and respond with ONLY a JSON object, no markdown, no extra text:\n"
        f'{{ "title": "...", "description": "One evocative sentence (20-60 words) that describes the mood, subject, and technique." }}'
    )

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-image-preview",
                contents=[
                    genai_types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                    prompt,
                ],
            )
            text = response.text.strip()
            # Strip markdown code fences if present
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
            data = json.loads(text)
            return data["title"], data["description"]
        except Exception as e:
            print(f"  Gemini attempt {attempt+1}/3 failed: {e}")
            import time
            time.sleep(2 ** attempt)

    # Fallback
    return f"Untitled — {artist_name}", "An original work from the collection."


def process_image(src: Path, dest: Path, max_dim: int) -> None:
    img = Image.open(src).convert("RGB")
    if max(img.size) > max_dim:
        img.thumbnail((max_dim, max_dim), Image.LANCZOS)
    img.save(str(dest), "PNG", optimize=True)


def main() -> None:
    PUBLIC_PIECES.mkdir(parents=True, exist_ok=True)

    artists = json.loads((DATA_DIR / "artists.json").read_text(encoding="utf-8"))
    artist_map = {a["slug"]: a for a in artists}

    pieces = json.loads((DATA_DIR / "pieces.json").read_text(encoding="utf-8")) if (DATA_DIR / "pieces.json").exists() else []
    existing_slugs = {p["slug"] for p in pieces}

    edition_sizes = {"affordable": 30, "mid-range": 20, "premium": 15}
    prices = {"affordable": 14900, "mid-range": 24900, "premium": 39900}

    for artist_slug in ARTISTS:
        artist = artist_map.get(artist_slug)
        if not artist:
            print(f"SKIP {artist_slug}: not in artists.json")
            continue

        raw_dir = RAW_DIR / artist_slug / artist_slug
        if not raw_dir.exists():
            print(f"SKIP {artist_slug}: no raw output at {raw_dir}")
            continue

        images = sorted(raw_dir.glob("*.png"))
        if not images:
            print(f"SKIP {artist_slug}: 0 images")
            continue

        print(f"\n=== {artist['name']} ({len(images)} images) ===")

        # Count existing pieces for this artist to number sequentially
        artist_existing = [p for p in pieces if p.get("artistSlug") == artist_slug]
        counter = len(artist_existing) + 1

        tier = artist.get("pricingTier", "mid-range")
        edition_size = edition_sizes.get(tier, 20)
        price_cents = prices.get(tier, 24900)

        for img_path in images:
            seed = img_path.stem.replace(f"{artist_slug}-", "")
            piece_num = f"{counter:03d}"
            piece_slug = f"{artist_slug}-{piece_num}"

            if piece_slug in existing_slugs:
                print(f"  SKIP {piece_slug}: already registered")
                counter += 1
                continue

            print(f"  {piece_slug} <- {img_path.name}")
            print(f"    Generating title/description...")

            title, description = gemini_title_description(
                img_path, artist["name"],
                artist.get("style", {}).get("subjects", "contemporary art")
            )
            print(f"    Title: {title}")

            # Copy image to public
            public_img_name = f"{piece_slug}.png"
            public_img_path = PUBLIC_PIECES / public_img_name
            process_image(img_path, public_img_path, GALLERY_SIZE)
            print(f"    Copied -> public/images/pieces/{public_img_name}")

            piece = {
                "slug": piece_slug,
                "title": title,
                "description": description,
                "artistSlug": artist_slug,
                "imageUrl": f"/images/pieces/{public_img_name}",
                "editionSize": edition_size,
                "editionsSold": 0,
                "reservedCount": 0,
                "availabilityStatus": "available",
                "priceCents": price_cents,
                "currency": "USD",
                "tags": artist.get("style", {}).get("subjects", "").split(",")[:4] or ["contemporary"],
            }
            pieces.append(piece)
            existing_slugs.add(piece_slug)
            counter += 1

    # Write pieces.json
    (DATA_DIR / "pieces.json").write_text(
        json.dumps(pieces, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nWrote {len(pieces)} pieces to data/pieces.json")
    print("Done.")


if __name__ == "__main__":
    main()
