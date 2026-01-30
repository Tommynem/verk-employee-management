# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Vacation day tracking with German law compliance (Bundesurlaubsgesetz)
  - Initial vacation balance setting
  - Annual entitlement configuration
  - Carryover days with March 31 expiration deadline
  - KPI card showing remaining vacation days
  - Warning badges when vacation days are about to expire
  - VacationCalculationService with comprehensive business logic
  - Settings API endpoint PATCH /settings/vacation
  - 32 tests (23 unit tests, 9 integration tests)

### Changed

- Extended UserSettings model with vacation tracking fields (initial_balance, annual_entitlement, carryover_days, carryover_expiration)
- Enhanced settings page with vacation configuration section
- Time entries browser view now displays vacation balance in KPI card

### Fixed

- End time before start time validation (C2)
- Weekly summary calculation showing wrong week (C4)
- Non-existent time entry returning JSON instead of HTML error (C5)
- Invalid query parameters returning JSON instead of HTML error (C6)
- Double-click protection for form submissions (C7)
- Mobile touch targets too small (C8)
- Last-write-wins race condition via optimistic locking (C11)
- Settings race condition via optimistic locking (C12)
- Form labels missing `for` attribute accessibility (C14)
- Month mismatch error handling in data import (M6)
- Year boundary navigation displaying [object Object] (M8)
- Unsaved changes warning missing (M9)
- Export endpoint validation errors returning JSON (M10)
- Horizontal scroll indicator on mobile (M11)
- Header navigation text cutoff at 320px (M12)
- Delete HTMX error when entry in edit mode (M14)
- Confusing actual hours display for vacation/sick days (M15)
- Date picker year navigation broken (M16)
- Invalid date input accepted without validation (M17)
- Duplicate note text display (m2)
