# Phase 4: API Routes Implementation Plan

## Overview

Implement FastAPI routes for TimeEntry CRUD operations following VaWW patterns with HTMX responses. Use TDD methodology with stub templates initially.

**Note**: Figma templates are not yet transcribed. We proceed with stub templates that render basic HTML, allowing full API testing. Templates will be polished in Phase 5 (Frontend).

---

## Implementation Order

### Step 1: Pydantic Schemas (Foundation)

**File**: `source/api/schemas/time_entry.py`

Create VaWW-pattern schemas:
- `TimeEntryUpdate` - Base with mutable fields
- `TimeEntryCreate` - Inherits Update, adds work_date
- `TimeEntryResponse` - Adds id, timestamps, calculated fields

**Test File**: `tests/test_schemas_time_entry.py`

Test cases:
- Valid creation schema
- Validation: break_minutes range (0-480)
- Validation: notes max_length (500)
- Response includes calculated fields
- from_attributes works with ORM model

### Step 2: Auth Dependency

**File**: `source/api/dependencies.py`

Add `get_current_user_id()` dependency:
- MVP: Return hardcoded user_id=1
- Future: VaWW auth integration

### Step 3: Stub Templates

**Location**: `templates/partials/`

Create minimal stub templates:
- `_browser_time_entries.html` - Table listing entries
- `_detail_time_entry.html` - Single entry detail
- `_new_time_entry.html` - Create form
- `_edit_time_entry.html` - Edit form
- `_summary_week.html` - Weekly summary
- `_summary_month.html` - Monthly summary

### Step 4: TimeEntry Routes (TDD)

**File**: `source/api/routers/time_entries.py`

**Test File**: `tests/test_api_time_entries.py`

RED-GREEN-REFACTOR for each endpoint:

| Route | Test Cases |
|-------|------------|
| GET `/time-entries` | Empty list, with data, filter by month/year |
| GET `/time-entries/new` | Returns form HTML |
| POST `/time-entries` | Success, duplicate date 422, validation errors |
| GET `/time-entries/{id}` | Found, not found 404 |
| GET `/time-entries/{id}/edit` | Returns edit form |
| PATCH `/time-entries/{id}` | Success, submitted readonly 422 |
| DELETE `/time-entries/{id}` | Success 204, triggers HX-Trigger |

### Step 5: Summary Routes

**File**: `source/api/routers/summaries.py`

| Route | Test Cases |
|-------|------------|
| GET `/summary/week` | Current week, specific week param |
| GET `/summary/month` | Current month, specific year/month |

### Step 6: Wire Up Router

Update `source/api/app.py`:
- Include time_entries router
- Include summaries router

---

## Files to Create/Modify

### Create
- `source/api/schemas/time_entry.py`
- `source/api/routers/time_entries.py`
- `source/api/routers/summaries.py`
- `templates/partials/_browser_time_entries.html`
- `templates/partials/_detail_time_entry.html`
- `templates/partials/_new_time_entry.html`
- `templates/partials/_edit_time_entry.html`
- `templates/partials/_summary_week.html`
- `templates/partials/_summary_month.html`
- `tests/test_schemas_time_entry.py`
- `tests/test_api_time_entries.py`
- `tests/test_api_summaries.py`

### Modify
- `source/api/dependencies.py` - Add get_current_user_id
- `source/api/app.py` - Include routers
- `source/api/schemas/__init__.py` - Export schemas
- `source/api/routers/__init__.py` - Export routers

---

## TDD Test Cases (Detailed)

### test_schemas_time_entry.py (~8 tests)

```python
class TestTimeEntrySchemas:
    def test_create_schema_valid():
        """Valid TimeEntryCreate passes validation"""

    def test_create_schema_requires_work_date():
        """TimeEntryCreate requires work_date"""

    def test_update_schema_all_optional():
        """TimeEntryUpdate fields are all optional"""

    def test_break_minutes_validation_range():
        """break_minutes rejects values outside 0-480"""

    def test_notes_max_length():
        """notes rejects strings over 500 chars"""

    def test_absence_type_default():
        """absence_type defaults to NONE"""

    def test_response_from_orm():
        """TimeEntryResponse.model_validate works with ORM"""

    def test_response_includes_calculated():
        """Response includes actual_hours, target_hours, balance"""
```

### test_api_time_entries.py (~15 tests)

```python
class TestTimeEntryList:
    def test_list_entries_empty():
        """GET /time-entries returns empty list HTML"""

    def test_list_entries_with_data():
        """GET /time-entries returns entries in HTML"""

    def test_list_filter_by_month_year():
        """GET /time-entries?month=1&year=2026 filters correctly"""

class TestTimeEntryCreate:
    def test_create_entry_success():
        """POST /time-entries creates entry, returns detail"""

    def test_create_entry_duplicate_date():
        """POST with duplicate date returns 422"""

    def test_create_entry_validation_error():
        """POST with invalid data returns 422"""

    def test_create_entry_hx_trigger():
        """POST sets HX-Trigger: timeEntryCreated"""

class TestTimeEntryDetail:
    def test_get_entry_success():
        """GET /time-entries/{id} returns detail HTML"""

    def test_get_entry_not_found():
        """GET /time-entries/{id} for missing entry returns 404"""

class TestTimeEntryEdit:
    def test_get_edit_form():
        """GET /time-entries/{id}/edit returns edit form"""

class TestTimeEntryUpdate:
    def test_update_entry_success():
        """PATCH /time-entries/{id} updates and returns detail"""

    def test_update_submitted_entry_fails():
        """PATCH on SUBMITTED entry returns 422"""

    def test_update_entry_hx_trigger():
        """PATCH sets HX-Trigger: timeEntryUpdated"""

class TestTimeEntryDelete:
    def test_delete_entry_success():
        """DELETE /time-entries/{id} returns 204"""

    def test_delete_entry_hx_trigger():
        """DELETE sets HX-Trigger: timeEntryDeleted"""
```

### test_api_summaries.py (~6 tests)

```python
class TestWeeklySummary:
    def test_get_current_week():
        """GET /summary/week returns current week"""

    def test_get_specific_week():
        """GET /summary/week?week_start=2026-01-20 returns specific week"""

class TestMonthlySummary:
    def test_get_current_month():
        """GET /summary/month returns current month"""

    def test_get_specific_month():
        """GET /summary/month?year=2026&month=1 returns specific month"""

    def test_monthly_includes_carryover():
        """Monthly summary includes carryover_in/out"""
```

---

## Quality Gates

- [ ] All ~30 new tests pass
- [ ] Overall coverage >= 80%
- [ ] Type hints on all functions
- [ ] German error messages for validation
- [ ] VaWW route patterns followed
- [ ] HX-Trigger headers on mutations
- [ ] Code review (code-reviewer agent)

---

## Agent Delegation

1. **test-runner**: Write failing tests for schemas (RED)
2. **python-dev**: Implement schemas (GREEN)
3. **test-runner**: Write failing tests for routes (RED)
4. **python-dev**: Implement routes + stub templates (GREEN)
5. **code-reviewer**: Review implementation
6. **documenter**: Update CHANGELOG

---

## Risk Mitigation

- **Template stub approach**: Allows full API testing without final designs
- **Calculated fields**: Use TimeCalculationService in Response schema
- **User isolation**: Hardcoded user_id=1 for MVP, easy to swap later
- **HTMX compliance**: Verify HX-Trigger headers in all mutation tests
