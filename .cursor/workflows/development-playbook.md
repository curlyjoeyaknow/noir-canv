# Noir Canvas v2 -- Development Playbook

## Overview

This playbook drives 11 development phases in dependency order. Each phase completes with a quality gate before the next begins. The orchestrator agent (`orchestrator.md`) follows this document as its runbook.

---

## Workflow Sequence

```
Pre-Development:  design -> plan -> decompose tasks -> assign subagents -> critical path

Phase  0: Project Structure
Phase  1: Schema + Contracts
Phase  2: Pipeline Core Lib        ─┐
Phase  5: Data Migration            ─┤ (parallelizable)
Phase  3: Pipeline Commands         ─┘ (after Phase 2)
Phase  4: Pipeline API
Phase  6: Frontend Core
Phase  7: Frontend Pages
Phase  8: Gallery Interactions
Phase  9: Design Polish
Phase 10: CI/CD + E2E

Quality Gate: runs after EVERY phase
```

---

## Pre-Development

Before any phase begins, the orchestrator must:

1. **Design**: Review `product-concept.mdc` and `AGENTS.md` to understand the product vision.
2. **Plan**: Confirm the phase sequence and identify parallelization opportunities.
3. **Decompose**: Break the current phase into concrete file-level tasks.
4. **Assign**: Map each task to a subagent by scope and domain expertise.
5. **Critical path**: Identify blocking dependencies within the phase.

---

## Phase Definitions

### Phase 0: Project Structure

| Field | Value |
|-------|-------|
| Agent | orchestrator (direct) |
| Scope | Root directories, config files, doc templates |
| Depends on | Nothing |

**Tasks**:
- Create directory skeleton per `architecture.mdc`:
  - `apps/web/app/`, `apps/web/components/`, `apps/web/lib/`, `apps/web/public/images/`
  - `pipeline/src/pipeline/commands/`, `pipeline/src/pipeline/lib/`, `pipeline/src/pipeline/api/`
  - `packages/shared/schemas/`
  - `data/`
  - `.github/workflows/`
  - `docs/adr/`
- Initialize `apps/web/package.json` (Next.js 16, TypeScript, Tailwind)
- Initialize `pipeline/pyproject.toml` (Click, FastAPI, Pydantic, uvicorn)
- Initialize `packages/shared/package.json`
- Wire existing `pnpm-workspace.yaml` and `turbo.json`
- Create `.env.example` with all required environment variables
- Create `docs/conventions.md` with naming conventions and doc templates

**Exit criteria**: All directories exist, all package managers can resolve dependencies, `pnpm install` succeeds.

---

### Phase 1: Schema + Contracts

| Field | Value |
|-------|-------|
| Agent | `schema-author` |
| Scope | `packages/shared/schemas/` |
| Depends on | Phase 0 |

**Tasks**:
- Define JSON Schema files: `artist.schema.json`, `piece.schema.json`, `collection.schema.json`, `mockup.schema.json`
- Generate Zod schemas -> `apps/web/lib/schemas.ts`
- Generate Pydantic models -> `pipeline/src/pipeline/lib/schemas.py`
- Create drift check script in `packages/shared/`
- Document ID conventions: `{artistSlug}-{sequential}` for pieces
- Document field rules: no `artistName` on Piece, collections as slug arrays

**Exit criteria**: JSON Schema files valid, Zod and Pydantic models generated and importable, drift check passes.

---

### Phase 2: Pipeline Core Lib

| Field | Value |
|-------|-------|
| Agent | `pipeline-porter` |
| Scope | `pipeline/src/pipeline/lib/` |
| Depends on | Phase 1 |

**Tasks**:
- Port from v1 (`c:\b2\noir-canv\pipeline\`):
  - `lib/config.py` -- Pydantic settings with `extra="forbid"`
  - `lib/paths.py` -- all paths via `pathlib.Path`
  - `lib/prompts.py` -- prompt templates for Gemini API
  - `lib/comfyui_client.py` -- ComfyUI WebSocket client
- All imports at top level, type hints on every function
- Replace `venv/bin/python` with cross-platform alternatives
- Import schemas from Phase 1

**Exit criteria**: All lib modules importable, type checks pass, no inline imports.

---

### Phase 3: Pipeline Commands

| Field | Value |
|-------|-------|
| Agent | `pipeline-porter` (port), `pipeline-phase-runner` (validate) |
| Scope | `pipeline/src/pipeline/commands/` |
| Depends on | Phase 2 |

**Tasks**:
- Port Click commands from v1:
  - `create_artist.py`, `generate.py`, `avatar.py`, `artist_studio.py`
  - `curate.py`, `frame.py`, `room_mockup.py`, `mockup.py`, `upscale.py`
- Wire CLI group in `pipeline/src/pipeline/__main__.py`
- Each command validates output against Phase 1 schemas before writing
- `pipeline-phase-runner` validates the full Phase 1-6 sequence is executable

**Exit criteria**: `python -m pipeline --help` shows all commands, each command's output schema validates.

---

### Phase 4: Pipeline API

| Field | Value |
|-------|-------|
| Agent | `api-builder` |
| Scope | `pipeline/src/pipeline/api/` |
| Depends on | Phase 3 |

**Tasks**:
- FastAPI app with router modules
- `X-API-Key` auth middleware on all mutation endpoints
- `BackgroundTasks` for GPU inference (never block handlers)
- Pydantic request/response models with `extra="forbid"`
- Path sandboxing -- validate all paths against allowed roots
- CORS from `ALLOWED_ORIGINS` env var
- OpenAPI spec generation for TypeScript client

**Exit criteria**: API starts, auth rejects unauthenticated mutations, background tasks enqueue correctly, OpenAPI spec generates.

---

### Phase 5: Data Migration (parallelizable with Phase 2-3)

| Field | Value |
|-------|-------|
| Agent | `data-migrator` |
| Scope | `data/` |
| Depends on | Phase 1 |

**Tasks**:
- Read v1 data from `c:\b2\noir-canv\src\lib\data\`
- Extract ~50 pieces with real titles and descriptions
- Discard ~97 "Pipeline selection" placeholder pieces
- Fix IDs to `{artistSlug}-{sequential}` format
- Remove denormalized `artistName` fields from pieces
- Output: `data/artists.json`, `data/pieces.json`, `data/collections.json`
- Validate every file against Phase 1 schemas

**Exit criteria**: All JSON files valid against schema, no placeholders, no ID collisions, no `artistName` on pieces.

---

### Phase 6: Frontend Core

| Field | Value |
|-------|-------|
| Agent | `frontend-builder`, `design-porter` |
| Scope | `apps/web/app/layout.tsx`, `apps/web/lib/`, `apps/web/components/` |
| Depends on | Phase 1, Phase 5 |

**Tasks**:
- Root layout with Inter (body) + Playfair Display (headings) via `next/font`
- `lib/data.ts` -- reads `data/*.json`, validates with Zod schemas from Phase 1
- Tailwind config with design tokens extracted from v1
- `globals.css` with CSS custom properties
- Shared components: `Header`, `Footer`, `ArtistCard`, `PieceCard`
- All Server Components, `next/image` for all images
- Components under 200 lines, one export per file

**Exit criteria**: `pnpm dev` renders root layout, data layer loads and validates, shared components render with mock data.

---

### Phase 7: Frontend Pages

| Field | Value |
|-------|-------|
| Agent | `frontend-builder` |
| Scope | `apps/web/app/` |
| Depends on | Phase 6 |

**Tasks**:
- `/` -- home/landing page
- `/artists` -- artist grid
- `/artists/[slug]/page.tsx` -- artist profile with `generateStaticParams`
- `/pieces/[slug]/page.tsx` -- piece detail with `generateStaticParams`
- `/collections/[slug]/page.tsx` -- collection page with `generateStaticParams`
- All async Server Components: `await params`, `notFound()` for missing
- No `"use client"` on any page file

**Exit criteria**: `pnpm build` generates all static pages, navigation works, `notFound()` triggers on bad slugs.

---

### Phase 8: Gallery Interactions

| Field | Value |
|-------|-------|
| Agent | `gallery-interaction-builder` |
| Scope | `apps/web/components/gallery/` |
| Depends on | Phase 7 |

**Tasks**:
- `ImageCarousel` -- keyboard arrows, touch swipe, dots, desktop arrows
- `ImageLightbox` -- pinch-zoom, Escape to close, click-outside
- `FrameSelector` -- real per-style image URLs (not CSS filters)
- `MockupViewer` -- room/frame composite display
- `EditionBadge` -- edition count with threshold styling
- All `"use client"`, all data via props, no direct fetching
- `Intl.NumberFormat` for prices, proper `aria-label` and `alt`

**Exit criteria**: All 5 components render, keyboard navigation works, props-only data flow verified.

---

### Phase 9: Design Polish

| Field | Value |
|-------|-------|
| Agent | `design-porter` |
| Scope | `apps/web/components/`, `apps/web/app/globals.css` |
| Depends on | Phase 8 |

**Tasks**:
- Visual parity pass against v1 (`c:\b2\noir-canv\src\`)
- Responsive refinement: 320px mobile through desktop
- WCAG contrast audit on all text/background combinations
- Typography hierarchy consistency (Inter vs Playfair usage)
- Spacing and padding consistency with design tokens
- Dark gallery aesthetic (noir theme)

**Exit criteria**: Visual comparison passes, WCAG contrast passes, responsive at 320px/768px/1024px/1440px.

---

### Phase 10: CI/CD + E2E

| Field | Value |
|-------|-------|
| Agent | `ci-builder`, `test-writer` |
| Scope | `.github/workflows/`, test files |
| Depends on | Phase 4, Phase 9 |

**Tasks**:
- GitHub Actions workflow: lint -> typecheck -> schema drift -> test -> build -> E2E
- `test-writer`: Vitest tests for components and data layer
- `test-writer`: Playwright E2E for navigation and gallery interactions
- `test-writer`: pytest for pipeline commands and API endpoints
- Cache strategies: pnpm store, `.next/cache`, Python venv
- Branch protection config recommendations

**Exit criteria**: CI workflow runs green on all stages, test coverage meets minimums, E2E passes.

---

## Quality Gate

Runs after **every** phase completes. All three steps must pass before advancing.

### Step 1: Hostile Code Review

**Agent**: `code-reviewer`

Review all files changed in the phase against all `.cursor/rules/*.mdc` files.

**Scoring formula**:
```
score = 100 - (CRITICAL x 15) - (HIGH x 8) - (MEDIUM x 3) - (LOW x 1)
```

**Pass thresholds**:

| File classification | Threshold | Matching patterns |
|-------------------|-----------|-------------------|
| Critical | >= 90 | `packages/shared/schemas/**`, `*/lib/data.ts`, `*/lib/schemas.*`, `*/lib/config.*`, `*/api/**`, `**/middleware.*` |
| Secondary | >= 80 | Everything else (components, styles, tests, config, docs) |

### Step 2: Remediation Loop

```
attempt = 0
while score < threshold AND attempt < 3:
    primary_agent fixes flagged issues (receives review findings as input)
    code-reviewer re-reviews ONLY changed files
    attempt += 1

if attempt == 3 AND score < threshold:
    ESCALATE to human with full findings report
    HALT workflow
```

### Step 3: Triple Audit (parallel)

Run all three in parallel. All must pass.

| Audit | Agent | Checks |
|-------|-------|--------|
| Boundary | `code-reviewer` | Files in correct locations per `architecture.mdc`, no cross-domain imports, no standalone scripts, one-way data flow |
| Schema | `schema-author` | Regenerate Zod + Pydantic from JSON Schema, `git diff --exit-code packages/shared/`, no denormalized fields |
| Security | `security-auditor` | SSRF, path traversal, missing auth, hardcoded secrets, open CORS, `execSync`, unsafe data handling |

**Failure handling**: Same remediation loop (max 3 attempts) per failing audit. Phase agent fixes, auditor re-checks.

### Advance or Escalate

```
if all 3 audits pass:
    log phase completion with scores
    advance to next phase
else:
    HALT and report to human
```

---

## Parallelization Map

| Phases | Can parallelize? | Reason |
|--------|-----------------|--------|
| 2 + 5 | Yes | Pipeline lib and data migration are independent after Phase 1 |
| 2 + 3 | No | Phase 3 depends on Phase 2 lib |
| 6 needs 1 + 5 | Both must complete | Frontend needs schemas and real data |
| 4 + 9 -> 10 | Phase 10 waits for both | CI/CD validates the full product |
| Triple audit steps | Yes | Boundary, schema, security are independent |

---

## Phase Completion Log

After each phase, the orchestrator records:

```
Phase: {number}
Status: PASS | FAIL
Review Score: {critical_score}/{secondary_score}
Remediation Attempts: {n}/3
Boundary Check: PASS | FAIL
Schema Check: PASS | FAIL
Security Audit: PASS | FAIL
Files Changed: {count}
Duration: {elapsed}
```

---

## Emergency Procedures

- **Gate failure after 3 attempts**: Stop all work. Report findings with file paths, severity, and violated rules. Wait for human decision.
- **Schema drift detected**: Halt frontend and pipeline work. `schema-author` resolves drift first. Re-run affected phase gates.
- **Security CRITICAL found**: Immediate halt. `security-auditor` provides full report. No advancement until resolved.
- **Cross-domain boundary violation**: `code-reviewer` flags exact files. Offending code must move to correct domain before re-check.
