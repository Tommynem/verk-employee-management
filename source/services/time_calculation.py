"""Time calculation service for time tracking.

This module provides the TimeCalculationService class that wraps
calculation functions and provides period summary capabilities.
"""

import calendar
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from source.database.calculations import actual_hours as calc_actual_hours
from source.database.calculations import balance as calc_balance
from source.database.calculations import target_hours as calc_target_hours
from source.database.enums import AbsenceType
from source.database.models import TimeEntry, UserSettings
from source.services.summaries import DaySummary, MonthlySummary, WeeklySummary


class TimeCalculationService:
    """Service for time tracking calculations.

    Wraps standalone calculation functions and provides additional
    period summary capabilities.
    """

    def actual_hours(self, entry: TimeEntry) -> Decimal:
        """Calculate actual hours worked for a single entry.

        Args:
            entry: TimeEntry instance

        Returns:
            Decimal hours worked (rounded to 2 decimal places)
        """
        return calc_actual_hours(entry)

    def target_hours(self, entry: TimeEntry, settings: UserSettings) -> Decimal:
        """Calculate target hours for a day based on user settings.

        Args:
            entry: TimeEntry with work_date
            settings: UserSettings with weekly_target_hours

        Returns:
            Decimal target hours for the day
        """
        return calc_target_hours(entry, settings)

    def daily_balance(self, entry: TimeEntry, settings: UserSettings) -> Decimal:
        """Calculate +/- balance for a single day.

        Args:
            entry: TimeEntry instance
            settings: UserSettings instance

        Returns:
            Decimal balance (actual - target)
        """
        return calc_balance(entry, settings)

    def all_time_balance(
        self,
        entries: list[TimeEntry],
        settings: UserSettings,
        target_date: date | None = None,
    ) -> Decimal:
        """Calculate all-time balance up to target_date.

        Args:
            entries: List of ALL time entries from tracking start
            settings: UserSettings with tracking_start_date and initial_hours_offset
            target_date: Optional cutoff date (inclusive). If None, includes all entries.

        Returns:
            sum(daily_balances for entries up to target_date) + initial_hours_offset
        """
        # Start with all entries
        filtered = entries

        # Filter by tracking_start_date if set
        if settings.tracking_start_date is not None:
            filtered = [e for e in filtered if e.work_date >= settings.tracking_start_date]

        # Filter by target_date if provided
        if target_date is not None:
            filtered = [e for e in filtered if e.work_date <= target_date]

        # Sum daily balances
        total = sum((self.daily_balance(e, settings) for e in filtered), start=Decimal("0.00"))

        # Add initial_hours_offset if present
        if settings.initial_hours_offset is not None:
            total += settings.initial_hours_offset

        # Return rounded
        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def period_balance(
        self,
        entries: list[TimeEntry],
        settings: UserSettings,
        include_carryover: bool = True,
        respect_tracking_start: bool = True,
    ) -> Decimal:
        """Calculate cumulative balance for a period (week/month).

        Args:
            entries: List of TimeEntry instances for the period
            settings: UserSettings with weekly_target_hours,
                      tracking_start_date, and initial_hours_offset
            include_carryover: Whether to include carryover from previous period
            respect_tracking_start: Whether to filter entries before tracking_start_date

        Returns:
            Decimal cumulative balance, optionally including carryover and initial offset
        """
        # Filter entries by tracking start date if specified
        filtered_entries = entries
        if respect_tracking_start and settings.tracking_start_date is not None:
            filtered_entries = [e for e in entries if e.work_date >= settings.tracking_start_date]

        # Sum daily balances
        total_balance = sum((self.daily_balance(entry, settings) for entry in filtered_entries), start=Decimal("0.00"))

        # Add initial hours offset if requested and available
        if include_carryover:
            if settings.initial_hours_offset is not None:
                total_balance += settings.initial_hours_offset

        return total_balance.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def weekly_summary(self, entries: list[TimeEntry], settings: UserSettings, week_start: date) -> WeeklySummary:
        """Generate weekly summary with totals.

        Args:
            entries: List of TimeEntry instances for the week
            settings: UserSettings with weekly_target_hours
            week_start: First day of the week (Monday)

        Returns:
            WeeklySummary with day-by-day breakdown and totals
        """
        week_end = week_start + timedelta(days=6)

        # Create a map of date -> entry for quick lookup
        entry_map = {entry.work_date: entry for entry in entries}

        days: list[DaySummary] = []
        total_actual = Decimal("0.00")
        total_target = Decimal("0.00")
        total_balance = Decimal("0.00")

        # Iterate through each day of the week
        for i in range(7):
            current_date = week_start + timedelta(days=i)
            entry = entry_map.get(current_date)

            if entry:
                actual = self.actual_hours(entry)
                target = self.target_hours(entry, settings)
                day_balance = self.daily_balance(entry, settings)
                absence_type = entry.absence_type
                has_entry = True
            else:
                # No entry - create a dummy entry just to get target hours
                actual = Decimal("0.00")
                # Calculate target based on weekday
                weekday = current_date.weekday()
                if weekday < 5:  # Mon-Fri
                    target = (settings.weekly_target_hours / Decimal("5")).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                else:
                    target = Decimal("0.00")
                day_balance = actual - target
                absence_type = AbsenceType.NONE
                has_entry = False

            day_summary = DaySummary(
                date=current_date,
                actual_hours=actual,
                target_hours=target,
                balance=day_balance,
                absence_type=absence_type,
                has_entry=has_entry,
            )
            days.append(day_summary)

            total_actual += actual
            total_target += target
            total_balance += day_balance

        return WeeklySummary(
            week_start=week_start,
            week_end=week_end,
            days=days,
            total_actual=total_actual.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            total_target=total_target.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            total_balance=total_balance.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        )

    def monthly_summary(
        self, entries: list[TimeEntry], settings: UserSettings, year: int, month: int
    ) -> MonthlySummary:
        """Generate monthly summary with totals and carryover.

        Args:
            entries: List of TimeEntry instances for the month
            settings: UserSettings with weekly_target_hours
            year: Year of the month
            month: Month number (1-12)

        Returns:
            MonthlySummary with weekly breakdown, totals, and carryover
        """
        # Get first and last day of the month
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])

        # Find the Monday of the week containing the first day
        days_since_monday = first_day.weekday()
        week_start = first_day - timedelta(days=days_since_monday)

        weeks: list[WeeklySummary] = []
        total_actual = Decimal("0.00")
        total_target = Decimal("0.00")
        period_balance = Decimal("0.00")

        # Generate weekly summaries
        while week_start <= last_day:
            # Filter entries for this week
            week_end = week_start + timedelta(days=6)
            week_entries = [entry for entry in entries if week_start <= entry.work_date <= week_end]

            weekly = self.weekly_summary(week_entries, settings, week_start)
            weeks.append(weekly)

            # Only count totals for days within this month
            for day in weekly.days:
                if first_day <= day.date <= last_day:
                    total_actual += day.actual_hours
                    total_target += day.target_hours
                    period_balance += day.balance

            week_start += timedelta(days=7)

        # Calculate carryover_in from historical data
        carryover_in = Decimal("0.00")

        if settings.tracking_start_date is not None:
            if first_day <= settings.tracking_start_date <= last_day:
                # First tracked month: use initial_hours_offset only (no historical balance yet)
                carryover_in = settings.initial_hours_offset or Decimal("0.00")
            elif settings.tracking_start_date < first_day:
                # Subsequent months: calculate from historical data
                prev_month_end = first_day - timedelta(days=1)
                carryover_in = self.all_time_balance(entries, settings, prev_month_end)
        # else: tracking_start_date is None, carryover_in stays at 0.00

        carryover_out = carryover_in + period_balance

        return MonthlySummary(
            year=year,
            month=month,
            weeks=weeks,
            total_actual=total_actual.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            total_target=total_target.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            period_balance=period_balance.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            carryover_in=carryover_in.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            carryover_out=carryover_out.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        )


__all__ = [
    "TimeCalculationService",
]
