import { describe, it, expect } from "vitest";

import {
  validateArtists,
  validatePieces,
  validateCollections,
  validateMockups,
} from "@/lib/schemas";

const validArtist = {
  slug: "test-artist",
  name: "Test Artist",
  bio: "A long enough biography that exceeds the minimum character count for validation.",
  artistStatement: "A meaningful statement about art.",
  portraitUrl: "/images/artists/test-artist.png",
  influences: ["Rothko", "Monet"],
  style: {
    medium: "Abstract painting",
    palette: "Warm earth tones",
    subjects: "Color fields and horizons",
  },
  pricingTier: "premium",
  defaultEditionSize: 15,
};

const validPiece = {
  slug: "test-artist-001",
  title: "Golden Horizon",
  description: "A luminous expanse of amber and gold that invites contemplation.",
  artistSlug: "test-artist",
  imageUrl: "/images/pieces/golden-horizon.png",
  editionSize: 15,
  editionsSold: 5,
  availabilityStatus: "available",
  priceCents: 29900,
  tags: ["abstract", "warm tones"],
};

const validCollection = {
  slug: "warm-abstractions",
  name: "Warm Abstractions",
  description: "A curated set of warm abstract works from multiple artists.",
  coverImageUrl: "/images/collections/warm-abstractions.png",
  pieceSlugs: ["test-artist-001"],
};

const validMockup = {
  slug: "test-artist-001-framed-black",
  pieceSlug: "test-artist-001",
  type: "framed",
  variant: "black",
  imageUrl: "/images/mockups/test-artist-001-black.png",
};

describe("validateArtists", () => {
  it("accepts valid artist data", () => {
    const result = validateArtists([validArtist]);
    expect(result).toHaveLength(1);
    expect(result[0].slug).toBe("test-artist");
    expect(result[0].name).toBe("Test Artist");
  });

  it("accepts multiple valid artists", () => {
    const second = { ...validArtist, slug: "another-artist", name: "Another" };
    const result = validateArtists([validArtist, second]);
    expect(result).toHaveLength(2);
  });

  it("rejects artist missing required field (name)", () => {
    const { name: _, ...missing } = validArtist;
    expect(() => validateArtists([missing])).toThrow();
  });

  it("rejects artist with invalid slug format (uppercase)", () => {
    expect(() =>
      validateArtists([{ ...validArtist, slug: "INVALID" }]),
    ).toThrow();
  });

  it("rejects artist with slug starting with number", () => {
    expect(() =>
      validateArtists([{ ...validArtist, slug: "1bad-slug" }]),
    ).toThrow();
  });

  it("rejects artist with bio shorter than 20 chars", () => {
    expect(() =>
      validateArtists([{ ...validArtist, bio: "Too short" }]),
    ).toThrow();
  });

  it("rejects artist with empty influences array", () => {
    expect(() =>
      validateArtists([{ ...validArtist, influences: [] }]),
    ).toThrow();
  });

  it("rejects artist with invalid pricingTier", () => {
    expect(() =>
      validateArtists([{ ...validArtist, pricingTier: "luxury" }]),
    ).toThrow();
  });

  it("rejects artist with portraitUrl not starting with /images/", () => {
    expect(() =>
      validateArtists([{ ...validArtist, portraitUrl: "https://example.com/pic.png" }]),
    ).toThrow();
  });

  it("rejects extra fields (strictObject enforcement)", () => {
    expect(() =>
      validateArtists([{ ...validArtist, extraField: "nope" }]),
    ).toThrow();
  });
});

describe("validatePieces", () => {
  it("accepts valid piece data", () => {
    const result = validatePieces([validPiece]);
    expect(result).toHaveLength(1);
    expect(result[0].slug).toBe("test-artist-001");
    expect(result[0].title).toBe("Golden Horizon");
  });

  it("rejects piece with placeholder description", () => {
    expect(() =>
      validatePieces([{ ...validPiece, description: "Short" }]),
    ).toThrow();
  });

  it("rejects piece with invalid slug format (missing sequential)", () => {
    expect(() =>
      validatePieces([{ ...validPiece, slug: "test-artist" }]),
    ).toThrow();
  });

  it("rejects piece with uppercase in slug", () => {
    expect(() =>
      validatePieces([{ ...validPiece, slug: "Test-Artist-001" }]),
    ).toThrow();
  });

  it("rejects piece with negative priceCents", () => {
    expect(() =>
      validatePieces([{ ...validPiece, priceCents: -10 }]),
    ).toThrow();
  });

  it("rejects piece with editionSize < 1", () => {
    expect(() =>
      validatePieces([{ ...validPiece, editionSize: 0 }]),
    ).toThrow();
  });

  it("rejects piece with negative editionsSold", () => {
    expect(() =>
      validatePieces([{ ...validPiece, editionsSold: -1 }]),
    ).toThrow();
  });

  it("accepts piece with optional fields present", () => {
    const withOptional = {
      ...validPiece,
      dimensions: "24x36in",
      medium: "Oil on canvas",
      year: 2025,
      mockups: ["black-frame"],
    };
    const result = validatePieces([withOptional]);
    expect(result[0].dimensions).toBe("24x36in");
    expect(result[0].year).toBe(2025);
  });

  it("rejects piece with year before 2024", () => {
    expect(() =>
      validatePieces([{ ...validPiece, year: 2023 }]),
    ).toThrow();
  });
});

describe("validateCollections", () => {
  it("accepts valid collection data", () => {
    const result = validateCollections([validCollection]);
    expect(result).toHaveLength(1);
    expect(result[0].slug).toBe("warm-abstractions");
    expect(result[0].pieceSlugs).toContain("test-artist-001");
  });

  it("rejects collection with empty pieceSlugs", () => {
    expect(() =>
      validateCollections([{ ...validCollection, pieceSlugs: [] }]),
    ).toThrow();
  });

  it("rejects collection with description shorter than 10 chars", () => {
    expect(() =>
      validateCollections([{ ...validCollection, description: "Short" }]),
    ).toThrow();
  });

  it("rejects collection with invalid coverImageUrl", () => {
    expect(() =>
      validateCollections([{ ...validCollection, coverImageUrl: "http://bad.com/img.png" }]),
    ).toThrow();
  });
});

describe("validateMockups", () => {
  it("accepts valid mockup data", () => {
    const result = validateMockups([validMockup]);
    expect(result).toHaveLength(1);
    expect(result[0].type).toBe("framed");
    expect(result[0].variant).toBe("black");
  });

  it("rejects mockup with invalid type", () => {
    expect(() =>
      validateMockups([{ ...validMockup, type: "poster" }]),
    ).toThrow();
  });

  it("accepts all valid mockup types", () => {
    const types = ["framed", "room", "artist-holding"] as const;
    for (const type of types) {
      const result = validateMockups([{ ...validMockup, type }]);
      expect(result[0].type).toBe(type);
    }
  });

  it("rejects mockup with invalid pieceSlug format", () => {
    expect(() =>
      validateMockups([{ ...validMockup, pieceSlug: "bad-slug" }]),
    ).toThrow();
  });
});
