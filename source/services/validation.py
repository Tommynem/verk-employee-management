"""Validation rules for time entries.

This module provides validation functions for time entry data
with German error messages for user-facing validation.
"""

from datetime import date, datetime
from typing import Any

from source.database.models import TimeEntry

# German error messages for user-facing validation
VALIDATION_ERRORS = {
    "end_before_start": "Endzeit muss nach Startzeit liegen",
    "break_exceeds_duration": "Pausenzeit überschreitet Arbeitszeit",
    "duplicate_entry": "Für diesen Tag existiert bereits ein Eintrag",
    "future_date": "Datum darf nicht in der Zukunft liegen",
    "submitted_readonly": "Abgeschlossene Einträge können nicht bearbeitet werden",
    "missing_end_time": "Endzeit fehlt",
    "missing_start_time": "Startzeit fehlt",
}


def validate_time_entry(
    entry_data: dict[str, Any],
    existing_entries: list[TimeEntry],
    allow_future: bool = False,
) -> list[str]:
    """Validate time entry data before creation/update.

    Args:
        entry_data: Dictionary with time entry fields:
            - user_id: int
            - work_date: date
            - start_time: time | None
            - end_time: time | None
            - break_minutes: int
        existing_entries: List of existing TimeEntry for duplicate check
        allow_future: Whether to allow future dates (default False)

    Returns:
        List of German error messages. Empty list if valid.
    """
    errors: list[str] = []

    start_time = entry_data.get("start_time")
    end_time = entry_data.get("end_time")
    break_minutes = entry_data.get("break_minutes", 0)
    work_date = entry_data.get("work_date")
    user_id = entry_data.get("user_id")

    # Check for missing start/end time (one without the other)
    if start_time is not None and end_time is None:
        errors.append(VALIDATION_ERRORS["missing_end_time"])

    if end_time is not None and start_time is None:
        errors.append(VALIDATION_ERRORS["missing_start_time"])

    # Check end time is after start time
    if start_time is not None and end_time is not None:
        if end_time <= start_time:
            errors.append(VALIDATION_ERRORS["end_before_start"])
        else:
            # Check break doesn't exceed duration
            # Calculate duration in minutes
            today = date.today()
            start_dt = datetime.combine(today, start_time)
            end_dt = datetime.combine(today, end_time)
            duration_minutes = (end_dt - start_dt).total_seconds() / 60

            if break_minutes > duration_minutes:
                errors.append(VALIDATION_ERRORS["break_exceeds_duration"])

    # Check for duplicate entry (same user, same date)
    if work_date is not None and user_id is not None:
        for existing in existing_entries:
            if existing.user_id == user_id and existing.work_date == work_date:
                errors.append(VALIDATION_ERRORS["duplicate_entry"])
                break

    # Check for future date
    if work_date is not None and not allow_future:
        if work_date > date.today():
            errors.append(VALIDATION_ERRORS["future_date"])

    return errors


__all__ = [
    "VALIDATION_ERRORS",
    "validate_time_entry",
]
