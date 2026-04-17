"""
Watch raw output directories for new artists and auto-publish when complete.
Adds artist to artists.json (from YAML config) and runs publish_pieces.py logic.
Run this in background while pipelines generate.
"""
from __future__ import annotations
import json, os, subprocess, sys, time
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "pipeline" / "output" / "raw"
ARTISTS_JSON = ROOT / "data" / "artists.json"
YAML_DIR = ROOT / "pipeline" / "content" / "artists"
PUBLISH_SCRIPT = ROOT / "pipeline" / "publish_pieces.py"

TARGET_COUNT = 8  # publish when we have at least this many images
CHECK_INTERVAL = 15  # seconds between checks
PUBLISHED = set()

PRICING = {"affordable": 14900, "mid-range": 24900, "premium": 39900}
EDITIONS = {"affordable": 30, "mid-range": 20, "premium": 15}


def load_artists() -> dict:
    return {a["slug"]: a for a in json.loads(ARTISTS_JSON.read_text(encoding="utf-8"))}


def yaml_to_artist(slug: str, cfg: dict) -> dict | None:
    name = cfg.get("name", slug.replace("-", " ").title())
    bio = cfg.get("bio", "")
    statement = cfg.get("statement", "")
    if not bio or len(bio) < 50:
        return None
    style_ref = cfg.get("style_reference", "")
    tier = cfg.get("pricing_tier", "mid-range")
    influences = [e.replace("_", " ").title() for e in cfg.get("example_artists", [])]
    return {
        "slug": slug,
        "name": name,
        "bio": bio,
        "artistStatement": statement or "I seek to capture the in-between—where possibility breathes.",
        "portraitUrl": f"/images/artists/{slug}/portrait.png",
        "studioImageUrls": [],
        "influences": influences or [style_ref[:40]],
        "style": {
            "medium": "Digital oil on canvas",
            "palette": "varied",
            "subjects": style_ref[:120],
        },
        "pricingTier": tier,
        "defaultEditionSize": EDITIONS.get(tier, 20),
    }


def add_to_artists_json(slug: str) -> bool:
    yaml_path = YAML_DIR / f"{slug}.yaml"
    if not yaml_path.exists():
        print(f"  No YAML for {slug}")
        return False
    cfg = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    artist = yaml_to_artist(slug, cfg)
    if not artist:
        print(f"  Bad artist data for {slug}")
        return False
    artists = json.loads(ARTISTS_JSON.read_text(encoding="utf-8"))
    if any(a["slug"] == slug for a in artists):
        print(f"  {slug} already in artists.json")
        return True
    artists.append(artist)
    ARTISTS_JSON.write_text(json.dumps(artists, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Added {name} ({slug}) to artists.json")
    return True


def publish_artist(slug: str) -> None:
    print(f"\n=== Auto-publishing {slug} ===")
    if not add_to_artists_json(slug):
        return
    env = {**os.environ, "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY", "")}
    result = subprocess.run(
        [sys.executable, str(PUBLISH_SCRIPT)],
        cwd=str(ROOT),
        env=env,
        capture_output=True, text=True
    )
    print(result.stdout[-2000:] if result.stdout else "(no output)")
    if result.returncode != 0:
        print("ERRORS:", result.stderr[-500:])
        return
    # Git commit and push
    subprocess.run(["git", "-C", str(ROOT), "add", "-A"], capture_output=True)
    msg = f"feat: publish {slug} gallery pieces"
    subprocess.run(["git", "-C", str(ROOT), "commit", "-m", msg], capture_output=True)
    subprocess.run(["git", "-C", str(ROOT), "push", "origin", "master"], capture_output=True)
    print(f"  Pushed {slug} to git")
    PUBLISHED.add(slug)


print("Watching for completed artist generations...")
print(f"Will publish when >= {TARGET_COUNT} images exist\n")

while True:
    current_artists = set(load_artists().keys())
    for artist_dir in RAW.iterdir():
        slug = artist_dir.name
        if slug in PUBLISHED or slug in current_artists:
            continue
        piece_dir = artist_dir / slug
        if not piece_dir.exists():
            continue
        count = len(list(piece_dir.glob("*.png")))
        print(f"  {slug}: {count} images", end="\r")
        if count >= TARGET_COUNT:
            publish_artist(slug)
    time.sleep(CHECK_INTERVAL)
