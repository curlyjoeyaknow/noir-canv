import { describe, it, expect } from "vitest";

import {
  getArtists,
  getArtist,
  getPieces,
  getArtistPieces,
  getCollections,
  getCollection,
  getCollectionPieces,
  getArtistName,
  getMockups,
} from "@/lib/data";

describe("getArtists", () => {
  it("returns a non-empty array", () => {
    const artists = getArtists();
    expect(artists.length).toBeGreaterThan(0);
  });

  it("returns artists with required fields", () => {
    const artists = getArtists();
    for (const artist of artists) {
      expect(artist.slug).toMatch(/^[a-z][a-z0-9-]*$/);
      expect(artist.name.length).toBeGreaterThan(0);
      expect(artist.bio.length).toBeGreaterThanOrEqual(20);
      expect(artist.influences.length).toBeGreaterThan(0);
    }
  });
});

describe("getArtist", () => {
  it("returns an artist by slug", () => {
    const artist = getArtist("kai-voss");
    expect(artist).toBeDefined();
    expect(artist!.name).toBe("Kai Voss");
    expect(artist!.slug).toBe("kai-voss");
  });

  it("returns undefined for unknown slug", () => {
    const artist = getArtist("nonexistent-artist-xyz");
    expect(artist).toBeUndefined();
  });
});

describe("getPieces", () => {
  it("returns a non-empty array", () => {
    const pieces = getPieces();
    expect(pieces.length).toBeGreaterThan(0);
  });

  it("returns pieces with valid slug format", () => {
    const pieces = getPieces();
    const slugPattern = /^[a-z][a-z0-9]*(?:-[a-z][a-z0-9]*)*-[0-9]{3}$/;
    for (const piece of pieces) {
      expect(piece.slug).toMatch(slugPattern);
    }
  });

  it("returns pieces with descriptions at least 20 chars", () => {
    const pieces = getPieces();
    for (const piece of pieces) {
      expect(piece.description.length).toBeGreaterThanOrEqual(20);
    }
  });
});

describe("getArtistPieces", () => {
  it("filters pieces by artist slug", () => {
    const pieces = getArtistPieces("kai-voss");
    expect(pieces.length).toBeGreaterThan(0);
    for (const piece of pieces) {
      expect(piece.artistSlug).toBe("kai-voss");
    }
  });

  it("returns empty array for unknown artist slug", () => {
    const pieces = getArtistPieces("nonexistent-artist-xyz");
    expect(pieces).toEqual([]);
  });
});

describe("getCollections", () => {
  it("returns a non-empty array", () => {
    const collections = getCollections();
    expect(collections.length).toBeGreaterThan(0);
  });

  it("returns collections with required fields", () => {
    const collections = getCollections();
    for (const collection of collections) {
      expect(collection.slug).toMatch(/^[a-z][a-z0-9-]*$/);
      expect(collection.name.length).toBeGreaterThan(0);
      expect(collection.pieceSlugs.length).toBeGreaterThan(0);
    }
  });
});

describe("getCollectionPieces", () => {
  it("resolves piece slugs to actual piece objects", () => {
    const collections = getCollections();
    const first = collections[0];
    const pieces = getCollectionPieces(first.slug);

    expect(pieces.length).toBeGreaterThan(0);
    for (const piece of pieces) {
      expect(first.pieceSlugs).toContain(piece.slug);
    }
  });

  it("returns empty array for unknown collection slug", () => {
    const pieces = getCollectionPieces("nonexistent-collection-xyz");
    expect(pieces).toEqual([]);
  });
});

describe("getArtistName", () => {
  it("returns artist name for known slug", () => {
    const name = getArtistName("kai-voss");
    expect(name).toBe("Kai Voss");
  });

  it("returns slug as fallback for unknown artist", () => {
    const name = getArtistName("unknown-artist");
    expect(name).toBe("unknown-artist");
  });
});

describe("getMockups", () => {
  it("returns an array (possibly empty if no mockups.json)", () => {
    const mockups = getMockups();
    expect(Array.isArray(mockups)).toBe(true);
  });
});

describe("cross-references", () => {
  it("every piece references an existing artist", () => {
    const artists = getArtists();
    const artistSlugs = new Set(artists.map((a) => a.slug));
    const pieces = getPieces();

    for (const piece of pieces) {
      expect(artistSlugs.has(piece.artistSlug)).toBe(true);
    }
  });

  it("every collection references existing pieces", () => {
    const pieces = getPieces();
    const pieceSlugs = new Set(pieces.map((p) => p.slug));
    const collections = getCollections();

    for (const collection of collections) {
      for (const slug of collection.pieceSlugs) {
        expect(pieceSlugs.has(slug)).toBe(true);
      }
    }
  });
});
