"""Shared fixtures for pipeline tests."""

from __future__ import annotations

import pytest

from pipeline.lib.schemas import Artist, ArtistStyle, Collection, Mockup, Piece


@pytest.fixture()
def valid_artist_data() -> dict:
    """Minimal valid Artist data matching the JSON Schema contract."""
    return {
        "slug": "test-artist",
        "name": "Test Artist",
        "bio": "A long enough biography that exceeds the minimum character count.",
        "artistStatement": "A meaningful statement about art.",
        "portraitUrl": "/images/artists/test-artist.png",
        "influences": ["Rothko", "Monet"],
        "style": {
            "medium": "Abstract painting",
            "palette": "Warm earth tones",
            "subjects": "Color fields and horizons",
        },
        "pricingTier": "premium",
        "defaultEditionSize": 15,
    }


@pytest.fixture()
def valid_piece_data() -> dict:
    """Minimal valid Piece data matching the JSON Schema contract."""
    return {
        "slug": "test-artist-001",
        "title": "Golden Horizon",
        "description": "A luminous expanse of amber and gold that invites contemplation.",
        "artistSlug": "test-artist",
        "imageUrl": "/images/pieces/golden-horizon.png",
        "editionSize": 15,
        "editionsSold": 5,
        "availabilityStatus": "available",
        "priceCents": 29900,
        "tags": ["abstract", "warm tones"],
    }


@pytest.fixture()
def valid_collection_data() -> dict:
    """Minimal valid Collection data matching the JSON Schema contract."""
    return {
        "slug": "warm-abstractions",
        "name": "Warm Abstractions",
        "description": "A curated set of warm abstract works from multiple artists.",
        "coverImageUrl": "/images/collections/warm-abstractions.png",
        "pieceSlugs": ["test-artist-001"],
    }


@pytest.fixture()
def valid_mockup_data() -> dict:
    """Minimal valid Mockup data matching the JSON Schema contract."""
    return {
        "slug": "test-mockup-framed",
        "pieceSlug": "test-artist-001",
        "type": "framed",
        "variant": "black",
        "imageUrl": "/images/mockups/test-artist-001-black.png",
    }
