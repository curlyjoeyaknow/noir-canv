import { z } from "zod";

// ---------------------------------------------------------------------------
// Shared patterns
// ---------------------------------------------------------------------------

const slugPattern = /^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/;
const pieceSlugPattern = /^[a-z][a-z0-9]*(?:-[a-z0-9]+)*-[0-9]{3}$/;
const artistImagePattern = /^\/images\/artists\//;
const pieceImagePattern = /^\/images\/pieces\//;
const imagePattern = /^\/images\//;
const currencyPattern = /^[A-Z]{3}$/;

// ---------------------------------------------------------------------------
// Artist
// ---------------------------------------------------------------------------

const artistStyleSchema = z.strictObject({
  medium: z.string().min(2),
  palette: z.string().min(2),
  subjects: z.string().min(2),
});

export const pricingTierSchema = z.enum(["affordable", "mid-range", "premium"]);

export const artistSchema = z.strictObject({
  slug: z.string().min(2).max(60).regex(slugPattern),
  name: z.string().min(2).max(100),
  bio: z.string().min(50),
  artistStatement: z.string().min(20),
  portraitUrl: z.string().regex(artistImagePattern),
  studioImageUrls: z.array(z.string().regex(artistImagePattern)).optional(),
  influences: z.array(z.string().min(1)).min(1),
  style: artistStyleSchema,
  pricingTier: pricingTierSchema,
  defaultEditionSize: z.number().int().min(1).max(500),
});

export type Artist = z.infer<typeof artistSchema>;
export type ArtistStyle = z.infer<typeof artistStyleSchema>;
export type PricingTier = z.infer<typeof pricingTierSchema>;

// ---------------------------------------------------------------------------
// Piece
// ---------------------------------------------------------------------------

export const availabilityStatusSchema = z.enum([
  "available",
  "low-stock",
  "reserved",
  "sold-out",
  "archived",
]);

export const pieceSchema = z.strictObject({
  slug: z.string().regex(pieceSlugPattern),
  title: z.string().min(1).max(200),
  description: z.string().min(20),
  artistSlug: z.string().regex(slugPattern),
  imageUrl: z.string().regex(pieceImagePattern),
  year: z.number().int().min(2024).optional(),
  medium: z.string().optional(),
  dimensions: z.string().optional(),
  editionSize: z.number().int().min(1).max(500),
  editionsSold: z.number().int().min(0),
  reservedCount: z.number().int().min(0).default(0),
  availabilityStatus: availabilityStatusSchema,
  priceCents: z.number().int().min(0),
  currency: z.string().regex(currencyPattern).default("USD"),
  tags: z.array(z.string().min(1)),
  mockups: z.array(z.string().regex(slugPattern)).optional(),
});

export type Piece = z.infer<typeof pieceSchema>;
export type AvailabilityStatus = z.infer<typeof availabilityStatusSchema>;

// ---------------------------------------------------------------------------
// Collection
// ---------------------------------------------------------------------------

export const collectionSchema = z.strictObject({
  slug: z.string().min(2).max(60).regex(slugPattern),
  name: z.string().min(1).max(150),
  description: z.string().min(10),
  coverImageUrl: z.string().regex(imagePattern),
  pieceSlugs: z.array(z.string().regex(pieceSlugPattern)).min(1),
  featured: z.boolean().default(false),
  sortOrder: z.number().int().min(0).default(0),
});

export type Collection = z.infer<typeof collectionSchema>;

// ---------------------------------------------------------------------------
// Mockup
// ---------------------------------------------------------------------------

export const mockupTypeSchema = z.enum(["framed", "room", "artist-holding"]);

export const mockupSchema = z.strictObject({
  slug: z.string().regex(slugPattern),
  pieceSlug: z.string().regex(pieceSlugPattern),
  type: mockupTypeSchema,
  variant: z.string().min(1),
  imageUrl: z.string().regex(imagePattern),
  isPrimary: z.boolean().default(false),
  altText: z.string().optional(),
  sortOrder: z.number().int().min(0).default(0),
});

export type Mockup = z.infer<typeof mockupSchema>;
export type MockupType = z.infer<typeof mockupTypeSchema>;

// ---------------------------------------------------------------------------
// Validation helpers
// ---------------------------------------------------------------------------

export function validateArtists(data: unknown): Artist[] {
  return z.array(artistSchema).parse(data);
}

export function validatePieces(data: unknown): Piece[] {
  return z.array(pieceSchema).parse(data);
}

export function validateCollections(data: unknown): Collection[] {
  return z.array(collectionSchema).parse(data);
}

export function validateMockups(data: unknown): Mockup[] {
  return z.array(mockupSchema).parse(data);
}

// ---------------------------------------------------------------------------
// Business logic helpers
// ---------------------------------------------------------------------------

export function formatPrice(priceCents: number, currency: string = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(priceCents / 100);
}

export function availableEditions(piece: Piece): number {
  return Math.max(0, piece.editionSize - piece.editionsSold - piece.reservedCount);
}
