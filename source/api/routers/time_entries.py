"""TimeEntry CRUD routes for Verk Employee Management.

Routes follow VaWW REST+HTMX pattern with HTML partial responses.
"""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, Response
from pydantic import ValidationError
from sqlalchemy import and_, extract
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from source.api.context import render_template
from source.api.dependencies import get_current_user_id, get_db
from source.api.schemas import TimeEntryCreate, TimeEntryUpdate
from source.database.enums import AbsenceType, RecordStatus
from source.database.models import TimeEntry, UserSettings
from source.services.time_calculation import TimeCalculationService

router = APIRouter(prefix="/time-entries", tags=["time-entries"])

# German month names
GERMAN_MONTHS = {
    1: "Januar",
    2: "Februar",
    3: "März",
    4: "April",
    5: "Mai",
    6: "Juni",
    7: "Juli",
    8: "August",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Dezember",
}


@router.get("", response_class=HTMLResponse)
async def list_time_entries(
    request: Request,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None, ge=2020, le=2100),
) -> HTMLResponse:
    """List time entries with optional month/year filtering.

    Args:
        request: FastAPI request object
        db: Database session
        user_id: Current user ID from auth
        month: Optional month filter (1-12)
        year: Optional year filter (2020-2100)

    Returns:
        HTML response with browser view of time entries
    """
    # Build query
    query = db.query(TimeEntry).filter(TimeEntry.user_id == user_id)

    # Apply filters if provided
    if month is not None and year is not None:
        query = query.filter(
            and_(
                extract("month", TimeEntry.work_date) == month,
                extract("year", TimeEntry.work_date) == year,
            )
        )

    # Order by date descending
    entries = query.order_by(TimeEntry.work_date.desc()).all()

    # Build context dictionary
    context = {"entries": entries}

    # Add monthly view context if month/year are specified
    if month is not None and year is not None:
        # Get or create UserSettings
        settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        if not settings:
            # Create default settings if not found (MVP: user_id=1)
            from decimal import Decimal

            settings = UserSettings(user_id=user_id, weekly_target_hours=Decimal("40.00"))
            db.add(settings)
            db.commit()
            db.refresh(settings)

        # Calculate monthly summary
        service = TimeCalculationService()
        summary = service.monthly_summary(entries, settings, year, month)

        # Calculate prev/next month navigation
        if month == 1:
            prev_month, prev_year = 12, year - 1
        else:
            prev_month, prev_year = month - 1, year

        if month == 12:
            next_month, next_year = 1, year + 1
        else:
            next_month, next_year = month + 1, year

        # Calculate next_date for "Add Next Day" button
        if entries:
            next_date = max(entry.work_date for entry in entries) + timedelta(days=1)
        else:
            next_date = date(year, month, 1)

        # Add all monthly context
        context.update(
            {
                "summary": summary,
                "month": month,
                "year": year,
                "month_name": GERMAN_MONTHS[month],
                "prev_month": prev_month,
                "prev_year": prev_year,
                "next_month": next_month,
                "next_year": next_year,
                "next_date": next_date,
            }
        )

    # Detect if this is an HTMX request
    is_htmx = request.headers.get("HX-Request") == "true"

    if is_htmx:
        # HTMX request - return partial only
        html = render_template(request, "partials/_browser_time_entries.html", **context)
    else:
        # Direct browser access - return full page
        html = render_template(request, "pages/time_entries.html", **context)

    return HTMLResponse(content=html, status_code=200)


@router.get("/new", response_class=HTMLResponse)
async def new_time_entry_form(
    request: Request,
    date: date | None = Query(None, alias="date"),
) -> HTMLResponse:
    """Show new time entry form.

    Args:
        request: FastAPI request object
        date: Optional default date for the form

    Returns:
        HTML response with new entry form
    """
    html = render_template(request, "partials/_new_time_entry.html", default_date=date)
    return HTMLResponse(content=html, status_code=200)


@router.get("/new-row", response_class=HTMLResponse)
async def new_row(
    request: Request,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    default_date: date | None = Query(None, alias="date"),
) -> HTMLResponse:
    """Get editable row partial for new entry.

    Fetches weekday defaults from user settings if available.

    Args:
        request: FastAPI request object
        db: Database session
        user_id: Current user ID
        default_date: Optional default date for the entry

    Returns:
        HTML response with editable row partial
    """
    # Default values
    default_start_time = None
    default_end_time = None
    default_break_minutes = 30

    # Fetch weekday defaults if date is provided
    if default_date:
        settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        if settings and settings.schedule_json:
            weekday_defaults = settings.schedule_json.get("weekday_defaults", {})
            # date.weekday() returns 0=Monday, 6=Sunday (matches our schema)
            weekday_key = str(default_date.weekday())
            day_defaults = weekday_defaults.get(weekday_key)

            if day_defaults:  # Not None (workday)
                default_start_time = day_defaults.get("start_time")
                default_end_time = day_defaults.get("end_time")
                default_break_minutes = day_defaults.get("break_minutes", 30)

    html = render_template(
        request,
        "partials/_row_time_entry_edit.html",
        entry=None,
        default_date=default_date,
        default_start_time=default_start_time,
        default_end_time=default_end_time,
        default_break_minutes=default_break_minutes,
        loop={"index": 0},
    )
    return HTMLResponse(content=html, status_code=200)


@router.post("", response_class=HTMLResponse, status_code=201)
async def create_time_entry(
    request: Request,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    work_date: date = Form(...),
    start_time: str | None = Form(None),
    end_time: str | None = Form(None),
    break_minutes: int = Form(0),
    absence_type: str = Form("none"),
    notes: str | None = Form(None),
) -> HTMLResponse:
    """Create new time entry.

    Args:
        request: FastAPI request object
        db: Database session
        user_id: Current user ID from auth
        work_date: Date of work entry
        start_time: Start time (HH:MM format)
        end_time: End time (HH:MM format)
        break_minutes: Break duration in minutes
        absence_type: Type of absence (none, vacation, sick, etc.)
        notes: Optional notes

    Returns:
        HTML response with detail view of created entry

    Raises:
        HTTPException: 422 if validation fails or duplicate entry exists
    """
    try:
        # Parse time strings to time objects if provided
        from datetime import time as dt_time

        parsed_start_time = None
        parsed_end_time = None

        if start_time:
            try:
                hours, minutes = map(int, start_time.split(":"))
                parsed_start_time = dt_time(hours, minutes)
            except (ValueError, AttributeError) as e:
                raise HTTPException(status_code=422, detail="Ungültige Startzeit") from e

        if end_time:
            try:
                hours, minutes = map(int, end_time.split(":"))
                parsed_end_time = dt_time(hours, minutes)
            except (ValueError, AttributeError) as e:
                raise HTTPException(status_code=422, detail="Ungültige Endzeit") from e

        # Validate with Pydantic schema
        entry_data = TimeEntryCreate(
            work_date=work_date,
            start_time=parsed_start_time,
            end_time=parsed_end_time,
            break_minutes=break_minutes,
            absence_type=AbsenceType(absence_type),
            notes=notes,
        )

        # Create database entry
        entry = TimeEntry(
            user_id=user_id,
            work_date=entry_data.work_date,
            start_time=entry_data.start_time,
            end_time=entry_data.end_time,
            break_minutes=entry_data.break_minutes,
            absence_type=entry_data.absence_type,
            notes=entry_data.notes,
            status=RecordStatus.DRAFT,
        )

        db.add(entry)
        try:
            db.commit()
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(status_code=422, detail="Eintrag für dieses Datum ist bereits vorhanden") from e

        db.refresh(entry)

        # Render row partial for inline editing
        html = render_template(
            request,
            "partials/_row_time_entry.html",
            entry=entry,
            loop={"index": 0},  # Provide mock loop context for standalone row
        )
        response = HTMLResponse(content=html, status_code=201)
        response.headers["HX-Trigger"] = "timeEntryCreated"
        return response

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.get("/{entry_id}", response_class=HTMLResponse)
async def get_time_entry(
    request: Request,
    entry_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> HTMLResponse:
    """Get time entry detail view.

    Args:
        request: FastAPI request object
        entry_id: Time entry ID
        db: Database session
        user_id: Current user ID from auth

    Returns:
        HTML response with detail view

    Raises:
        HTTPException: 404 if entry not found
    """
    entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id, TimeEntry.user_id == user_id).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Eintrag nicht gefunden")

    html = render_template(request, "partials/_detail_time_entry.html", entry=entry)
    return HTMLResponse(content=html, status_code=200)


@router.get("/{entry_id}/edit-row", response_class=HTMLResponse)
async def edit_row(
    request: Request,
    entry_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> HTMLResponse:
    """Get editable row partial for inline editing.

    Args:
        request: FastAPI request object
        entry_id: Time entry ID
        db: Database session
        user_id: Current user ID from auth

    Returns:
        HTML response with editable row for existing entry

    Raises:
        HTTPException: 404 if entry not found
    """
    entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id, TimeEntry.user_id == user_id).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Eintrag nicht gefunden")

    # Provide mock loop object for standalone rendering
    html = render_template(request, "partials/_row_time_entry_edit.html", entry=entry, loop={"index": 0})
    return HTMLResponse(content=html, status_code=200)


@router.get("/{entry_id}/row", response_class=HTMLResponse)
async def get_row(
    request: Request,
    entry_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> HTMLResponse:
    """Get read-only row partial for display.

    Args:
        request: FastAPI request object
        entry_id: Time entry ID
        db: Database session
        user_id: Current user ID from auth

    Returns:
        HTML response with read-only row for display

    Raises:
        HTTPException: 404 if entry not found
    """
    entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id, TimeEntry.user_id == user_id).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Eintrag nicht gefunden")

    # Provide mock loop object for standalone rendering
    html = render_template(request, "partials/_row_time_entry.html", entry=entry, loop={"index": 0})
    return HTMLResponse(content=html, status_code=200)


@router.get("/{entry_id}/edit", response_class=HTMLResponse)
async def edit_time_entry_form(
    request: Request,
    entry_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> HTMLResponse:
    """Show edit form for time entry.

    Args:
        request: FastAPI request object
        entry_id: Time entry ID
        db: Database session
        user_id: Current user ID from auth

    Returns:
        HTML response with edit form

    Raises:
        HTTPException: 404 if entry not found
    """
    entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id, TimeEntry.user_id == user_id).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Eintrag nicht gefunden")

    html = render_template(request, "partials/_edit_time_entry.html", entry=entry)
    return HTMLResponse(content=html, status_code=200)


@router.patch("/{entry_id}", response_class=HTMLResponse)
async def update_time_entry(
    request: Request,
    entry_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    start_time: str | None = Form(None),
    end_time: str | None = Form(None),
    break_minutes: int | None = Form(None),
    absence_type: str | None = Form(None),
    notes: str | None = Form(None),
) -> HTMLResponse:
    """Update time entry.

    Args:
        request: FastAPI request object
        entry_id: Time entry ID
        db: Database session
        user_id: Current user ID from auth
        start_time: Optional updated start time
        end_time: Optional updated end time
        break_minutes: Optional updated break minutes
        absence_type: Optional updated absence type
        notes: Optional updated notes

    Returns:
        HTML response with updated detail view

    Raises:
        HTTPException: 404 if entry not found, 422 if entry is submitted or validation fails
    """
    entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id, TimeEntry.user_id == user_id).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Eintrag nicht gefunden")

    # Check if entry is submitted (locked)
    if entry.status == RecordStatus.SUBMITTED:
        raise HTTPException(status_code=422, detail="Eingereichte Einträge können nicht bearbeitet werden")

    try:
        # Parse time strings if provided
        from datetime import time as dt_time

        parsed_start_time = entry.start_time
        parsed_end_time = entry.end_time

        if start_time is not None:
            try:
                hours, minutes = map(int, start_time.split(":"))
                parsed_start_time = dt_time(hours, minutes)
            except (ValueError, AttributeError) as e:
                raise HTTPException(status_code=422, detail="Ungültige Startzeit") from e

        if end_time is not None:
            try:
                hours, minutes = map(int, end_time.split(":"))
                parsed_end_time = dt_time(hours, minutes)
            except (ValueError, AttributeError) as e:
                raise HTTPException(status_code=422, detail="Ungültige Endzeit") from e

        # Build update data
        update_dict = {}
        if start_time is not None:
            update_dict["start_time"] = parsed_start_time
        if end_time is not None:
            update_dict["end_time"] = parsed_end_time
        if break_minutes is not None:
            update_dict["break_minutes"] = break_minutes
        if absence_type is not None:
            update_dict["absence_type"] = AbsenceType(absence_type)
        if notes is not None:
            update_dict["notes"] = notes

        # Validate with Pydantic schema
        if update_dict:
            TimeEntryUpdate(**update_dict)

        # Apply updates
        for key, value in update_dict.items():
            setattr(entry, key, value)

        db.commit()
        db.refresh(entry)

        # Render updated row partial for inline editing
        html = render_template(
            request,
            "partials/_row_time_entry.html",
            entry=entry,
            loop={"index": 0},  # Provide mock loop context for standalone row
        )
        response = HTMLResponse(content=html, status_code=200)
        response.headers["HX-Trigger"] = "timeEntryUpdated"
        return response

    except ValidationError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.delete("/{entry_id}", status_code=204)
async def delete_time_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> Response:
    """Delete time entry.

    Args:
        entry_id: Time entry ID
        db: Database session
        user_id: Current user ID from auth

    Returns:
        Empty 204 response with HX-Trigger header

    Raises:
        HTTPException: 404 if entry not found
    """
    entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id, TimeEntry.user_id == user_id).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Eintrag nicht gefunden")

    db.delete(entry)
    db.commit()

    response = Response(status_code=204)
    response.headers["HX-Trigger"] = "timeEntryDeleted"
    return response
