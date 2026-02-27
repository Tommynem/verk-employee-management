"""Settings routes for Verk Employee Management.

Routes for user settings including weekday defaults.
"""

from datetime import date
from decimal import Decimal, InvalidOperation

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
    """Update weekday defaults settings with optimistic locking.

    Args:
        request: FastAPI request object
        db: Database session
        user_id: Current user ID

    Returns:
        HTML response with updated settings partial

    Raises:
        HTTPException: 409 if stale timestamp, 422 if validation fails
    """
    # Get form data
    form_data = await request.form()

    # Get or create settings
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if not settings:
        from decimal import Decimal

        settings = UserSettings(user_id=user_id, weekly_target_hours=Decimal("40.00"), schedule_json={})
        db.add(settings)
        # For new settings, skip optimistic locking check
    else:
        # Optimistic locking: Require updated_at timestamp for existing settings
        updated_at_str = form_data.get("updated_at")
        if updated_at_str is None:
            raise HTTPException(
                status_code=422, detail="Zeitstempel (updated_at) ist erforderlich für die Aktualisierung"
            )

        # Parse updated_at timestamp
        from datetime import datetime

        try:
            sent_updated_at = datetime.fromisoformat(str(updated_at_str))
        except (ValueError, TypeError) as e:
            raise HTTPException(status_code=422, detail="Ungültiger Zeitstempel") from e

        # Check for concurrent modification (optimistic locking)
        if settings.updated_at != sent_updated_at:
            raise HTTPException(
                status_code=409,
                detail="Einstellungen wurden zwischenzeitlich geändert. Bitte laden Sie die Seite neu.",
            )

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

            # Validate end_time is after start_time for enabled work days
            if start_time and end_time:
                # Convert HH:MM to comparable format (minutes since midnight)
                start_parts = start_time.split(":")
                end_parts = end_time.split(":")
                start_minutes = int(start_parts[0]) * 60 + int(start_parts[1])
                end_minutes = int(end_parts[0]) * 60 + int(end_parts[1])

                if end_minutes <= start_minutes:
                    raise HTTPException(
                        status_code=422, detail=f"Endzeit muss nach der Startzeit liegen für {GERMAN_DAYS[i]}"
                    )

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


@router.patch("/tracking", response_class=HTMLResponse)
async def update_tracking_settings(
    request: Request,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> HTMLResponse:
    """Update tracking settings including weekly target hours with optimistic locking.

    Handles weekly_target_hours, tracking_start_date, and initial_hours_offset.
    Supports German number format (comma as decimal separator) for numeric fields.
    Supports German date format (DD.MM.YYYY) with fallback to ISO format.

    Args:
        request: FastAPI request object
        db: Database session
        user_id: Current user ID

    Returns:
        HTML response with tracking settings form partial

    Raises:
        HTTPException: 409 if stale timestamp, 422 if validation fails
    """
    # Get form data
    form_data = await request.form()

    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()

    # Get or create settings
    if not settings:
        settings = UserSettings(user_id=user_id, weekly_target_hours=Decimal("40.00"))
        db.add(settings)
        # For new settings, skip optimistic locking check
    else:
        # Optimistic locking: Require updated_at timestamp for existing settings
        updated_at_str = form_data.get("updated_at")
        if updated_at_str is None:
            raise HTTPException(
                status_code=422, detail="Zeitstempel (updated_at) ist erforderlich für die Aktualisierung"
            )

        # Parse updated_at timestamp
        from datetime import datetime

        try:
            sent_updated_at = datetime.fromisoformat(str(updated_at_str))
        except (ValueError, TypeError) as e:
            raise HTTPException(status_code=422, detail="Ungültiger Zeitstempel") from e

        # Check for concurrent modification (optimistic locking)
        if settings.updated_at != sent_updated_at:
            raise HTTPException(
                status_code=409,
                detail="Einstellungen wurden zwischenzeitlich geändert. Bitte laden Sie die Seite neu.",
            )

    # Parse weekly_target_hours (German format: comma as decimal separator)
    weekly_hours_str = form_data.get("weekly_target_hours", "")
    if weekly_hours_str:
        try:
            # Convert German decimal format (comma) to standard (dot)
            weekly_hours_str = str(weekly_hours_str).replace(",", ".")
            weekly_hours = Decimal(weekly_hours_str)
            if weekly_hours < Decimal("0") or weekly_hours > Decimal("80"):
                raise HTTPException(status_code=422, detail="Wochenstunden müssen zwischen 0 und 80 liegen")
            settings.weekly_target_hours = weekly_hours
        except InvalidOperation as e:
            raise HTTPException(status_code=422, detail="Ungültige Wochenstunden") from e

    # Parse tracking_start_date (German format: DD.MM.YYYY)
    tracking_start_str = form_data.get("tracking_start_date", "")
    if tracking_start_str:
        try:
            # Try German date format DD.MM.YYYY first
            from datetime import datetime

            settings.tracking_start_date = datetime.strptime(str(tracking_start_str), "%d.%m.%Y").date()
        except ValueError:
            # Fallback to ISO format
            try:
                settings.tracking_start_date = date.fromisoformat(str(tracking_start_str))
            except ValueError as e:
                raise HTTPException(status_code=422, detail="Ungültiges Datumsformat") from e
    else:
        settings.tracking_start_date = None

    # Parse initial_hours_offset (HH:MM format, e.g., "24:20" or "-5:30")
    offset_str = form_data.get("initial_hours_offset", "")
    if offset_str:
        offset_str = str(offset_str).strip()
        try:
            # Parse HH:MM format (supports negative values like "-5:30")
            import re

            match = re.match(r"^(-?)(\d+):(\d{2})$", offset_str)
            if match:
                sign = -1 if match.group(1) == "-" else 1
                hours = int(match.group(2))
                minutes = int(match.group(3))
                if minutes >= 60:
                    raise HTTPException(status_code=422, detail="Minuten müssen zwischen 0 und 59 liegen")
                # Convert to decimal hours
                offset = sign * (Decimal(hours) + Decimal(minutes) / Decimal(60))
                offset = offset.quantize(Decimal("0.01"))
            else:
                # Fallback: try German decimal format for backwards compatibility
                offset_str = offset_str.replace(",", ".")
                offset = Decimal(offset_str)

            if offset < Decimal("-999.99") or offset > Decimal("999.99"):
                raise HTTPException(status_code=422, detail="Saldo muss zwischen -999:59 und 999:59 liegen")
            settings.initial_hours_offset = offset
        except InvalidOperation as e:
            raise HTTPException(status_code=422, detail="Ungültiges Format. Bitte HH:MM verwenden (z.B. 24:20)") from e
    else:
        settings.initial_hours_offset = None

    db.commit()
    db.refresh(settings)

    html = render_template(request, "partials/_settings_tracking.html", settings=settings)
    response = HTMLResponse(content=html, status_code=200)
    response.headers["HX-Trigger"] = "settingsUpdated"
    return response


@router.patch("/vacation", response_class=HTMLResponse)
async def update_vacation_settings(
    request: Request,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> HTMLResponse:
    """Update vacation settings with optimistic locking.

    Handles:
    - initial_vacation_days: Decimal (e.g., 15.5)
    - annual_vacation_days: Decimal (e.g., 30.0)
    - vacation_carryover_days: Decimal (e.g., 5.0)
    - vacation_carryover_expires: Date (e.g., 2026-03-31)

    Supports German number format (comma as decimal separator).
    Supports German date format (DD.MM.YYYY) with fallback to ISO.

    Args:
        request: FastAPI request object
        db: Database session
        user_id: Current user ID

    Returns:
        HTML response with vacation settings form partial

    Raises:
        HTTPException: 409 if stale timestamp, 422 if validation fails
    """
    # Get form data
    form_data = await request.form()

    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()

    # Get or create settings
    if not settings:
        settings = UserSettings(user_id=user_id, weekly_target_hours=Decimal("40.00"))
        db.add(settings)
        # For new settings, skip optimistic locking check
    else:
        # Optimistic locking: Require updated_at timestamp for existing settings
        updated_at_str = form_data.get("updated_at")
        if updated_at_str is None:
            raise HTTPException(
                status_code=422, detail="Zeitstempel (updated_at) ist erforderlich für die Aktualisierung"
            )

        # Parse updated_at timestamp
        from datetime import datetime

        try:
            sent_updated_at = datetime.fromisoformat(str(updated_at_str))
        except (ValueError, TypeError) as e:
            raise HTTPException(status_code=422, detail="Ungültiger Zeitstempel") from e

        # Check for concurrent modification (optimistic locking)
        if settings.updated_at != sent_updated_at:
            raise HTTPException(
                status_code=409,
                detail="Einstellungen wurden zwischenzeitlich geändert. Bitte laden Sie die Seite neu.",
            )

    # Parse initial_vacation_days (German format: comma as decimal separator)
    initial_days_str = form_data.get("initial_vacation_days", "")
    if initial_days_str:
        try:
            # Convert German decimal format (comma) to standard (dot)
            initial_days_str = str(initial_days_str).replace(",", ".")
            initial_days = Decimal(initial_days_str)
            if initial_days < Decimal("0"):
                raise HTTPException(status_code=422, detail="Urlaubstage dürfen nicht negativ sein")
            settings.initial_vacation_days = initial_days
        except InvalidOperation as e:
            raise HTTPException(status_code=422, detail="Ungültiger Zahlenwert") from e
    else:
        settings.initial_vacation_days = None

    # Parse annual_vacation_days (German format)
    annual_days_str = form_data.get("annual_vacation_days", "")
    if annual_days_str:
        try:
            # Convert German decimal format
            annual_days_str = str(annual_days_str).replace(",", ".")
            annual_days = Decimal(annual_days_str)
            if annual_days < Decimal("0"):
                raise HTTPException(status_code=422, detail="Urlaubstage dürfen nicht negativ sein")
            settings.annual_vacation_days = annual_days
        except InvalidOperation as e:
            raise HTTPException(status_code=422, detail="Ungültiger Zahlenwert") from e
    else:
        settings.annual_vacation_days = None

    # Parse vacation_carryover_days (German format)
    carryover_days_str = form_data.get("vacation_carryover_days", "")
    if carryover_days_str:
        try:
            # Convert German decimal format
            carryover_days_str = str(carryover_days_str).replace(",", ".")
            carryover_days = Decimal(carryover_days_str)
            if carryover_days < Decimal("0"):
                raise HTTPException(status_code=422, detail="Urlaubstage dürfen nicht negativ sein")
            settings.vacation_carryover_days = carryover_days
        except InvalidOperation as e:
            raise HTTPException(status_code=422, detail="Ungültiger Zahlenwert") from e
    else:
        settings.vacation_carryover_days = None

    # Parse vacation_carryover_expires (German format: DD.MM.YYYY)
    carryover_expires_str = form_data.get("vacation_carryover_expires", "")
    if carryover_expires_str:
        try:
            # Try German date format DD.MM.YYYY first
            from datetime import datetime

            settings.vacation_carryover_expires = datetime.strptime(str(carryover_expires_str), "%d.%m.%Y").date()
        except ValueError:
            # Fallback to ISO format
            try:
                settings.vacation_carryover_expires = date.fromisoformat(str(carryover_expires_str))
            except ValueError as e:
                raise HTTPException(status_code=422, detail="Ungültiges Datumsformat") from e
    else:
        settings.vacation_carryover_expires = None

    db.commit()
    db.refresh(settings)

    html = render_template(request, "partials/_settings_vacation.html", settings=settings)
    response = HTMLResponse(content=html, status_code=200)
    response.headers["HX-Trigger"] = "settingsUpdated"
    return response
