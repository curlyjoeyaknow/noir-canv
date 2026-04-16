# Branch protection for `main`

This document describes recommended GitHub settings so merges to `main` stay aligned with the [CI workflow](../.github/workflows/ci.yml) and repository policy (see `.cursor/rules/ci-cd.mdc`).

## Require status checks before merging

Enable **Require status checks to pass before merging** and require these checks (names match the `name:` field of each job in `ci.yml`):

| Check | Purpose |
| --- | --- |
| Lint | ESLint (TypeScript) via Turborepo |
| Typecheck | `tsc --noEmit` |
| Schema drift | JSON Schema vs Zod vs Pydantic drift (`drift-check.js`) |
| Test | Vitest |
| Build | Next.js / Turborepo build |
| E2E | Playwright (uses production build artifact) |
| Python lint (ruff) | `ruff check pipeline/src/` |
| Python typecheck (mypy) | `mypy pipeline/src/pipeline/` |
| Python test (pytest) | `pytest pipeline/tests/` |

Treat **Schema drift** as a first-class merge gate: it catches contract drift before release and should never be bypassed for convenience.

Optional tightening:

- Require branches to be **up to date** before merging (reduces skew between green CI and the merge base).
- Use **Require conversation resolution** for review threads when using mandatory review.

## Require pull request reviews

- Require at least **one approval** on pull requests before merging to `main`.
- Optionally restrict which teams or people may dismiss reviews or push to protected branches.

## Block force pushes and deletion

- **Do not allow force pushes** to `main`.
- **Do not allow deletions** of `main`.

## Secrets and fork PRs

- Pipeline tests read **`GEMINI_API_KEY`** from GitHub Actions secrets (never committed). Ensure the secret exists for workflows that need it.
- Pull requests from **forks** do not receive repository secrets by default; decide whether fork PRs should run pytest without the key (skipped tests), use a read-only test key in an environment with approval rules, or require CI from branches on the canonical repo only.

## Optional rules

- **Require signed commits** if your org policy expects commit signing.
- **Require linear history** if you prefer squash-only merges and a linear `main`.
- **Restrict who can push** to `main` so day-to-day work always goes through PRs.

## Alignment with CI triggers

The `CI` workflow runs on **pushes to `main`** and **pull requests targeting `main`**. Branch protection should reference the jobs from that workflow file so required checks stay in sync when job names change.
