import { join } from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { mockReadFile, fixtures } = vi.hoisted(() => {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const fs = require("fs") as typeof import("node:fs");
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const path = require("path") as typeof import("node:path");
  const dir = path.join(__dirname, "..", "__fixtures__");

  const read = (name: string) => fs.readFileSync(path.join(dir, name), "utf-8");

  return {
    mockReadFile: vi.fn<(path: string, encoding: string) => string>(),
    fixtures: {
      artist: read("artist.json"),
      piece: read("piece.json"),
      soldOut: read("piece-sold-out.json"),
      almostGone: read("piece-almost-gone.json"),
      collection: read("collection.json"),
    },
  };
});

vi.mock("node:fs", () => ({
  readFileSync: mockReadFile,
  default: { readFileSync: mockReadFile },
}));

function setupMockData(overrides: Record<string, string> = {}) {
  const data: Record<string, string> = {
    "artists.json": `[${fixtures.artist}]`,
    "pieces.json": `[${fixtures.piece},${fixtures.soldOut},${fixtures.almostGone}]`,
    "collections.json": `[${fixtures.collection}]`,
    "mockups.json": "[]",
    ...overrides,
  };

  mockReadFile.mockImplementation((filePath: string) => {
    for (const [key, value] of Object.entries(data)) {
      if (filePath.includes(key)) return value;
    }
    return "[]";
  });
}

describe("data layer", () => {
  beforeEach(() => {
    vi.resetModules();
    mockReadFile.mockReset();
  });

  afterEach(() => {
    mockReadFile.mockReset();
  });

  describe("getArtists", () => {
    it("returns validated artist array", async () => {
      setupMockData();
      const { getArtists } = await import("@/lib/data");
      const artists = getArtists();
      expect(artists).toHaveLength(1);
      expect(artists[0].name).toBe("Kai Voss");
      expect(artists[0].slug).toBe("kai-voss");
    });
  });

  describe("getArtist", () => {
    it("returns the correct artist for a valid slug", async () => {
      setupMockData();
      const { getArtist } = await import("@/lib/data");
      const artist = getArtist("kai-voss");
      expect(artist).toBeDefined();
      expect(artist!.name).toBe("Kai Voss");
      expect(artist!.slug).toBe("kai-voss");
    });

    it("returns undefined for an unknown slug", async () => {
      setupMockData();
      const { getArtist } = await import("@/lib/data");
      expect(getArtist("nonexistent")).toBeUndefined();
    });
  });

  describe("getPieces", () => {
    it("returns validated piece array", async () => {
      setupMockData();
      const { getPieces } = await import("@/lib/data");
      const pieces = getPieces();
      expect(pieces).toHaveLength(3);
      expect(pieces[0].title).toBe("Dusk Amber II");
    });
  });

  describe("getPiece", () => {
    it("returns piece for a valid slug", async () => {
      setupMockData();
      const { getPiece } = await import("@/lib/data");
      const piece = getPiece("kai-voss-001");
      expect(piece).toBeDefined();
      expect(piece!.title).toBe("Dusk Amber II");
      expect(piece!.artistSlug).toBe("kai-voss");
    });

    it("returns undefined for an unknown slug", async () => {
      setupMockData();
      const { getPiece } = await import("@/lib/data");
      expect(getPiece("nonexistent-999")).toBeUndefined();
    });
  });

  describe("getPiecesByArtist", () => {
    it("returns only pieces matching the artist slug", async () => {
      setupMockData();
      const { getPiecesByArtist } = await import("@/lib/data");
      const pieces = getPiecesByArtist("kai-voss");
      expect(pieces).toHaveLength(3);
      for (const p of pieces) {
        expect(p.artistSlug).toBe("kai-voss");
      }
    });

    it("returns empty array for unknown artist slug", async () => {
      setupMockData();
      const { getPiecesByArtist } = await import("@/lib/data");
      expect(getPiecesByArtist("unknown-artist")).toEqual([]);
    });
  });

  describe("getCollections", () => {
    it("returns validated collections array", async () => {
      setupMockData();
      const { getCollections } = await import("@/lib/data");
      const collections = getCollections();
      expect(collections).toHaveLength(1);
      expect(collections[0].slug).toBe("midnight-abstractions");
      expect(collections[0].name).toBe("Midnight Abstracts");
    });
  });

  describe("getCollection", () => {
    it("returns the correct collection for a valid slug", async () => {
      setupMockData();
      const { getCollection } = await import("@/lib/data");
      const collection = getCollection("midnight-abstractions");
      expect(collection).toBeDefined();
      expect(collection!.name).toBe("Midnight Abstracts");
      expect(collection!.pieceSlugs).toContain("kai-voss-001");
    });

    it("returns undefined for an unknown slug", async () => {
      setupMockData();
      const { getCollection } = await import("@/lib/data");
      expect(getCollection("nonexistent")).toBeUndefined();
    });
  });

  describe("getCollectionPieces", () => {
    it("resolves piece slugs to piece objects", async () => {
      setupMockData();
      const { getCollectionPieces } = await import("@/lib/data");
      const pieces = getCollectionPieces("midnight-abstractions");
      expect(pieces.length).toBeGreaterThan(0);
      for (const p of pieces) {
        expect(p.artistSlug).toBe("kai-voss");
      }
    });

    it("returns empty array for unknown collection slug", async () => {
      setupMockData();
      const { getCollectionPieces } = await import("@/lib/data");
      expect(getCollectionPieces("nonexistent")).toEqual([]);
    });
  });

  describe("getArtistForPiece", () => {
    it("returns the artist matching the piece artistSlug", async () => {
      setupMockData();
      const { getPiece, getArtistForPiece } = await import("@/lib/data");
      const piece = getPiece("kai-voss-001")!;
      const artist = getArtistForPiece(piece);
      expect(artist).toBeDefined();
      expect(artist!.slug).toBe("kai-voss");
      expect(artist!.name).toBe("Kai Voss");
    });
  });

  describe("getArtistName", () => {
    it("returns artist display name for a known slug", async () => {
      setupMockData();
      const { getArtistName } = await import("@/lib/data");
      expect(getArtistName("kai-voss")).toBe("Kai Voss");
    });

    it("falls back to the slug for an unknown artist", async () => {
      setupMockData();
      const { getArtistName } = await import("@/lib/data");
      expect(getArtistName("unknown-artist")).toBe("unknown-artist");
    });
  });

  describe("getMockups", () => {
    it("returns empty array when mockups.json is empty", async () => {
      setupMockData();
      const { getMockups } = await import("@/lib/data");
      expect(getMockups()).toEqual([]);
    });

    it("gracefully returns empty array when mockups.json is missing", async () => {
      mockReadFile.mockImplementation((filePath: string) => {
        if (filePath.includes("mockups.json")) throw new Error("ENOENT");
        if (filePath.includes("artists.json")) return `[${fixtures.artist}]`;
        if (filePath.includes("pieces.json"))
          return `[${fixtures.piece},${fixtures.soldOut},${fixtures.almostGone}]`;
        if (filePath.includes("collections.json"))
          return `[${fixtures.collection}]`;
        return "[]";
      });

      const { getMockups } = await import("@/lib/data");
      expect(getMockups()).toEqual([]);
    });
  });

  describe("getMockupsForPiece", () => {
    it("returns empty array when no mockups exist", async () => {
      setupMockData();
      const { getMockupsForPiece } = await import("@/lib/data");
      expect(getMockupsForPiece("kai-voss-001")).toEqual([]);
    });
  });

  describe("cross-references", () => {
    it("every piece.artistSlug references an existing artist", async () => {
      setupMockData();
      const { getArtists, getPieces } = await import("@/lib/data");
      const artistSlugs = new Set(getArtists().map((a) => a.slug));
      for (const piece of getPieces()) {
        expect(artistSlugs.has(piece.artistSlug)).toBe(true);
      }
    });

    it("every collection pieceSlugs entry references an existing piece", async () => {
      setupMockData();
      const { getCollections, getPieces } = await import("@/lib/data");
      const pieceSlugs = new Set(getPieces().map((p) => p.slug));
      for (const collection of getCollections()) {
        for (const slug of collection.pieceSlugs) {
          expect(pieceSlugs.has(slug)).toBe(true);
        }
      }
    });
  });

  describe("data quality", () => {
    it("no piece has a placeholder description", async () => {
      setupMockData();
      const { getPieces } = await import("@/lib/data");
      for (const piece of getPieces()) {
        expect(piece.description).not.toContain("Pipeline selection");
      }
    });
  });

  describe("error handling", () => {
    it("throws when data fails schema validation", async () => {
      setupMockData({
        "artists.json": JSON.stringify([{ bad: "data" }]),
      });
      const { getArtists } = await import("@/lib/data");
      expect(() => getArtists()).toThrow();
    });

    it("throws when JSON file cannot be read", async () => {
      mockReadFile.mockImplementation(() => {
        throw new Error("ENOENT");
      });
      const { getArtists } = await import("@/lib/data");
      expect(() => getArtists()).toThrow("Failed to read");
    });
  });
});
