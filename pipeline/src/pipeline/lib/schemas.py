"""Pydantic models matching packages/shared/schemas/*.schema.json.

These are the Python-side data contracts for the Noir Canvas pipeline.
Every model uses ConfigDict(extra="forbid") to reject unknown fields,
ensuring strict parity with the JSON Schema source of truth.
"""

from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PricingTier(str, Enum):
    AFFORDABLE = "affordable"
    MID_RANGE = "mid-range"
    PREMIUM = "premium"


class AvailabilityStatus(str, Enum):
    AVAILABLE = "available"
    LOW_STOCK = "low-stock"
    RESERVED = "reserved"
    SOLD_OUT = "sold-out"
    ARCHIVED = "archived"


class MockupType(str, Enum):
    FRAMED = "framed"
    ROOM = "room"
    ARTIST_HOLDING = "artist-holding"


# ---------------------------------------------------------------------------
# Artist
# ---------------------------------------------------------------------------

class ArtistStyle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    medium: str = Field(..., min_length=2)
    palette: str = Field(..., min_length=2)
    subjects: str = Field(..., min_length=2)


class Artist(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str = Field(..., pattern=r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$", min_length=2, max_length=60)
    name: str = Field(..., min_length=2, max_length=100)
    bio: str = Field(..., min_length=50)
    artist_statement: str = Field(..., alias="artistStatement", min_length=20)
    portrait_url: str = Field(..., alias="portraitUrl", pattern=r"^/images/artists/")
    studio_image_urls: list[str] | None = Field(None, alias="studioImageUrls")
    influences: list[str] = Field(..., min_length=1)
    style: ArtistStyle
    pricing_tier: PricingTier = Field(..., alias="pricingTier")
    default_edition_size: int = Field(..., alias="defaultEditionSize", ge=1, le=500)

    @field_validator("influences")
    @classmethod
    def influences_non_empty_strings(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("influences must have at least one entry")
        for item in v:
            if not item.strip():
                raise ValueError("influence entries must not be empty")
        return v

    @field_validator("studio_image_urls")
    @classmethod
    def studio_urls_pattern(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        pattern = re.compile(r"^/images/artists/")
        for url in v:
            if not pattern.match(url):
                raise ValueError(f"studioImageUrl '{url}' must start with '/images/artists/'")
        return v


# ---------------------------------------------------------------------------
# Piece
# ---------------------------------------------------------------------------

PIECE_SLUG_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*-[0-9]{3}$")
SLUG_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")


class Piece(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str = Field(..., pattern=r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*-[0-9]{3}$")
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=20)
    artist_slug: str = Field(..., alias="artistSlug", pattern=r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
    image_url: str = Field(..., alias="imageUrl", pattern=r"^/images/pieces/")
    year: int | None = Field(None, ge=2024)
    medium: str | None = None
    dimensions: str | None = None
    edition_size: int = Field(..., alias="editionSize", ge=1, le=500)
    editions_sold: int = Field(..., alias="editionsSold", ge=0)
    reserved_count: int = Field(0, alias="reservedCount", ge=0)
    availability_status: AvailabilityStatus = Field(..., alias="availabilityStatus")
    price_cents: int = Field(..., alias="priceCents", ge=0)
    currency: str = Field("USD", pattern=r"^[A-Z]{3}$")
    tags: list[str] = Field(...)
    mockups: list[str] | None = None

    @field_validator("tags")
    @classmethod
    def tags_non_empty_strings(cls, v: list[str]) -> list[str]:
        for item in v:
            if not item.strip():
                raise ValueError("tag entries must not be empty")
        return v

    @field_validator("mockups")
    @classmethod
    def mockups_slug_format(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        for slug in v:
            if not SLUG_PATTERN.match(slug):
                raise ValueError(f"mockup slug '{slug}' has invalid format")
        return v


# ---------------------------------------------------------------------------
# Collection
# ---------------------------------------------------------------------------

class Collection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str = Field(..., pattern=r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$", min_length=2, max_length=60)
    name: str = Field(..., min_length=1, max_length=150)
    description: str = Field(..., min_length=10)
    cover_image_url: str = Field(..., alias="coverImageUrl", pattern=r"^/images/")
    piece_slugs: list[str] = Field(..., alias="pieceSlugs", min_length=1)
    featured: bool = Field(False)
    sort_order: int = Field(0, alias="sortOrder", ge=0)

    @field_validator("piece_slugs")
    @classmethod
    def piece_slugs_format(cls, v: list[str]) -> list[str]:
        for slug in v:
            if not PIECE_SLUG_PATTERN.match(slug):
                raise ValueError(f"piece slug '{slug}' must match '{{artistSlug}}-{{sequential}}' format")
        return v


# ---------------------------------------------------------------------------
# Mockup
# ---------------------------------------------------------------------------

class Mockup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str = Field(..., pattern=r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
    piece_slug: str = Field(..., alias="pieceSlug", pattern=r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*-[0-9]{3}$")
    type: MockupType
    variant: str = Field(..., min_length=1)
    image_url: str = Field(..., alias="imageUrl", pattern=r"^/images/")
    is_primary: bool = Field(False, alias="isPrimary")
    alt_text: str | None = Field(None, alias="altText")
    sort_order: int = Field(0, alias="sortOrder", ge=0)
