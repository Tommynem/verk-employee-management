# Phase 4: API Routes

## Overview

FastAPI routes with HTMX responses following VaWW patterns.

**Blocked on**: Figma design transcription (for response templates)

---

## Route Structure

### TimeEntry Routes

Location: `source/api/routers/time_entries.py`

| Method | Path | Response | HX-Trigger | Notes |
|--------|------|----------|------------|-------|
| GET | `/time-entries` | `_browser_time_entries.html` | - | List for current user, with filters |
| GET | `/time-entries/new` | `_new_time_entry.html` | - | New entry form |
| POST | `/time-entries` | `_detail_time_entry.html` | `timeEntryCreated` | Create entry |
| GET | `/time-entries/{id}` | `_detail_time_entry.html` | - | Single entry detail |
| GET | `/time-entries/{id}/edit` | `_edit_time_entry.html` | - | Edit form |
| PATCH | `/time-entries/{id}` | `_detail_time_entry.html` | `timeEntryUpdated` | Update entry |
| DELETE | `/time-entries/{id}` | 204 No Content | `timeEntryDeleted` | Delete entry |

### UserSettings Routes (Future - HR View)

| Method | Path | Response | Notes |
|--------|------|----------|-------|
| GET | `/settings` | `_settings.html` | Current user's settings |
| PATCH | `/settings` | `_settings.html` | Update settings |

### Summary Routes

| Method | Path | Response | Notes |
|--------|------|----------|-------|
| GET | `/summary/week` | `_summary_week.html` | Weekly summary partial |
| GET | `/summary/month` | `_summary_month.html` | Monthly summary partial |

---

## Pydantic Schemas

Location: `source/api/schemas/time_entry.py`

### VaWW Pattern: Update -> Create -> Response

```python
from datetime import date, time, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from source.database.models import AbsenceType, RecordStatus

class TimeEntryUpdate(BaseModel):
    """Base with all mutable fields."""
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    break_minutes: Optional[int] = Field(None, ge=0, le=480)
    notes: Optional[str] = Field(None, max_length=500)
    absence_type: AbsenceType = AbsenceType.NONE

class TimeEntryCreate(TimeEntryUpdate):
    """Add required fields for creation."""
    work_date: date
    # user_id injected from auth context, not in schema

class TimeEntryResponse(TimeEntryUpdate):
    """Add read-only database fields."""
    id: int
    user_id: int
    work_date: date
    status: RecordStatus
    created_at: datetime
    updated_at: datetime

    # Calculated fields (not stored)
    actual_hours: Decimal
    target_hours: Decimal
    balance: Decimal

    model_config = ConfigDict(from_attributes=True)
```

### UserSettings Schemas

```python
class UserSettingsUpdate(BaseModel):
    weekly_target_hours: Optional[Decimal] = Field(None, ge=0, le=60)
    carryover_hours: Optional[Decimal] = None
    schedule_json: Optional[dict] = None

class UserSettingsResponse(UserSettingsUpdate):
    id: int
    user_id: int
    weekly_target_hours: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

---

## Route Implementation Pattern

```python
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from source.api.context import render_template
from source.api.dependencies import get_db, get_current_user_id
from source.api.schemas.time_entry import TimeEntryCreate, TimeEntryUpdate
from source.database.models import TimeEntry
from source.services.time_calculation import TimeCalculationService

router = APIRouter(prefix="/time-entries", tags=["time-entries"])

@router.get("")
def list_time_entries(
    request: Request,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    month: int = None,  # Filter params
    year: int = None,
) -> HTMLResponse:
    """List time entries for current user."""
    entries = db.query(TimeEntry).filter(
        TimeEntry.user_id == user_id
    ).order_by(TimeEntry.work_date.desc()).all()

    html = render_template(
        request,
        "partials/_browser_time_entries.html",
        entries=entries
    )
    return HTMLResponse(content=html)

@router.post("", status_code=201)
def create_time_entry(
    request: Request,
    entry_data: TimeEntryCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> HTMLResponse:
    """Create a new time entry."""
    entry = TimeEntry(user_id=user_id, **entry_data.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)

    html = render_template(
        request,
        "partials/_detail_time_entry.html",
        entry=entry
    )
    response = HTMLResponse(content=html, status_code=201)
    response.headers["HX-Trigger"] = "timeEntryCreated"
    return response
```

---

## Dependencies

### get_current_user_id

For MVP, hardcode a test user. Later integrate with VaWW auth.

```python
def get_current_user_id() -> int:
    """Get current user ID from session/auth.

    MVP: Return hardcoded test user ID.
    Future: Integrate with VaWW authentication.
    """
    return 1  # Test user
```

---

## Query Filters

Support filtering by:
- `month` / `year` - Show entries for specific month
- `status` - DRAFT only, SUBMITTED only
- `absence_type` - Filter by absence type

```python
@router.get("")
def list_time_entries(
    request: Request,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2020, le=2100),
    status: Optional[RecordStatus] = None,
) -> HTMLResponse:
    query = db.query(TimeEntry).filter(TimeEntry.user_id == user_id)

    if month and year:
        start = date(year, month, 1)
        end = date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)
        query = query.filter(TimeEntry.work_date >= start, TimeEntry.work_date < end)

    if status:
        query = query.filter(TimeEntry.status == status)

    entries = query.order_by(TimeEntry.work_date.desc()).all()
    # ...
```

---

## TDD Test Cases

```python
class TestTimeEntryAPI:
    def test_list_entries_empty(self, client, db_session):
        """Empty list returns valid HTML"""

    def test_list_entries_with_data(self, client, db_session):
        """List shows existing entries"""

    def test_create_entry_success(self, client, db_session):
        """POST creates entry, returns detail partial"""

    def test_create_entry_duplicate_date(self, client, db_session):
        """POST with duplicate date returns 422"""

    def test_get_entry_detail(self, client, db_session):
        """GET /{id} returns detail partial"""

    def test_get_entry_not_found(self, client, db_session):
        """GET /{id} for missing entry returns 404"""

    def test_update_entry_success(self, client, db_session):
        """PATCH updates entry, returns detail partial"""

    def test_update_submitted_entry_fails(self, client, db_session):
        """PATCH on submitted entry returns 422"""

    def test_delete_entry_success(self, client, db_session):
        """DELETE returns 204, triggers event"""

    def test_filter_by_month(self, client, db_session):
        """GET with month/year filters correctly"""
```
