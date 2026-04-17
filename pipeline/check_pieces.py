import json, subprocess, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Check committed pieces.json
result = subprocess.check_output(["git", "show", "HEAD:data/pieces.json"], cwd=str(ROOT))
data = json.loads(result)
from collections import Counter
by_artist = Counter(p["artistSlug"] for p in data)
print("Committed pieces.json:")
for a, c in sorted(by_artist.items()):
    print(f"  {a}: {c} pieces")

print()
# Check image files exist
missing = []
for p in data:
    pub = ROOT / "apps/web/public" / p["imageUrl"].lstrip("/")
    if not pub.exists():
        missing.append((p["slug"], p["imageUrl"]))

if missing:
    print(f"MISSING {len(missing)} images:")
    for slug, url in missing[:10]:
        print(f"  {slug}: {url}")
else:
    print("All piece images exist ✓")

# Check artistSlug matches actual artists
artists = json.loads((ROOT / "data/artists.json").read_text(encoding="utf-8"))
artist_slugs = {a["slug"] for a in artists}
bad = [p for p in data if p["artistSlug"] not in artist_slugs]
if bad:
    print(f"\nBad artistSlug references ({len(bad)}):")
    for p in bad[:5]:
        print(f"  {p['slug']}: artistSlug={p['artistSlug']}")
else:
    print("All artistSlug references valid ✓")
