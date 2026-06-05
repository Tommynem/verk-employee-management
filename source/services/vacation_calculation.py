"""Vacation calculation service for time tracking.

This module provides the VacationCalculationService class that calculates
vacation day balances following German law (Bundesurlaubsgesetz).
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from source.database.calculations import is_non_working_day_for_settings
from source.database.enums import AbsenceType
from source.database.models import TimeEntry, UserSettings


@dataclass
class VacationBalance:
    """Vacation balance summary."""

    total_entitlement: Decimal
    days_used: Decimal
    days_remaining: Decimal
    carryover_days: Decimal
    carryover_expires: date | None


@dataclass
class VacationWarning:
    """Warning about expiring vacation days."""

    severity: str  # 'info' | 'warning' | 'critical'
    message: str
    days_expiring: Decimal
    expiry_date: date


class VacationCalculationService:
    """Service for vacation tracking calculations.

    Provides methods for counting vacation days, calculating balances,
    and generating expiry warnings.
    """

    def _vacation_days_for_entry(self, entry: TimeEntry) -> Decimal:
        """Return the vacation day amount, defaulting legacy rows to one day."""
        if entry.vacation_days is None:
            return Decimal("1.00")
        return Decimal(str(entry.vacation_days))

    def count_vacation_days(
        self,
        entries: list[TimeEntry],
        start: date,
        end: date,
        settings: UserSettings | None = None,
    ) -> Decimal:
        """Count weekday vacation days in date range.

        Args:
            entries: List of TimeEntry instances
            start: Start date (inclusive)
            end: End date (inclusive)
            settings: Optional UserSettings for holiday/company closure policy

        Returns:
            Decimal number of vacation days in range
        """
        count = Decimal("0")
        for entry in entries:
            if (
                entry.absence_type == AbsenceType.VACATION
                and start <= entry.work_date <= end
                and entry.work_date.weekday() < 5
                and not is_non_working_day_for_settings(entry.work_date, settings)
            ):
                count += self._vacation_days_for_entry(entry)
        return count

    def _balance_period_start(self, settings: UserSettings, as_of: date) -> date | None:
        """Return the first date whose vacation usage applies to the current balance."""
        tracking_start = settings.tracking_start_date
        if tracking_start is not None:
            if as_of < tracking_start:
                return None
            if as_of.year == tracking_start.year:
                return tracking_start

        return date(as_of.year, 1, 1)

    def _base_entitlement(self, settings: UserSettings, as_of: date) -> Decimal:
        """Return the non-carryover entitlement for the balance period."""
        initial_days = settings.initial_vacation_days or Decimal("0")
        annual_days = settings.annual_vacation_days or Decimal("0")
        tracking_start = settings.tracking_start_date

        if tracking_start is None:
            return initial_days if settings.initial_vacation_days is not None else annual_days

        if as_of < tracking_start:
            return Decimal("0")

        if as_of.year == tracking_start.year:
            return initial_days

        return annual_days

    def calculate_balance(self, entries: list[TimeEntry], settings: UserSettings, as_of: date) -> VacationBalance:
        """Calculate vacation balance as of a given date.

        Args:
            entries: List of TimeEntry instances
            settings: UserSettings with vacation configuration
            as_of: Date to calculate balance as of

        Returns:
            VacationBalance with current entitlement and usage
        """
        # Handle None settings fields
        carryover_days = settings.vacation_carryover_days or Decimal("0")
        carryover_expires = settings.vacation_carryover_expires

        # Determine valid carryover
        valid_carryover = Decimal("0")
        if carryover_expires is not None:
            if as_of <= carryover_expires:
                valid_carryover = carryover_days
        else:
            valid_carryover = carryover_days

        # Total entitlement for the current vacation year. The opening balance is
        # a one-time balance for the first tracked year; later years use the
        # regular annual entitlement unless explicit carryover is configured.
        base_entitlement = self._base_entitlement(settings, as_of)
        total_entitlement = base_entitlement + valid_carryover

        # Count days used
        balance_period_start = self._balance_period_start(settings, as_of)
        if balance_period_start is None:
            days_used = Decimal("0")
        else:
            days_used = self.count_vacation_days(entries, balance_period_start, as_of, settings)

        remaining_carryover = valid_carryover
        if valid_carryover > 0 and balance_period_start is not None:
            remaining_carryover = max(valid_carryover - days_used, Decimal("0"))

        # Days remaining
        days_remaining = total_entitlement - days_used
        if carryover_expires is not None and as_of > carryover_expires and balance_period_start is not None:
            used_through_expiry = self.count_vacation_days(
                entries,
                balance_period_start,
                carryover_expires,
                settings,
            )
            used_after_expiry = self.count_vacation_days(
                entries,
                max(balance_period_start, carryover_expires + timedelta(days=1)),
                as_of,
                settings,
            )
            base_days_used = max(used_through_expiry - carryover_days, Decimal("0")) + used_after_expiry
            days_remaining = base_entitlement - base_days_used

        return VacationBalance(
            total_entitlement=total_entitlement,
            days_used=days_used,
            days_remaining=days_remaining,
            carryover_days=remaining_carryover,
            carryover_expires=carryover_expires,
        )

    def get_expiry_warning(self, balance: VacationBalance, as_of: date) -> VacationWarning | None:
        """Get expiry warning if carryover days are about to expire.

        Args:
            balance: VacationBalance with carryover information
            as_of: Current date

        Returns:
            VacationWarning if carryover is expiring soon, None otherwise
        """
        # No warning if no carryover days
        if balance.carryover_days == Decimal("0"):
            return None

        # No warning if no expiry date
        if balance.carryover_expires is None:
            return None

        # No warning if already expired
        if as_of > balance.carryover_expires:
            return None

        # Calculate days until expiry
        days_until_expiry = (balance.carryover_expires - as_of).days

        # No warning if more than 30 days
        if days_until_expiry > 30:
            return None

        # Determine severity based on days until expiry
        if days_until_expiry < 7:
            severity = "critical"
        elif days_until_expiry <= 14:
            severity = "warning"
        else:  # 15-30 days
            severity = "info"

        # Format message in German
        message = f"{balance.carryover_days} Urlaubstage verfallen am {balance.carryover_expires}"

        return VacationWarning(
            severity=severity,
            message=message,
            days_expiring=balance.carryover_days,
            expiry_date=balance.carryover_expires,
        )


__all__ = [
    "VacationBalance",
    "VacationWarning",
    "VacationCalculationService",
]
