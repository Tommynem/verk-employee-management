"""Vacation calculation service for time tracking.

This module provides the VacationCalculationService class that calculates
vacation day balances following German law (Bundesurlaubsgesetz).
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta

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

    def count_vacation_days(self, entries: list[TimeEntry], start: date, end: date) -> Decimal:
        """Count vacation days in date range.

        Args:
            entries: List of TimeEntry instances
            start: Start date (inclusive)
            end: End date (inclusive)

        Returns:
            Decimal number of vacation days in range
        """
        count = Decimal("0")
        for entry in entries:
            if entry.absence_type == AbsenceType.VACATION and start <= entry.work_date <= end:
                count += Decimal("1")
        return count

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
        initial_days = settings.initial_vacation_days or Decimal("0")
        annual_days = settings.annual_vacation_days or Decimal("0")
        carryover_days = settings.vacation_carryover_days or Decimal("0")
        carryover_expires = settings.vacation_carryover_expires

        # Determine valid carryover
        valid_carryover = Decimal("0")
        if carryover_expires is not None:
            if as_of <= carryover_expires:
                valid_carryover = carryover_days
        else:
            valid_carryover = carryover_days

        # Calculate annual entitlement based on full years tracked
        annual_entitlement = Decimal("0")
        if settings.tracking_start_date is not None and annual_days > 0:
            # Calculate number of full years between tracking_start_date and as_of
            years_diff = relativedelta(as_of, settings.tracking_start_date).years
            if years_diff > 0:
                annual_entitlement = annual_days * Decimal(str(years_diff))

        # Total entitlement
        total_entitlement = initial_days + valid_carryover + annual_entitlement

        # Count days used
        if settings.tracking_start_date is not None:
            days_used = self.count_vacation_days(entries, settings.tracking_start_date, as_of)
        else:
            # No tracking start date, count all vacation entries up to as_of
            if entries:
                earliest_date = min(e.work_date for e in entries)
                days_used = self.count_vacation_days(entries, earliest_date, as_of)
            else:
                days_used = Decimal("0")

        # Days remaining
        days_remaining = total_entitlement - days_used

        return VacationBalance(
            total_entitlement=total_entitlement,
            days_used=days_used,
            days_remaining=days_remaining,
            carryover_days=valid_carryover,
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
