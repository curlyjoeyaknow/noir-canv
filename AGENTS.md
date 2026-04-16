# Noir Canvas v2 -- Agent Instructions

## Project Overview

Noir Canvas is a premium limited-edition art gallery powered by AI-generated "virtual artists." This is a Turborepo monorepo with three domains:

| Domain | Location | Language | Purpose |
|--------|----------|----------|---------|
| Frontend | `apps/web/` | TypeScript (Next.js 16) | Gallery website, static generation |
| Pipeline | `pipeline/` | Python (Click CLI + FastAPI) | AI art generation, curation, mockups |
| Shared | `packages/shared/` | JSON Schema | Cross-language data contracts |
| Data | `data/` | JSON | Pipeline output consumed by frontend |

## Data Flow

```
pipeline/ (Python)
  |
  v
data/*.json (validated against packages/shared/schemas/)
  |
  v
apps/web/ (Next.js, reads at build time, validates with Zod)
```

- The pipeline writes. The frontend reads. Never the reverse.
- `packages/shared/schemas/` is the single source of truth for data shapes.
- If the pipeline outputs invalid JSON, the Next.js build fails. This is intentional.

## Rules

Every agent must follow these `.cursor/rules/*.mdc` files:

| Rule | Scope | Purpose |
|------|-------|---------|
| `architecture.mdc` | Always | Monorepo boundaries, file placement, data flow |
| `product-concept.mdc` | Always | Product vision, pipeline phases, creative principles |
| `nextjs-app-router.mdc` | `apps/web/**` | Server Components, static generation, image optimization |
| `data-contracts.mdc` | `packages/shared/**`, `data/**` | JSON Schema, Zod, Pydantic, no hardcoded arrays |
| `components.mdc` | `apps/web/components/**` | Component structure, accessibility, styling |
| `gallery-ux.mdc` | `apps/web/**` | Carousel, lightbox, frame selector, mockup viewer |
| `python-pipeline.mdc` | `pipeline/**` | CLI structure, Pydantic models, cross-platform paths |
| `testing.mdc` | Test files | Vitest, Playwright, pytest, coverage requirements |
| `ci-cd.mdc` | `.github/**` | CI stages, schema drift check, deployment |
| `security.mdc` | All code | No execSync, no open proxies, auth on mutations |
| `imports.mdc` | `**/*.{ts,tsx}` | Import order, path aliases, no circular imports |
| `git-hygiene.mdc` | Always | Gitignore, commit messages, file size limits |

## Critical Constraints

1. **Never create standalone scripts.** Every operation is a Click CLI command or a Next.js build step.
2. **Never hardcode data in TypeScript.** All gallery data comes from `data/*.json`.
3. **Never rewrite source files programmatically.** The pipeline writes JSON, not `.ts` files.
4. **Never use `"use client"` on a page file.** Pages are Server Components. Extract interactive parts to separate client component files.
5. **Never accept arbitrary filesystem paths from API input.** Validate and sandbox.
6. **Never block an API handler on GPU inference.** Use background tasks.

## V1 Reference

The v1 codebase at `c:\b2\noir-canv\` contains pipeline code worth porting. When porting:
- Fix cross-platform paths (use `pathlib.Path`)
- Move inline imports to module top
- Add type hints to all functions
- Replace any `venv/bin/python` references with cross-platform alternatives
- Validate output against JSON Schema before writing

---

## Specialized Agent Roles

### Infrastructure Agents

#### schema-author
- **Scope**: `packages/shared/schemas/`
- **Rules**: `data-contracts.mdc`
- **Task**: Define JSON Schema files for Artist, Piece, Collection, Mockup. Generate corresponding Zod schemas for TypeScript and Pydantic models for Python. Run drift checks.
- **Never**: Write application code, modify pages or components.

#### ci-builder
- **Scope**: `.github/workflows/`
- **Rules**: `ci-cd.mdc`
- **Task**: Set up GitHub Actions for lint, typecheck, test, build, schema drift detection, and E2E.
- **Never**: Modify application code.

#### test-writer
- **Scope**: `apps/web/**/*.test.tsx`, `apps/web/e2e/`, `pipeline/tests/`
- **Rules**: `testing.mdc`
- **Task**: Add Vitest, Playwright, and pytest tests. Write fixture files.
- **Never**: Modify the code under test.

### Frontend Agents

#### frontend-builder
- **Scope**: `apps/web/app/`, `apps/web/components/`
- **Rules**: `nextjs-app-router.mdc`, `components.mdc`, `gallery-ux.mdc`
- **Task**: Build Server Component pages, layouts, and extracted client component islands. Use data from `apps/web/lib/data.ts` exclusively.
- **Never**: Read from `pipeline/` directly, add `"use client"` to page files, use native `<img>`.

#### design-porter
- **Scope**: `apps/web/components/`, `apps/web/app/globals.css`
- **Rules**: `components.mdc`
- **Task**: Port visual design from v1 (`c:\b2\noir-canv\src\`). Extract Tailwind theme tokens, typography (Inter + Playfair Display), color palette, component markup. Adapt to Server Component patterns.
- **Never**: Change data access patterns or page routing.

#### gallery-interaction-builder
- **Scope**: `apps/web/components/gallery/`
- **Rules**: `gallery-ux.mdc`, `components.mdc`
- **Task**: Build `"use client"` interactive components: ImageCarousel, ImageLightbox, FrameSelector, MockupViewer, EditionBadge.
- **Never**: Fetch data directly -- receive all data as props from server component parents.

### Data Agents

#### data-migrator
- **Scope**: `data/`, `packages/shared/schemas/`
- **Rules**: `data-contracts.mdc`
- **Task**: Extract valuable content from `c:\b2\noir-canv\src\lib\data\` into `data/*.json`. Only port hand-written pieces with real descriptions (~50 pieces). Discard the 97 "Pipeline selection" placeholders. Fix ID collisions (`{artistSlug}-{sequential}` format). Remove denormalized `artistName` fields. Validate against shared JSON Schema.
- **Never**: Write TypeScript source code.

### Pipeline Agents

#### pipeline-porter
- **Scope**: `pipeline/src/pipeline/`
- **Rules**: `python-pipeline.mdc`
- **Task**: Port Python code from `c:\b2\noir-canv\pipeline\` to `pipeline/src/pipeline/`. Fix cross-platform paths, remove inline imports, add type hints. Key files: `commands/create_artist.py`, `commands/generate.py`, `commands/avatar.py`, `commands/artist_studio.py`, `commands/curate.py`, `commands/frame.py`, `commands/room_mockup.py`, `commands/mockup.py`, `commands/upscale.py`, `lib/config.py`, `lib/paths.py`, `lib/prompts.py`, `lib/schemas.py`, `lib/comfyui_client.py`.
- **Never**: Modify frontend code.

#### pipeline-phase-runner
- **Scope**: Full pipeline orchestration
- **Rules**: `product-concept.mdc`, `python-pipeline.mdc`
- **Task**: Orchestrate the full artist creation pipeline (Phase 1-6). Run individual phases or the full sequence. Validate output at each phase boundary using shared schemas.
- **Never**: Skip validation between phases.

#### api-builder
- **Scope**: `pipeline/src/pipeline/api/`
- **Rules**: `python-pipeline.mdc`, `security.mdc`
- **Task**: Port FastAPI endpoints with auth (API key), background tasks (no blocking on GPU inference), input validation (no arbitrary paths), env-based CORS. Generate OpenAPI spec for TypeScript client generation.
- **Never**: Accept raw filesystem paths from request input, block on long-running inference.

### Quality Agents

#### code-reviewer
- **Scope**: Entire repository
- **Rules**: All rules
- **Task**: Hostile review against all `.cursor/rules/*.mdc` files. Check for architecture drift, standalone scripts, schema inconsistencies, security issues, missing tests. Report findings with severity levels (CRITICAL, HIGH, MEDIUM, LOW).
- **Never**: Make changes -- report only.

#### security-auditor
- **Scope**: `**/*.{ts,tsx,py}`
- **Rules**: `security.mdc`
- **Task**: Check for SSRF, path traversal, missing auth, hardcoded secrets, open CORS, execSync in handlers. Scan both TypeScript and Python.
- **Never**: Make changes -- report only.
