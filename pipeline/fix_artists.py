"""One-shot script: adds the 6 pipeline-created artists back to data/artists.json
and ensures studioImageUrls is never null."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "data" / "artists.json"

data = json.loads(path.read_text(encoding="utf-8"))
existing = {a["slug"] for a in data}

new_artists = [
    {
        "slug": "river-strand",
        "name": "River Strand",
        "bio": "River Strand works in the space between the botanical and the surreal, weaving intricate linework with Art Nouveau-inspired forms. Their gallery-quality paintings layer organic motifs with muted pastel palettes that reward sustained attention.",
        "artistStatement": "I seek to capture the in-between—the moment before form settles, where possibility still breathes.",
        "portraitUrl": "/images/artists/river-strand/portrait.png",
        "studioImageUrls": [],
        "influences": ["James Jean", "Art Nouveau", "Botanical illustration"],
        "style": {
            "medium": "Oil and ink on canvas",
            "palette": "Muted pastels, ivory, sage, dusty rose",
            "subjects": "Botanical and figurative surrealism"
        },
        "pricingTier": "premium",
        "defaultEditionSize": 25
    },
    {
        "slug": "ren-cross",
        "name": "Ren Cross",
        "bio": "Ren Cross brings a cinematic darkness to portraiture, painting uncanny figures that hover between folk tale and dream. Deeply influenced by classic illustration, their work transforms the antique into something quietly unsettling.",
        "artistStatement": "Every face holds a story older than the person wearing it.",
        "portraitUrl": "/images/artists/ren-cross/portrait.png",
        "studioImageUrls": [],
        "influences": ["Travis Louie", "Victorian illustration", "Silent film"],
        "style": {
            "medium": "Gouache on panel",
            "palette": "Sepia, slate, pale gold",
            "subjects": "Gothic portraiture and creature studies"
        },
        "pricingTier": "mid-range",
        "defaultEditionSize": 25
    },
    {
        "slug": "elara-nakamura",
        "name": "Elara Nakamura",
        "bio": "Elara Nakamura merges Japanese woodblock tradition with Art Nouveau sinuousness, producing luminous figures that feel both ancient and contemporary. Her graceful compositions have drawn collectors from across the Pacific Rim.",
        "artistStatement": "Beauty is a discipline—every line must earn its place.",
        "portraitUrl": "/images/artists/elara-nakamura/portrait.png",
        "studioImageUrls": [],
        "influences": ["Audrey Kawasaki", "Mucha", "Hokusai"],
        "style": {
            "medium": "Ink and wood stain on birch panel",
            "palette": "Ivory, cherry blossom, deep lacquer",
            "subjects": "Female figures with floral and natural motifs"
        },
        "pricingTier": "premium",
        "defaultEditionSize": 20
    },
    {
        "slug": "nova-ash",
        "name": "Nova Ash",
        "bio": "Nova Ash paints softly luminous dreamscapes where figures dissolve into forests and starfields. Her work has a quality of remembered childhood wonder—approachable yet quietly melancholic.",
        "artistStatement": "I paint the places I go when I close my eyes.",
        "portraitUrl": "/images/artists/nova-ash/portrait.png",
        "studioImageUrls": [],
        "influences": ["Amy Sol", "Studio Ghibli", "Edward Lear"],
        "style": {
            "medium": "Acrylic on canvas",
            "palette": "Lavender, gold, soft teal",
            "subjects": "Dreamy figures in natural environments"
        },
        "pricingTier": "affordable",
        "defaultEditionSize": 30
    },
    {
        "slug": "elara-chen",
        "name": "Elara Chen",
        "bio": "Elara Chen fuses street art energy with fine art craft, building high-contrast works that carry the visual weight of propaganda posters and the emotional depth of protest art. Her bold compositions demand attention.",
        "artistStatement": "Art without urgency is decoration. I want my work to mean something.",
        "portraitUrl": "/images/artists/elara-chen/portrait.png",
        "studioImageUrls": [],
        "influences": ["Shepard Fairey", "Constructivism", "Street art"],
        "style": {
            "medium": "Mixed media on canvas",
            "palette": "Red, black, cream, gold",
            "subjects": "Graphic figurative and political imagery"
        },
        "pricingTier": "mid-range",
        "defaultEditionSize": 25
    },
    {
        "slug": "vera-voss",
        "name": "Vera Voss",
        "bio": "Vera Voss paints luminous figurative works of extraordinary technical refinement—gilded surfaces, cascading fabric, and translucent glazes that recall Old Master technique in a contemporary context. Her pieces are among the most sought-after in the collection.",
        "artistStatement": "Light is the subject. Everything else is just its occasion.",
        "portraitUrl": "/images/artists/vera-voss/portrait.png",
        "studioImageUrls": [],
        "influences": ["Brad Kunkle", "Klimt", "Vermeer"],
        "style": {
            "medium": "Oil and gold leaf on panel",
            "palette": "Gold, ivory, deep burgundy",
            "subjects": "Romantic figurative with gilded detail"
        },
        "pricingTier": "premium",
        "defaultEditionSize": 15
    }
]

added = 0
for artist in new_artists:
    if artist["slug"] not in existing:
        data.append(artist)
        added += 1

# Fix any null studioImageUrls
for a in data:
    if a.get("studioImageUrls") is None:
        a["studioImageUrls"] = []

path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Done. {len(data)} artists total, {added} new added.")
