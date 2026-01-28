"""TimeEntry CRUD routes for Verk Employee Management.

Routes follow VaWW REST+HTMX pattern with HTML partial responses.
"""

from datetime import date, time, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, Response
from pydantic import ValidationError
from sqlalchemy import and_, extract
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from source.api.context import render_template
from source.api.dependencies import get_current_user_id, get_db
from source.api.schemas import TimeEntryCreate, TimeEntryUpdate
from source.core.holidays import is_holiday
from source.core.i18n import GERMAN_MONTHS
from source.database import calculations
from source.database.enums import AbsenceType, RecordStatus
from source.database.models import TimeEntry, UserSettings
from source.services.time_calculation import TimeCalculationService

router = APIRouter(prefix="/time-entries", tags=["time-entries"])


def get_daily_target_hours(db: Session, user_id: int = 1) -> Decimal:
    """Get daily target hours from user settings.

    Args:
        db: Database session
        user_id: User ID to fetch settings for

    Returns:
        Daily target hours (weekly_target_hours / 5) quantized to 2 decimal places.
        Returns 8.00 if no settings found.
    """
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if not settings:
        return Decimal("8.00")
    return (settings.weekly_target_hours / Decimal("5")).quantize(Decimal("0.01"))


def parse_time_string(time_str: str | None, field_name: str) -> time | None:
    """Parse time string in HH:MM format to time object.

    Args:
        time_str: Time string in HH:MM format or None
        field_name: Name of field for error message (e.g., "Startzeit", "Endzeit")

    Returns:
        Time object if parsing successful, None if input is None or empty

    Raises:
        HTTPException: 422 if time_str format is invalid
    """
    if not time_str:
        return None

    try:
        hours, minutes = map(int, time_str.split(":"))
        return time(hours, minutes)
    except (ValueError, AttributeError) as e:
        raise HTTPException(status_code=422, detail=f"Ungültige {field_name}") from e


def get_entry_context(entry: TimeEntry, db: Session, user_id: int) -> dict:
    """Prepare template context for a time entry with calculated values.

    Args:
        entry: TimeEntry instance
        db: Database session
        user_id: User ID to fetch settings for

    Returns:
        Dictionary with entry and calculated values (actual_hours, target_hours, balance, holiday info)
    """
    # Get user settings
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if not settings:
        # Create default settings if not found
        settings = UserSettings(user_id=user_id, weekly_target_hours=Decimal("40.00"))
        db.add(settings)
        db.commit()
        db.refresh(settings)

    # Calculate values using calculations module
    actual_hours_value = calculations.actual_hours(entry)
    target_hours_value = calculations.target_hours(entry, settings)
    balance_value = calculations.balance(entry, settings)

    # Check if date is a holiday
    is_holiday_date, holiday_name = is_holiday(entry.work_date, return_name=True)

    return {
        "entry": entry,
        "actual_hours": actual_hours_value,
        "target_hours": target_hours_value,
        "balance": balance_value,
        "is_holiday": is_holiday_date,
        "holiday_name": holiday_name,
    }


@router.get("", response_class=HTMLResponse)
async def list_time_entries(
    request: Request,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None, ge=2020, le=2100),
) -> HTMLResponse:
    """List time entries with month/year filtering.

    If month/year not provided, redirects to current month.

    Args:
        request: FastAPI request object
        db: Database session
        user_id: Current user ID from auth
        month: Month filter (1-12), defaults to current month
        year: Year filter (2020-2100), defaults to current year

    Returns:
        HTML response with browser view of time entries, or redirect
    """
    # Redirect to current month if no month/year specified
    if month is None or year is None:
        from fastapi.responses import RedirectResponse

        today = date.today()
        return RedirectResponse(url=f"/time-entries?month={today.month}&year={today.year}", status_code=302)

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

    # Get user settings for calculations
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if not settings:
        settings = UserSettings(user_id=user_id, weekly_target_hours=Decimal("40.00"))
        db.add(settings)
        db.commit()
        db.refresh(settings)

    # Pre-compute calculated values for each entry
    entries_with_calculations = []
    for entry in entries:
        # Check if date is a holiday
        is_holiday_date, holiday_name = is_holiday(entry.work_date, return_name=True)

        entries_with_calculations.append(
            {
                "entry": entry,
                "actual_hours": calculations.actual_hours(entry),
                "target_hours": calculations.target_hours(entry, settings),
                "balance": calculations.balance(entry, settings),
                "is_holiday": is_holiday_date,
                "holiday_name": holiday_name,
            }
        )

    # Calculate weekly summary for current week
    today = date.today()
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=6)

    # Get all entries for current week
    week_entries = (
        db.query(TimeEntry)
        .filter(
            TimeEntry.user_id == user_id,
            TimeEntry.work_date >= week_start,
            TimeEntry.work_date <= week_end,
        )
        .all()
    )

    service = TimeCalculationService()
    weekly_summary = service.weekly_summary(week_entries, settings, week_start)

    # Build context dictionary
    context = {
        "entries": entries_with_calculations,
        "weekly_summary": weekly_summary,
    }

    # Add monthly view context if month/year are specified
    if month is not None and year is not None:
        # Get or create UserSettings
        settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        if not settings:
            # Create default settings if not found (MVP: user_id=1)
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
        parsed_start_time = parse_time_string(start_time, "Startzeit")
        parsed_end_time = parse_time_string(end_time, "Endzeit")

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

        # Get calculated values
        entry_context = get_entry_context(entry, db, user_id)

        # Render row partial for inline editing
        html = render_template(
            request,
            "partials/_row_time_entry.html",
            entry=entry_context["entry"],
            actual_hours=entry_context["actual_hours"],
            target_hours=entry_context["target_hours"],
            balance=entry_context["balance"],
            is_holiday=entry_context["is_holiday"],
            holiday_name=entry_context["holiday_name"],
            loop={"index": 0},  # Provide mock loop context for standalone row
        )
        response = HTMLResponse(content=html, status_code=201)
        response.headers["HX-Trigger"] = "timeEntryCreated"
        return response

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.get("/last")
async def get_last_entry_times(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> dict:
    """Get most recent time entry's times for copy-last-entry feature.

    Returns only time-related fields (start_time, end_time, break_minutes)
    from the entry with the most recent work_date.

    Args:
        db: Database session
        user_id: Current user ID from auth

    Returns:
        JSON dict with start_time, end_time, break_minutes (times formatted as HH:MM strings)

    Raises:
        HTTPException: 404 if no entries exist for user
    """
    # Get most recent entry by work_date
    last_entry = db.query(TimeEntry).filter(TimeEntry.user_id == user_id).order_by(TimeEntry.work_date.desc()).first()

    if not last_entry:
        raise HTTPException(status_code=404, detail="Keine Einträge gefunden")

    # Return only time fields, formatted for form inputs
    return {
        "start_time": last_entry.start_time.strftime("%H:%M") if last_entry.start_time else None,
        "end_time": last_entry.end_time.strftime("%H:%M") if last_entry.end_time else None,
        "break_minutes": last_entry.break_minutes,
    }


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

    # Check if date is a holiday
    is_holiday_date, holiday_name = is_holiday(entry.work_date, return_name=True)

    # Provide mock loop object for standalone rendering
    html = render_template(
        request,
        "partials/_row_time_entry_edit.html",
        entry=entry,
        is_holiday=is_holiday_date,
        holiday_name=holiday_name,
        loop={"index": 0},
    )
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

    # Get calculated values
    entry_context = get_entry_context(entry, db, user_id)

    # Provide mock loop object for standalone rendering
    html = render_template(
        request,
        "partials/_row_time_entry.html",
        entry=entry_context["entry"],
        actual_hours=entry_context["actual_hours"],
        target_hours=entry_context["target_hours"],
        balance=entry_context["balance"],
        is_holiday=entry_context["is_holiday"],
        holiday_name=entry_context["holiday_name"],
        loop={"index": 0},
    )
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
        parsed_start_time = entry.start_time
        parsed_end_time = entry.end_time

        if start_time is not None:
            parsed_start_time = parse_time_string(start_time, "Startzeit")

        if end_time is not None:
            parsed_end_time = parse_time_string(end_time, "Endzeit")

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

        # Get calculated values
        entry_context = get_entry_context(entry, db, user_id)

        # Render updated row partial for inline editing
        html = render_template(
            request,
            "partials/_row_time_entry.html",
            entry=entry_context["entry"],
            actual_hours=entry_context["actual_hours"],
            target_hours=entry_context["target_hours"],
            balance=entry_context["balance"],
            is_holiday=entry_context["is_holiday"],
            holiday_name=entry_context["holiday_name"],
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


@router.get("/summary/week")
async def get_weekly_summary(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    date_param: date | None = Query(None, alias="date"),
) -> dict:
    """Get weekly summary for current week or specified date's week.

    Returns total_actual, total_target, and total_balance for the week (Monday-Sunday).

    Args:
        db: Database session
        user_id: Current user ID from auth
        date_param: Optional date to calculate week for (defaults to today)

    Returns:
        JSON dict with total_actual, total_target, total_balance (all as Decimal)
    """
    # Get user settings
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if not settings:
        settings = UserSettings(user_id=user_id, weekly_target_hours=Decimal("40.00"))
        db.add(settings)
        db.commit()
        db.refresh(settings)

    # Determine the week to calculate
    target_date = date_param if date_param else date.today()

    # Find Monday of the week containing target_date (ISO week: Monday=0)
    days_since_monday = target_date.weekday()
    week_start = target_date - timedelta(days=days_since_monday)

    # Calculate week end (Sunday)
    week_end = week_start + timedelta(days=6)

    # Get all entries for this week
    entries = (
        db.query(TimeEntry)
        .filter(
            TimeEntry.user_id == user_id,
            TimeEntry.work_date >= week_start,
            TimeEntry.work_date <= week_end,
        )
        .all()
    )

    # Calculate weekly summary
    service = TimeCalculationService()
    weekly_summary = service.weekly_summary(entries, settings, week_start)

    return {
        "total_actual": float(weekly_summary.total_actual),
        "total_target": float(weekly_summary.total_target),
        "total_balance": float(weekly_summary.total_balance),
    }
