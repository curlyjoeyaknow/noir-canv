# Noir Canvas -- Conventions

## Naming

### Slugs

All entity identifiers are URL-safe slugs: lowercase ASCII, digits, and hyphens only.

| Entity | Pattern | Example |
|--------|---------|---------|
| Artist | `[a-z][a-z0-9-]*` | `kai-voss` |
| Piece | `{artistSlug}-{NNN}` | `kai-voss-001` |
| Collection | `[a-z][a-z0-9-]*` | `midnight-abstractions` |
| Mockup | `[a-z][a-z0-9-]*` | `kai-voss-001-black-frame` |

Piece slugs embed their artist slug as a prefix followed by a three-digit sequential number.
This guarantees no cross-artist ID collisions.

### File Naming

| Domain | Convention | Example |
|--------|-----------|---------|
| React components | PascalCase `.tsx` | `PieceCard.tsx` |
| Pages/layouts | `page.tsx` / `layout.tsx` (Next.js convention) | `app/artists/[slug]/page.tsx` |
| TypeScript utilities | camelCase `.ts` | `lib/data.ts` |
| Python modules | snake_case `.py` | `commands/create_artist.py` |
| JSON Schema | kebab-case `.schema.json` | `artist.schema.json` |
| Data files | kebab-case `.json` | `artists.json` |
| CSS | `globals.css` (single global file) | `app/globals.css` |

### Image Paths

All image URLs in data files are relative paths starting with `/images/`:

```
/images/artists/{slug}.png       -- artist portrait
/images/pieces/{slug}.png        -- piece primary image
/images/collections/{slug}.jpg   -- collection cover
/images/mockups/{slug}.png       -- mockup visualization
```

## Data Contracts

- **Source of truth**: JSON Schema in `packages/shared/schemas/`
- **TypeScript**: Zod schemas in `apps/web/lib/schemas.ts`
- **Python**: Pydantic models in `pipeline/src/pipeline/lib/schemas.py`
- **Drift check**: `pnpm --filter @noir-canvas/shared drift-check`

All three representations must stay in sync. CI enforces this.

## Commit Messages

Follow conventional commits: `type: concise description`

Types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `style`, `ci`

## Component Guidelines

- One component per file, export name matches filename
- Max 200 lines per component file
- Server Components by default; only `"use client"` in leaf component files
- Never `"use client"` on `page.tsx` or `layout.tsx`
- `next/image` for all images with proper `sizes` and `alt`

## Pipeline Commands

All operations are Click CLI commands under `pipeline/src/pipeline/commands/`:

```
pipeline create-artist    -- Phase 1: create virtual artist
pipeline avatar           -- Phase 2: generate portrait
pipeline artist-studio    -- Phase 2: generate studio shots
pipeline generate         -- Phase 3: generate pieces
pipeline curate           -- Phase 4: select best pieces
pipeline upscale          -- Phase 4: upscale for print
pipeline mockup           -- Phase 5: generate mockups
pipeline frame            -- Phase 5: generate framed variants
pipeline room-mockup      -- Phase 5: generate room settings
pipeline register         -- Phase 6: publish to gallery
```
