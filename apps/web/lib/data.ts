import { readFileSync } from "node:fs";
import { join } from "node:path";

import {
  validateArtists,
  validatePieces,
  validateCollections,
  validateMockups,
} from "@/lib/schemas";
import type { Artist, Piece, Collection, Mockup, AvailabilityStatus } from "@/lib/schemas";
import { formatPrice, availableEditions } from "@/lib/schemas";

const DATA_DIR = join(process.cwd(), "..", "..", "data");

function loadJson(filename: string): unknown {
  const filePath = join(DATA_DIR, filename);
  try {
    const raw = readFileSync(filePath, "utf-8");
    return JSON.parse(raw);
  } catch (err) {
    throw new Error(
      `Failed to read ${filename} from ${filePath}: ${err instanceof Error ? err.message : String(err)}`,
    );
  }
}

function loadArtists(): Artist[] {
  return validateArtists(loadJson("artists.json"));
}

function loadPieces(): Piece[] {
  return validatePieces(loadJson("pieces.json"));
}

function loadCollections(): Collection[] {
  return validateCollections(loadJson("collections.json"));
}

function loadMockups(): Mockup[] {
  try {
    return validateMockups(loadJson("mockups.json"));
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    if (msg.includes("ENOENT") || msg.includes("no such file")) {
      return [];
    }
    throw new Error(`Failed to load mockups: ${msg}`);
  }
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export function getArtists(): Artist[] {
  return loadArtists();
}

export function getArtist(slug: string): Artist | undefined {
  return loadArtists().find((a) => a.slug === slug);
}

export function getPieces(): Piece[] {
  return loadPieces();
}

export function getPiece(slug: string): Piece | undefined {
  return loadPieces().find((p) => p.slug === slug);
}

export function getArtistPieces(artistSlug: string): Piece[] {
  return loadPieces().filter((p) => p.artistSlug === artistSlug);
}

export const getPiecesByArtist = getArtistPieces;

export function getArtistForPiece(piece: Piece): Artist | undefined {
  return getArtist(piece.artistSlug);
}

export function getCollections(): Collection[] {
  return loadCollections();
}

export function getCollection(slug: string): Collection | undefined {
  return loadCollections().find((c) => c.slug === slug);
}

export function getCollectionPieces(collectionSlug: string): Piece[] {
  const collection = getCollection(collectionSlug);
  if (!collection) return [];
  const slugSet = new Set(collection.pieceSlugs);
  return loadPieces().filter((p) => slugSet.has(p.slug));
}

export function getArtistName(artistSlug: string): string {
  return getArtist(artistSlug)?.name ?? artistSlug;
}

export function getMockups(): Mockup[] {
  return loadMockups();
}

export function getMockupsForPiece(pieceSlug: string): Mockup[] {
  return loadMockups().filter((m) => m.pieceSlug === pieceSlug);
}

export function getFeaturedCollections(): Collection[] {
  return loadCollections()
    .filter((c) => c.featured)
    .sort((a, b) => (a.sortOrder ?? 0) - (b.sortOrder ?? 0));
}

export function getAvailablePieces(): Piece[] {
  return loadPieces().filter(
    (p) => p.availabilityStatus !== "archived",
  );
}

export function getPieceDisplayPrice(piece: Piece): string {
  return formatPrice(piece.priceCents, piece.currency);
}

export function getPieceAvailableCount(piece: Piece): number {
  return availableEditions(piece);
}

export { formatPrice, availableEditions };
export type { AvailabilityStatus };
