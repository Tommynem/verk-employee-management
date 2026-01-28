"""Settings routes for Verk Employee Management.

Routes for user settings including weekday defaults.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from source.api.context import render_template
from source.api.dependencies import get_current_user_id, get_db
from source.core.i18n import GERMAN_DAYS
from source.database.models import UserSettings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> HTMLResponse:
    """Show settings page.

    Args:
        request: FastAPI request object
        db: Database session
        user_id: Current user ID

    Returns:
        HTML response with settings page
    """
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()

    # Detect if this is an HTMX request
    is_htmx = request.headers.get("HX-Request") == "true"

    if is_htmx:
        html = render_template(request, "partials/_settings_weekday_defaults.html", settings=settings)
    else:
        html = render_template(request, "pages/settings.html", settings=settings)

    return HTMLResponse(content=html, status_code=200)


@router.patch("/weekday-defaults", response_class=HTMLResponse)
async def update_weekday_defaults(
    request: Request,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> HTMLResponse:
    """Update weekday defaults settings.

    Args:
        request: FastAPI request object
        db: Database session
        user_id: Current user ID

    Returns:
        HTML response with updated settings partial

    Raises:
        HTTPException: 422 if validation fails
    """
    # Get or create settings
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if not settings:
        from decimal import Decimal

        settings = UserSettings(user_id=user_id, weekly_target_hours=Decimal("40.00"), schedule_json={})
        db.add(settings)

    # Get form data
    form_data = await request.form()

    # Initialize schedule_json if needed
    if not settings.schedule_json:
        settings.schedule_json = {}

    # Ensure weekday_defaults exists
    if "weekday_defaults" not in settings.schedule_json:
        settings.schedule_json["weekday_defaults"] = {}

    weekday_defaults = settings.schedule_json["weekday_defaults"]

    # Validate weekday keys are 0-6
    for key in form_data.keys():
        if key.startswith("weekday_"):
            parts = key.split("_")
            if len(parts) >= 2:
                try:
                    weekday_num = int(parts[1])
                    if weekday_num < 0 or weekday_num > 6:
                        raise HTTPException(status_code=422, detail="Ungültiger Wochentag")
                except ValueError:
                    pass  # Not a weekday field

    # Process form data for each weekday (0-6)
    import re

    time_pattern = re.compile(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")

    for i in range(7):
        enabled_key = f"weekday_{i}_enabled"
        start_key = f"weekday_{i}_start_time"
        end_key = f"weekday_{i}_end_time"
        break_key = f"weekday_{i}_break_minutes"

        # Check if any data was submitted for this weekday
        if start_key in form_data or end_key in form_data or break_key in form_data:
            start_time = form_data.get(start_key, "")
            end_time = form_data.get(end_key, "")
            break_minutes_str = form_data.get(break_key, "30")

            # Validate time format if provided
            if start_time and not time_pattern.match(start_time):
                raise HTTPException(status_code=422, detail=f"Ungültige Startzeit für {GERMAN_DAYS[i]}")
            if end_time and not time_pattern.match(end_time):
                raise HTTPException(status_code=422, detail=f"Ungültige Endzeit für {GERMAN_DAYS[i]}")

            # Validate break minutes
            try:
                break_minutes = int(break_minutes_str) if break_minutes_str else 30
                if break_minutes < 0 or break_minutes > 480:
                    raise HTTPException(status_code=422, detail=f"Ungültige Pausenzeit für {GERMAN_DAYS[i]}")
            except ValueError as e:
                raise HTTPException(status_code=422, detail=f"Ungültige Pausenzeit für {GERMAN_DAYS[i]}") from e

            weekday_defaults[str(i)] = {
                "start_time": start_time,
                "end_time": end_time,
                "break_minutes": break_minutes,
            }
        elif enabled_key in form_data:
            # Only enabled checkbox is present, but with value "false" - set to null
            if form_data.get(enabled_key) == "false":
                weekday_defaults[str(i)] = None

    # Mark the JSON column as modified to trigger SQLAlchemy change detection
    flag_modified(settings, "schedule_json")

    db.commit()
    db.refresh(settings)

    html = render_template(request, "partials/_settings_weekday_defaults.html", settings=settings)
    response = HTMLResponse(content=html, status_code=200)
    response.headers["HX-Trigger"] = "settingsUpdated"
    return response
