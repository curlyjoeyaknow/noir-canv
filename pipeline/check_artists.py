import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
artists = json.load(open(ROOT / "data/artists.json", encoding="utf-8"))
pieces = json.load(open(ROOT / "data/pieces.json", encoding="utf-8"))
piece_artists = {p["artistSlug"] for p in pieces}

print(f"{'slug':25s} {'portrait':8s} {'pieces':6s} {'portraitUrl'}")
for a in artists:
    portrait = ROOT / "apps/web/public" / a["portraitUrl"].lstrip("/")
    has_portrait = "YES" if portrait.exists() else "NO"
    has_pieces = "YES" if a["slug"] in piece_artists else "NO"
    print(f"{a['slug']:25s} {has_portrait:8s} {has_pieces:6s} {a['portraitUrl']}")
