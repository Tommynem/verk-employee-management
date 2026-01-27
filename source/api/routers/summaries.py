"""Summary API routes for weekly and monthly time tracking views.

Routes:
- GET /summary/week - Current week summary
- GET /summary/week?week_start=YYYY-MM-DD - Specific week summary
- GET /summary/month - Current month summary
- GET /summary/month?year=YYYY&month=M - Specific month summary
"""

import calendar
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from source.api.context import render_template
from source.api.dependencies import get_current_user_id, get_db
from source.database.models import TimeEntry, UserSettings
from source.services.time_calculation import TimeCalculationService

router = APIRouter(prefix="/summary", tags=["summaries"])


def get_monday_of_week(target_date: date) -> date:
    """Get the Monday of the week containing the target date.

    Args:
        target_date: Any date in the week

    Returns:
        Monday of that week
    """
    days_since_monday = target_date.weekday()
    return target_date - timedelta(days=days_since_monday)


@router.get("/week", response_class=HTMLResponse)
async def get_weekly_summary(
    request: Request,
    week_start: str | None = Query(None, description="Week start date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Get weekly summary view.

    Args:
        request: FastAPI request object
        week_start: Optional week start date (YYYY-MM-DD format)
        db: Database session
        user_id: Current user ID

    Returns:
        HTML response with weekly summary or 422 error
    """
    # Get user settings
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if not settings:
        html = "<p>Keine Benutzereinstellungen gefunden</p>"
        return HTMLResponse(content=html, status_code=422)

    # Parse week_start parameter
    if week_start:
        try:
            week_start_date = date.fromisoformat(week_start)
        except (ValueError, TypeError):
            html = "<p>Ungültiges Datumsformat</p>"
            return HTMLResponse(content=html, status_code=422)
        # Ensure it's a Monday
        week_start_date = get_monday_of_week(week_start_date)
    else:
        # Default to current week (Monday)
        week_start_date = get_monday_of_week(date.today())

    # Query time entries for this week
    week_end = week_start_date + timedelta(days=6)
    entries = (
        db.query(TimeEntry)
        .filter(TimeEntry.user_id == user_id)
        .filter(TimeEntry.work_date >= week_start_date)
        .filter(TimeEntry.work_date <= week_end)
        .order_by(TimeEntry.work_date)
        .all()
    )

    # Generate summary using service
    service = TimeCalculationService()
    summary = service.weekly_summary(entries, settings, week_start_date)

    # Render template
    html = render_template(request, "partials/_summary_week.html", summary=summary)
    return HTMLResponse(content=html, status_code=200)


@router.get("/month", response_class=HTMLResponse)
async def get_monthly_summary(
    request: Request,
    year: int | None = Query(None, description="Year (YYYY)"),
    month: int | None = Query(None, description="Month (1-12)"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Get monthly summary view.

    Args:
        request: FastAPI request object
        year: Optional year (YYYY)
        month: Optional month (1-12)
        db: Database session
        user_id: Current user ID

    Returns:
        HTML response with monthly summary or 422 error
    """
    # Get user settings
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if not settings:
        html = "<p>Keine Benutzereinstellungen gefunden</p>"
        return HTMLResponse(content=html, status_code=422)

    # Parse year/month parameters
    if year is not None and month is not None:
        # Validate month
        if not (1 <= month <= 12):
            html = "<p>Ungültiger Monat</p>"
            return HTMLResponse(content=html, status_code=422)
        target_year = year
        target_month = month
    elif year is not None or month is not None:
        # Both must be provided or neither
        html = "<p>Jahr und Monat müssen zusammen angegeben werden</p>"
        return HTMLResponse(content=html, status_code=422)
    else:
        # Default to current month
        today = date.today()
        target_year = today.year
        target_month = today.month

    # Validate date (will raise ValueError for invalid dates)
    try:
        first_day = date(target_year, target_month, 1)
        last_day = date(target_year, target_month, calendar.monthrange(target_year, target_month)[1])
    except (ValueError, TypeError):
        html = "<p>Ungültiges Datum</p>"
        return HTMLResponse(content=html, status_code=422)

    # Query time entries for this month
    entries = (
        db.query(TimeEntry)
        .filter(TimeEntry.user_id == user_id)
        .filter(TimeEntry.work_date >= first_day)
        .filter(TimeEntry.work_date <= last_day)
        .order_by(TimeEntry.work_date)
        .all()
    )

    # Generate summary using service
    service = TimeCalculationService()
    summary = service.monthly_summary(entries, settings, target_year, target_month)

    # Render template
    html = render_template(request, "partials/_summary_month.html", summary=summary)
    return HTMLResponse(content=html, status_code=200)
