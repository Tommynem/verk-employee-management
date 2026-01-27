# Verk Employee Management Extension

## Core Principles

### 1. VaWW Component Reuse
Reuse production-grade components from VaWW main app via filesystem copies.

- VaWW location: `/Users/tomge/Documents/Git/vaww/the_great_rewiring`
- Copy components instead of rebuilding
- Modals, error pages, form patterns, table layouts are all candidates
- Maintain visual consistency with main app

### 2. Strict TDD Discipline
- 80% minimum coverage, target 90%
- RED-GREEN-REFACTOR cycle
- Tests written BEFORE implementation
- Playwright for HTMX frontend testing

### 3. VaWW Compatibility
- Template naming: `_browser_*`, `_detail_*`, `_new_*`, `_edit_*`
- Route patterns: REST with HTMX responses
- Schema inheritance: Update -> Create -> Response
- German error messages for user-facing validation

## Quick Commands

- `make test` - Run tests with coverage
- `make dev` - Start development server
- `make lint` - Run linting
- `make format` - Format code
- `make css` - Compile Tailwind CSS
