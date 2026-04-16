"""Tests for pipeline Pydantic data models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pipeline.lib.schemas import Artist, Collection, Mockup, Piece


class TestArtistModel:
    def test_valid_data(self, valid_artist_data: dict) -> None:
        artist = Artist(**valid_artist_data)
        assert artist.slug == "test-artist"
        assert artist.name == "Test Artist"
        assert artist.pricing_tier.value == "premium"
        assert artist.default_edition_size == 15

    def test_rejects_extra_fields(self, valid_artist_data: dict) -> None:
        data = {**valid_artist_data, "extraField": "should fail"}
        with pytest.raises(ValidationError, match="extra"):
            Artist(**data)

    def test_rejects_invalid_slug(self, valid_artist_data: dict) -> None:
        data = {**valid_artist_data, "slug": "INVALID"}
        with pytest.raises(ValidationError, match="slug"):
            Artist(**data)

    def test_rejects_slug_starting_with_number(self, valid_artist_data: dict) -> None:
        data = {**valid_artist_data, "slug": "1bad-slug"}
        with pytest.raises(ValidationError, match="slug"):
            Artist(**data)

    def test_rejects_short_bio(self, valid_artist_data: dict) -> None:
        data = {**valid_artist_data, "bio": "Too short"}
        with pytest.raises(ValidationError, match="bio"):
            Artist(**data)

    def test_rejects_empty_influences(self, valid_artist_data: dict) -> None:
        data = {**valid_artist_data, "influences": []}
        with pytest.raises(ValidationError, match="influences"):
            Artist(**data)

    def test_rejects_empty_string_influence(self, valid_artist_data: dict) -> None:
        data = {**valid_artist_data, "influences": ["   "]}
        with pytest.raises(ValidationError, match="influence"):
            Artist(**data)

    def test_rejects_invalid_pricing_tier(self, valid_artist_data: dict) -> None:
        data = {**valid_artist_data, "pricingTier": "luxury"}
        with pytest.raises(ValidationError):
            Artist(**data)

    def test_rejects_invalid_portrait_url(self, valid_artist_data: dict) -> None:
        data = {**valid_artist_data, "portraitUrl": "https://external.com/pic.png"}
        with pytest.raises(ValidationError, match="portraitUrl"):
            Artist(**data)

    def test_rejects_zero_edition_size(self, valid_artist_data: dict) -> None:
        data = {**valid_artist_data, "defaultEditionSize": 0}
        with pytest.raises(ValidationError, match="defaultEditionSize"):
            Artist(**data)

    def test_all_pricing_tiers_accepted(self, valid_artist_data: dict) -> None:
        for tier in ("affordable", "mid-range", "premium"):
            data = {**valid_artist_data, "pricingTier": tier}
            artist = Artist(**data)
            assert artist.pricing_tier.value == tier


class TestPieceModel:
    def test_valid_data(self, valid_piece_data: dict) -> None:
        piece = Piece(**valid_piece_data)
        assert piece.slug == "test-artist-001"
        assert piece.title == "Golden Horizon"
        assert piece.edition_size == 15

    def test_rejects_invalid_slug_format(self, valid_piece_data: dict) -> None:
        data = {**valid_piece_data, "slug": "test-artist"}
        with pytest.raises(ValidationError, match="slug"):
            Piece(**data)

    def test_rejects_slug_without_three_digit_suffix(self, valid_piece_data: dict) -> None:
        data = {**valid_piece_data, "slug": "test-artist-01"}
        with pytest.raises(ValidationError, match="slug"):
            Piece(**data)

    def test_rejects_short_description(self, valid_piece_data: dict) -> None:
        data = {**valid_piece_data, "description": "Short desc"}
        with pytest.raises(ValidationError, match="description"):
            Piece(**data)

    def test_rejects_negative_price_cents(self, valid_piece_data: dict) -> None:
        data = {**valid_piece_data, "priceCents": -10}
        with pytest.raises(ValidationError):
            Piece(**data)

    def test_rejects_extra_fields(self, valid_piece_data: dict) -> None:
        data = {**valid_piece_data, "artistName": "should not be here"}
        with pytest.raises(ValidationError, match="extra"):
            Piece(**data)

    def test_accepts_optional_fields(self, valid_piece_data: dict) -> None:
        data = {
            **valid_piece_data,
            "dimensions": "24x36in",
            "medium": "Oil on canvas",
            "year": 2025,
            "mockups": ["black-frame"],
        }
        piece = Piece(**data)
        assert piece.dimensions == "24x36in"
        assert piece.year == 2025

    def test_rejects_year_before_2024(self, valid_piece_data: dict) -> None:
        data = {**valid_piece_data, "year": 2023}
        with pytest.raises(ValidationError, match="year"):
            Piece(**data)

    def test_rejects_empty_tag_string(self, valid_piece_data: dict) -> None:
        data = {**valid_piece_data, "tags": ["abstract", "  "]}
        with pytest.raises(ValidationError, match="tag"):
            Piece(**data)

    def test_rejects_invalid_mockup_slug(self, valid_piece_data: dict) -> None:
        data = {**valid_piece_data, "mockups": ["INVALID!"]}
        with pytest.raises(ValidationError, match="mockup slug"):
            Piece(**data)


class TestCollectionModel:
    def test_valid_data(self, valid_collection_data: dict) -> None:
        collection = Collection(**valid_collection_data)
        assert collection.slug == "warm-abstractions"
        assert collection.name == "Warm Abstractions"
        assert len(collection.piece_slugs) == 1

    def test_rejects_extra_fields(self, valid_collection_data: dict) -> None:
        data = {**valid_collection_data, "curatedBy": "someone"}
        with pytest.raises(ValidationError, match="extra"):
            Collection(**data)

    def test_rejects_empty_piece_slugs(self, valid_collection_data: dict) -> None:
        data = {**valid_collection_data, "pieceSlugs": []}
        with pytest.raises(ValidationError, match="pieceSlugs"):
            Collection(**data)

    def test_rejects_invalid_piece_slug_format(self, valid_collection_data: dict) -> None:
        data = {**valid_collection_data, "pieceSlugs": ["bad-slug"]}
        with pytest.raises(ValidationError, match="piece slug"):
            Collection(**data)

    def test_rejects_short_description(self, valid_collection_data: dict) -> None:
        data = {**valid_collection_data, "description": "Short"}
        with pytest.raises(ValidationError, match="description"):
            Collection(**data)


class TestMockupModel:
    def test_valid_data(self, valid_mockup_data: dict) -> None:
        mockup = Mockup(**valid_mockup_data)
        assert mockup.slug == "test-mockup-framed"
        assert mockup.type.value == "framed"
        assert mockup.variant == "black"

    def test_rejects_invalid_type(self, valid_mockup_data: dict) -> None:
        data = {**valid_mockup_data, "type": "poster"}
        with pytest.raises(ValidationError):
            Mockup(**data)

    def test_all_mockup_types_accepted(self, valid_mockup_data: dict) -> None:
        for mtype in ("framed", "room", "artist-holding"):
            data = {**valid_mockup_data, "type": mtype}
            mockup = Mockup(**data)
            assert mockup.type.value == mtype

    def test_rejects_invalid_piece_slug(self, valid_mockup_data: dict) -> None:
        data = {**valid_mockup_data, "pieceSlug": "bad-slug"}
        with pytest.raises(ValidationError, match="pieceSlug"):
            Mockup(**data)

    def test_rejects_extra_fields(self, valid_mockup_data: dict) -> None:
        data = {**valid_mockup_data, "resolution": "4k"}
        with pytest.raises(ValidationError, match="extra"):
            Mockup(**data)
