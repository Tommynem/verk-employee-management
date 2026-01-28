"""Calculation functions for time tracking.

This module provides pure functions for calculating hours, targets, and balances
without modifying database models.
"""

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from source.database.enums import AbsenceType
from source.database.models import TimeEntry, UserSettings


def actual_hours(entry: TimeEntry) -> Decimal:
    """Calculate actual hours worked for a time entry.

    Args:
        entry: TimeEntry instance with start_time, end_time, break_minutes

    Returns:
        Decimal hours worked (rounded to 2 decimal places)
        Returns 0.00 if start_time or end_time is None

    Example:
        7:00-15:00 with 30min break = 7.50 hours
    """
    if entry.start_time is None or entry.end_time is None:
        return Decimal("0.00")

    # Calculate duration using datetime.combine
    today = datetime.today().date()
    start_dt = datetime.combine(today, entry.start_time)
    end_dt = datetime.combine(today, entry.end_time)

    # Calculate hours as decimal
    duration_seconds = (end_dt - start_dt).total_seconds()
    duration_hours = Decimal(str(duration_seconds / 3600))

    # Subtract break time (convert minutes to hours)
    break_hours = Decimal(str(entry.break_minutes)) / Decimal("60")
    total_hours = duration_hours - break_hours

    # Round to 2 decimal places
    return total_hours.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def target_hours(entry: TimeEntry, settings: UserSettings) -> Decimal:
    """Calculate target hours for a specific day.

    Args:
        entry: TimeEntry with work_date to determine weekday
        settings: UserSettings with weekly_target_hours

    Returns:
        Decimal target hours for the day (rounded to 2 decimal places)
        Weekdays (Mon-Fri): weekly_target_hours / 5
        Weekends (Sat-Sun): 0.00
        Public holidays (HOLIDAY): 0.00

    Example:
        32h/week on Wednesday = 6.40 hours/day
        Any day on Saturday = 0.00 hours
    """
    # Get weekday (0=Monday, 6=Sunday)
    weekday = entry.work_date.weekday()

    # Weekend check (Saturday=5, Sunday=6)
    if weekday >= 5:
        return Decimal("0.00")

    # Public holidays (Feiertag) are not work days - target = 0
    if entry.absence_type == AbsenceType.HOLIDAY:
        return Decimal("0.00")

    # Calculate daily target (weekly / 5 workdays)
    # Note: SICK gets normal target per German EFZG (credited as worked)
    daily_target = settings.weekly_target_hours / Decimal("5")

    # Round to 2 decimal places
    return daily_target.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def balance(entry: TimeEntry, settings: UserSettings) -> Decimal:
    """Calculate +/- balance for a time entry.

    Args:
        entry: TimeEntry with work_date, start/end times, absence_type
        settings: UserSettings with weekly_target_hours

    Returns:
        Decimal balance (actual - target) rounded to 2 decimal places
        VACATION and SICK: neutral (paid leave/illness counts as target met per EFZG)

    Example:
        Worked 10h with 6.4h target = +3.60
        Worked 4h with 6.4h target = -2.40
        Vacation day = 0.00 (neutral)
    """
    # VACATION and SICK: neutral (paid leave/illness counts as target met per EFZG)
    if entry.absence_type in (AbsenceType.VACATION, AbsenceType.SICK):
        return Decimal("0.00")

    # All other types: actual - target
    # HOLIDAY: target=0, actual=0, so balance=0 (calculated, not hardcoded)
    # FLEX_TIME: target=normal, actual=0, so balance=negative
    # NONE: normal calculation
    actual = actual_hours(entry)
    target = target_hours(entry, settings)

    # Return difference
    balance_value = actual - target

    # Round to 2 decimal places
    return balance_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


__all__ = [
    "actual_hours",
    "target_hours",
    "balance",
]
