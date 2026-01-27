"""Summary data classes for time tracking reports.

This module provides dataclasses for day, week, and month summaries
used in time calculation reporting.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from source.database.enums import AbsenceType


@dataclass
class DaySummary:
    """Summary of a single day's time tracking.

    Args:
        date: The date being summarized
        actual_hours: Hours actually worked
        target_hours: Expected hours for the day
        balance: Difference between actual and target
        absence_type: Type of absence if applicable
        has_entry: Whether a time entry exists for this day
    """

    date: date
    actual_hours: Decimal
    target_hours: Decimal
    balance: Decimal
    absence_type: AbsenceType
    has_entry: bool


@dataclass
class WeeklySummary:
    """Summary of a week's time tracking.

    Args:
        week_start: First day of the week (Monday)
        week_end: Last day of the week (Sunday)
        days: List of DaySummary for each day
        total_actual: Sum of actual hours for the week
        total_target: Sum of target hours for the week
        total_balance: Sum of daily balances
    """

    week_start: date
    week_end: date
    days: list[DaySummary]
    total_actual: Decimal
    total_target: Decimal
    total_balance: Decimal


@dataclass
class MonthlySummary:
    """Summary of a month's time tracking.

    Args:
        year: Year of the month
        month: Month number (1-12)
        weeks: List of WeeklySummary for weeks in month
        total_actual: Sum of actual hours for the month
        total_target: Sum of target hours for the month
        period_balance: Balance for this period only
        carryover_in: Balance carried in from previous month
        carryover_out: Balance to carry to next month
    """

    year: int
    month: int
    weeks: list[WeeklySummary]
    total_actual: Decimal
    total_target: Decimal
    period_balance: Decimal
    carryover_in: Decimal
    carryover_out: Decimal


__all__ = [
    "DaySummary",
    "WeeklySummary",
    "MonthlySummary",
]
