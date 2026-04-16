import { describe, expect, it } from "vitest";

import artistFixture from "../__fixtures__/artist.json";
import collectionFixture from "../__fixtures__/collection.json";
import pieceFixture from "../__fixtures__/piece.json";
import {
  artistSchema,
  collectionSchema,
  pieceSchema,
  validateArtists,
  validateCollections,
  validatePieces,
} from "./schemas";

describe("artistSchema", () => {
  it("accepts valid artist data", () => {
    const result = artistSchema.safeParse(artistFixture);
    expect(result.success).toBe(true);
  });

  it("rejects artist missing required name", () => {
    const { name: _, ...noName } = artistFixture;
    const result = artistSchema.safeParse(noName);
    expect(result.success).toBe(false);
  });

  it("rejects artist with bio shorter than 20 chars", () => {
    const result = artistSchema.safeParse({ ...artistFixture, bio: "Short" });
    expect(result.success).toBe(false);
  });

  it("rejects artist slug with uppercase", () => {
    const result = artistSchema.safeParse({
      ...artistFixture,
      slug: "Kai-Voss",
    });
    expect(result.success).toBe(false);
  });

  it("rejects artist with empty influences array", () => {
    const result = artistSchema.safeParse({
      ...artistFixture,
      influences: [],
    });
    expect(result.success).toBe(false);
  });

  it("rejects unknown extra fields (strictObject)", () => {
    const result = artistSchema.safeParse({
      ...artistFixture,
      unknownField: "nope",
    });
    expect(result.success).toBe(false);
  });

  it("rejects portraitUrl that does not start with /images/", () => {
    const result = artistSchema.safeParse({
      ...artistFixture,
      portraitUrl: "https://cdn.example.com/portrait.png",
    });
    expect(result.success).toBe(false);
  });
});

describe("pieceSchema", () => {
  it("accepts valid piece data", () => {
    const result = pieceSchema.safeParse(pieceFixture);
    expect(result.success).toBe(true);
  });

  it("rejects piece missing required title", () => {
    const { title: _, ...noTitle } = pieceFixture;
    const result = pieceSchema.safeParse(noTitle);
    expect(result.success).toBe(false);
  });

  it("rejects piece with invalid slug format", () => {
    const result = pieceSchema.safeParse({
      ...pieceFixture,
      slug: "bad-slug",
    });
    expect(result.success).toBe(false);
  });

  it("accepts piece slug matching {artist}-{nnn} format", () => {
    const result = pieceSchema.safeParse({
      ...pieceFixture,
      slug: "kai-voss-001",
    });
    expect(result.success).toBe(true);
  });

  it("rejects piece with denormalized artistName field", () => {
    const result = pieceSchema.safeParse({
      ...pieceFixture,
      artistName: "Kai Voss",
    });
    expect(result.success).toBe(false);
  });

  it("rejects piece with negative price", () => {
    const result = pieceSchema.safeParse({ ...pieceFixture, price: -10 });
    expect(result.success).toBe(false);
  });

  it("rejects piece with editionSize of zero", () => {
    const result = pieceSchema.safeParse({ ...pieceFixture, editionSize: 0 });
    expect(result.success).toBe(false);
  });
});

describe("collectionSchema", () => {
  it("accepts valid collection data", () => {
    const result = collectionSchema.safeParse(collectionFixture);
    expect(result.success).toBe(true);
  });

  it("rejects collection with empty pieceSlugs", () => {
    const result = collectionSchema.safeParse({
      ...collectionFixture,
      pieceSlugs: [],
    });
    expect(result.success).toBe(false);
  });

  it("rejects collection with invalid piece slug format", () => {
    const result = collectionSchema.safeParse({
      ...collectionFixture,
      pieceSlugs: ["not-a-valid-slug"],
    });
    expect(result.success).toBe(false);
  });
});

describe("validateArtists", () => {
  it("validates an array of artists", () => {
    const artists = validateArtists([artistFixture]);
    expect(artists).toHaveLength(1);
    expect(artists[0].slug).toBe("kai-voss");
  });

  it("throws on invalid artist data", () => {
    expect(() => validateArtists([{ bad: true }])).toThrow();
  });
});

describe("validatePieces", () => {
  it("validates an array of pieces", () => {
    const pieces = validatePieces([pieceFixture]);
    expect(pieces).toHaveLength(1);
    expect(pieces[0].slug).toBe("kai-voss-001");
  });

  it("throws on invalid piece data", () => {
    expect(() => validatePieces([{ bad: true }])).toThrow();
  });
});

describe("validateCollections", () => {
  it("validates an array of collections", () => {
    const collections = validateCollections([collectionFixture]);
    expect(collections).toHaveLength(1);
    expect(collections[0].slug).toBe("midnight-abstractions");
  });

  it("throws on invalid collection data", () => {
    expect(() => validateCollections([{ bad: true }])).toThrow();
  });
});
