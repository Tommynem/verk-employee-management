# CI Strategy

## Purpose

This document explains how CI should work for `verk-employee-management`, how it relates to the broader `verk` stack, and how the pipeline should evolve as the project matures toward integration and commercial release.

---

## Project context

`verk-employee-management` is an early-stage extension module intended for integration into the Verk ERP ecosystem.

Key facts:
- currently in early development with a small user base providing active feedback
- shares the Python + FastAPI + SQLAlchemy + Tailwind CSS tech stack with `verk`
- eventual integration as a proper Verk module is planned within 1–2 months
- commercial release targeted for Q3–Q4 2026

The project is in **foundational quality** mode:
- stakes are low today, but investing in quality tooling now will pay off at integration time
- the goal is to arrive at the integration point with a mature, trustworthy CI baseline rather than scrambling to build one under pressure
- stack sharing with `verk` means CI patterns, reusable workflows, and tooling decisions here should be made with the broader ecosystem in mind

---

## CI philosophy

### 1) Build for the integration point, not just today
The pipeline should be good enough to trust now and structured well enough to merge into `verk`'s CI model later without major rework.

### 2) Share the verk stack contract where possible
`verk` and this module use the same Python toolchain. Where practical, CI decisions should align:
- same linting/formatting stack (black, isort, ruff)
- same test runner and coverage expectations
- same local command model (`make ci`, `make lint`, `make quality`)

Over time, this module should adopt reusable workflows or composite actions from `verk` rather than maintaining a fully separate CI infrastructure.

### 3) `make ci` is the local/GitHub parity contract
If `make ci` passes locally, GitHub's blocking checks should pass too.

Only blocking-quality checks belong in `make ci`. Broader diagnostics belong in `make quality` or `make prepush`.

### 4) Keep the blocking path lean
At this stage, blocking checks should focus on:
- code formatting and import hygiene
- linting for real bugs, not style preferences
- tests with a reasonable coverage threshold

Do not add blocking checks that will slow down the feedback cycle during early development. Advisory checks can carry heavier diagnostics.

### 5) Separate quality gates from automation
Any stats generation, reporting, or self-updating workflows should live in separate workflow files, not inside the main CI contract.

---

## Current local command model

## `make ci`
Meaning:
- GitHub blocking parity

Current scope:
- `black --check` (formatting)
- `isort --check-only` (import sorting)
- `ruff check` (linting)
- `pytest` with 80% coverage gate

Contract:
- local pass should predict a passing GitHub blocking pipeline
- only checks that mirror GitHub's blocking job belong here

## `make lint`
Meaning:
- standard local lint checks

## `make quality`
Meaning:
- extended diagnostics (mypy, deeper checks)
- useful during development but not yet blocking

## `make prepush`
Meaning:
- one-stop "is this push-worthy?" command
- combines `ci` + broader quality checks

---

## Current GitHub workflow model

### `ci.yml`

**Blocking job — "Lint, Format & Tests"**
- install Python (uv) and Node dependencies
- `black --check`
- `isort --check-only`
- `ruff check`
- Tailwind CSS build verification (catches broken templates/config)
- `pytest` with 80% coverage gate
- coverage artifact upload for visibility

**Advisory job — "Type Checking"**
- runs mypy after blocking checks pass
- `continue-on-error: true` — provides signal without blocking merges

### Workflow triggers
- push to `main` (filtered by relevant paths)
- pull requests targeting `main`
- manual dispatch

---

## Tool roles

### Blocking
- `black` — formatting
- `isort` — import sorting
- `ruff` — linting (errors, warnings, flake8-bugbear, comprehensions, pyupgrade)
- `pytest` — tests with coverage threshold
- Tailwind build — template/config sanity

### Advisory
- `mypy` — type checking (currently noisy, non-blocking)
- `pytest-cov` reporting — coverage trends and visibility

---

## Near-term improvement priorities

1. **Align with verk's CI model** — as verk's CI patterns stabilize, mirror them here. The local command surface, workflow structure, and blocking/advisory split should converge.
2. **Reusable workflows** — extract shared Python setup, lint, and test steps into composite actions or reusable workflows used by both `verk` and this module.
3. **Strengthen coverage policy** — as test coverage grows, consider raising the threshold or gating specific new code paths more strictly.
4. **Add security baseline** — dependency review, secret scanning, action pinning hygiene. Low priority now, but should be in place before commercial release.
5. **Separate concerns if automation is added** — if stats generation, changelog automation, or deployment workflows are introduced later, keep them in separate workflow files.

---

## What not to do

- do not build a fully independent CI platform that diverges from verk's stack
- do not add blocking checks that are too noisy for early-development velocity
- do not gate on legacy patterns before the module has legacy code to gate on
- do not skip quality tooling just because the stakes feel low now — the integration point will come faster than expected

---

## Maintenance rule

Update this document when:
- a check changes between blocking and advisory
- the meaning of `make ci`, `lint`, `quality`, or `prepush` changes
- reusable workflows are adopted from verk
- the project moves from early development to integration/release mode
- the coverage threshold or tooling stack changes materially
