"""Tests for VacationCalculationService.

This module tests the VacationCalculationService which calculates vacation day
balances following German law (Bundesurlaubsgesetz).

PREREQUISITES:
- UserSettings model needs these additional fields:
  - initial_vacation_days: Decimal | None (starting vacation balance)
  - annual_vacation_days: Decimal | None (days per year)
  - vacation_carryover_days: Decimal | None (carried from previous year)
  - vacation_carryover_expires: date | None (typically March 31)
"""

from datetime import date
from decimal import Decimal

import pytest

from source.database.enums import AbsenceType
from source.services.vacation_calculation import (
    VacationBalance,
    VacationCalculationService,
    VacationWarning,
)
from tests.factories import TimeEntryFactory, UserSettingsFactory, VacationEntryFactory


class TestCountVacationDays:
    """Tests for VacationCalculationService.count_vacation_days method."""

    @pytest.mark.unit
    def test_count_vacation_days_empty_list(self):
        """Empty entry list returns 0 vacation days."""
        service = VacationCalculationService()
        start = date(2026, 1, 1)
        end = date(2026, 1, 31)

        result = service.count_vacation_days([], start, end)

        assert result == Decimal("0")

    @pytest.mark.unit
    def test_count_vacation_days_no_vacation_entries(self):
        """List with only work entries returns 0 vacation days."""
        entries = [
            TimeEntryFactory.build(
                work_date=date(2026, 1, 13),
                absence_type=AbsenceType.NONE,
            ),
            TimeEntryFactory.build(
                work_date=date(2026, 1, 14),
                absence_type=AbsenceType.SICK,
            ),
        ]
        service = VacationCalculationService()
        start = date(2026, 1, 1)
        end = date(2026, 1, 31)

        result = service.count_vacation_days(entries, start, end)

        assert result == Decimal("0")

    @pytest.mark.unit
    def test_count_vacation_days_single_vacation(self):
        """Single vacation entry returns 1 day."""
        entries = [
            VacationEntryFactory.build(work_date=date(2026, 1, 13)),
        ]
        service = VacationCalculationService()
        start = date(2026, 1, 1)
        end = date(2026, 1, 31)

        result = service.count_vacation_days(entries, start, end)

        assert result == Decimal("1")

    @pytest.mark.unit
    def test_count_vacation_days_multiple_vacations(self):
        """Multiple vacation entries return correct count."""
        entries = [
            VacationEntryFactory.build(work_date=date(2026, 1, 13)),
            VacationEntryFactory.build(work_date=date(2026, 1, 14)),
            VacationEntryFactory.build(work_date=date(2026, 1, 15)),
        ]
        service = VacationCalculationService()
        start = date(2026, 1, 1)
        end = date(2026, 1, 31)

        result = service.count_vacation_days(entries, start, end)

        assert result == Decimal("3")

    @pytest.mark.unit
    def test_count_vacation_days_uses_fractional_vacation_days(self):
        """Vacation entries consume their configured decimal vacation_days."""
        entries = [
            VacationEntryFactory.build(work_date=date(2026, 1, 13), vacation_days=Decimal("0.50")),
            VacationEntryFactory.build(work_date=date(2026, 1, 14), vacation_days=Decimal("0.25")),
            VacationEntryFactory.build(work_date=date(2026, 1, 15), vacation_days=None),  # Legacy row
        ]
        service = VacationCalculationService()
        start = date(2026, 1, 1)
        end = date(2026, 1, 31)

        result = service.count_vacation_days(entries, start, end)

        assert result == Decimal("1.75")

    @pytest.mark.unit
    def test_count_vacation_days_respects_date_range(self):
        """Only counts vacation days within date range."""
        entries = [
            VacationEntryFactory.build(work_date=date(2025, 12, 30)),  # Before range
            VacationEntryFactory.build(work_date=date(2026, 1, 13)),  # In range
            VacationEntryFactory.build(work_date=date(2026, 1, 14)),  # In range
            VacationEntryFactory.build(work_date=date(2026, 2, 1)),  # After range
        ]
        service = VacationCalculationService()
        start = date(2026, 1, 1)
        end = date(2026, 1, 31)

        result = service.count_vacation_days(entries, start, end)

        assert result == Decimal("2")

    @pytest.mark.unit
    def test_count_vacation_days_ignores_other_absence_types(self):
        """Only counts VACATION absence type, not sick/holiday."""
        entries = [
            VacationEntryFactory.build(work_date=date(2026, 1, 13)),
            TimeEntryFactory.build(work_date=date(2026, 1, 14), absence_type=AbsenceType.SICK),
            TimeEntryFactory.build(work_date=date(2026, 1, 15), absence_type=AbsenceType.HOLIDAY),
            TimeEntryFactory.build(work_date=date(2026, 1, 16), absence_type=AbsenceType.FLEX_TIME),
        ]
        service = VacationCalculationService()
        start = date(2026, 1, 1)
        end = date(2026, 1, 31)

        result = service.count_vacation_days(entries, start, end)

        assert result == Decimal("1")

    @pytest.mark.unit
    def test_count_vacation_days_ignores_weekends(self):
        """Weekend vacation entries do not consume vacation days."""
        entries = [
            VacationEntryFactory.build(work_date=date(2026, 1, 16)),  # Friday
            VacationEntryFactory.build(work_date=date(2026, 1, 17)),  # Saturday
            VacationEntryFactory.build(work_date=date(2026, 1, 18)),  # Sunday
        ]
        service = VacationCalculationService()
        start = date(2026, 1, 1)
        end = date(2026, 1, 31)

        result = service.count_vacation_days(entries, start, end)

        assert result == Decimal("1")

    @pytest.mark.unit
    def test_count_vacation_days_ignores_german_public_holidays(self):
        """Vacation entries on known German public holidays do not consume vacation days."""
        entries = [
            VacationEntryFactory.build(work_date=date(2025, 10, 2)),  # Thursday
            VacationEntryFactory.build(work_date=date(2025, 10, 3)),  # German Unity Day
        ]
        service = VacationCalculationService()
        start = date(2025, 10, 1)
        end = date(2025, 10, 31)

        result = service.count_vacation_days(entries, start, end)

        assert result == Decimal("1")

    @pytest.mark.unit
    def test_count_vacation_days_ignores_bundesland_holidays_from_settings(self):
        """Vacation entries on Bundesland holidays do not consume vacation days."""
        entries = [
            VacationEntryFactory.build(work_date=date(2026, 6, 3)),  # Wednesday
            VacationEntryFactory.build(work_date=date(2026, 6, 4)),  # Fronleichnam in NRW
        ]
        settings = UserSettingsFactory.build(holiday_state="NW")
        service = VacationCalculationService()
        start = date(2026, 6, 1)
        end = date(2026, 6, 30)

        result = service.count_vacation_days(entries, start, end, settings)

        assert result == Decimal("1.00")

    @pytest.mark.unit
    def test_count_vacation_days_ignores_non_vacation_company_closures(self):
        """Vacation entries on non-vacation company closures do not consume days."""
        entries = [
            VacationEntryFactory.build(work_date=date(2026, 12, 23)),
            VacationEntryFactory.build(work_date=date(2026, 12, 24)),
        ]
        settings = UserSettingsFactory.build(
            schedule_json={
                "company_closures": {
                    "12-24": {
                        "day": 24,
                        "month": 12,
                        "name": "Heiligabend",
                        "recurring": True,
                        "enabled": True,
                        "counts_as_vacation": False,
                    }
                }
            }
        )
        service = VacationCalculationService()
        start = date(2026, 12, 1)
        end = date(2026, 12, 31)

        result = service.count_vacation_days(entries, start, end, settings)

        assert result == Decimal("1.00")


class TestCalculateBalance:
    """Tests for VacationCalculationService.calculate_balance method."""

    @pytest.mark.unit
    def test_calculate_balance_no_settings_returns_zero(self):
        """No settings provided returns balance with all zeros."""
        entries = [
            VacationEntryFactory.build(work_date=date(2026, 1, 13)),
        ]
        # Note: UserSettings will need vacation fields added
        settings = UserSettingsFactory.build(tracking_start_date=None)
        service = VacationCalculationService()
        as_of = date(2026, 1, 30)

        balance = service.calculate_balance(entries, settings, as_of)

        assert balance.total_entitlement == Decimal("0")
        assert balance.days_used == Decimal("1")
        assert balance.days_remaining == Decimal("-1")
        assert balance.carryover_days == Decimal("0")
        assert balance.carryover_expires is None

    @pytest.mark.unit
    def test_calculate_balance_initial_only(self):
        """Balance with only initial days, no usage."""
        entries = []
        settings = UserSettingsFactory.build(
            initial_vacation_days=Decimal("15.0"),
            annual_vacation_days=Decimal("30.0"),
            vacation_carryover_days=Decimal("0.0"),
            vacation_carryover_expires=None,
            tracking_start_date=date(2026, 1, 1),
        )
        service = VacationCalculationService()
        as_of = date(2026, 1, 30)

        balance = service.calculate_balance(entries, settings, as_of)

        assert balance.total_entitlement == Decimal("15.0")
        assert balance.days_used == Decimal("0")
        assert balance.days_remaining == Decimal("15.0")
        assert balance.carryover_days == Decimal("0.0")
        assert balance.carryover_expires is None

    @pytest.mark.unit
    def test_calculate_balance_with_usage(self):
        """Balance calculation with vacation days used."""
        entries = [
            VacationEntryFactory.build(work_date=date(2026, 1, 13)),
            VacationEntryFactory.build(work_date=date(2026, 1, 14)),
            VacationEntryFactory.build(work_date=date(2026, 1, 15)),
        ]
        settings = UserSettingsFactory.build(
            initial_vacation_days=Decimal("20.0"),
            annual_vacation_days=Decimal("30.0"),
            vacation_carryover_days=Decimal("0.0"),
            vacation_carryover_expires=None,
            tracking_start_date=date(2026, 1, 1),
        )
        service = VacationCalculationService()
        as_of = date(2026, 1, 30)

        balance = service.calculate_balance(entries, settings, as_of)

        assert balance.total_entitlement == Decimal("20.0")
        assert balance.days_used == Decimal("3")
        assert balance.days_remaining == Decimal("17.0")

    @pytest.mark.unit
    def test_calculate_balance_annual_entitlement_adds_per_year(self):
        """Annual entitlement replaces the opening balance in later vacation years."""
        entries = [
            VacationEntryFactory.build(work_date=date(2026, 6, 15)),
        ]
        settings = UserSettingsFactory.build(
            initial_vacation_days=Decimal("10.0"),
            annual_vacation_days=Decimal("30.0"),
            vacation_carryover_days=Decimal("0.0"),
            vacation_carryover_expires=None,
            tracking_start_date=date(2025, 1, 1),  # Started tracking over 1 year ago
        )
        service = VacationCalculationService()
        as_of = date(2026, 6, 30)

        balance = service.calculate_balance(entries, settings, as_of)

        assert balance.total_entitlement == Decimal("30.0")
        assert balance.days_used == Decimal("1")
        assert balance.days_remaining == Decimal("29.0")

    @pytest.mark.unit
    def test_calculate_balance_opening_balance_and_next_year_entitlement(self):
        """A mid-year opening balance is exhausted in year one and annual entitlement starts Jan 1."""
        vacation_dates_2025 = [
            date(2025, 7, 4),
            date(2025, 8, 1),
            date(2025, 9, 5),
            date(2025, 9, 8),
            date(2025, 9, 9),
            date(2025, 10, 1),
            date(2025, 10, 2),
            date(2025, 10, 6),
            date(2025, 10, 7),
            date(2025, 10, 8),
            date(2025, 10, 9),
            date(2025, 10, 10),
            date(2025, 10, 13),
            date(2025, 10, 14),
            date(2025, 11, 7),
            date(2025, 11, 10),
            date(2025, 12, 15),
            date(2025, 12, 29),
            date(2025, 12, 30),
        ]
        entries = [VacationEntryFactory.build(work_date=work_date) for work_date in vacation_dates_2025]
        settings = UserSettingsFactory.build(
            initial_vacation_days=Decimal("19.0"),
            annual_vacation_days=Decimal("30.0"),
            vacation_carryover_days=Decimal("0.0"),
            vacation_carryover_expires=None,
            tracking_start_date=date(2025, 7, 1),
        )
        service = VacationCalculationService()

        opening_balance = service.calculate_balance(entries, settings, date(2025, 7, 1))
        end_of_2025_balance = service.calculate_balance(entries, settings, date(2025, 12, 31))
        start_of_2026_balance = service.calculate_balance(entries, settings, date(2026, 1, 1))

        assert opening_balance.days_remaining == Decimal("19.0")
        assert end_of_2025_balance.days_remaining == Decimal("0.0")
        assert start_of_2026_balance.total_entitlement == Decimal("30.0")
        assert start_of_2026_balance.days_used == Decimal("0")
        assert start_of_2026_balance.days_remaining == Decimal("30.0")

    @pytest.mark.unit
    def test_calculate_balance_does_not_automatically_carry_unused_opening_balance(self):
        """Unused opening balance expires at year boundary unless explicit carryover is configured."""
        entries = [
            VacationEntryFactory.build(work_date=date(2025, 7, 4)),
            VacationEntryFactory.build(work_date=date(2025, 8, 1)),
        ]
        settings = UserSettingsFactory.build(
            initial_vacation_days=Decimal("19.0"),
            annual_vacation_days=Decimal("30.0"),
            vacation_carryover_days=Decimal("0.0"),
            vacation_carryover_expires=None,
            tracking_start_date=date(2025, 7, 1),
        )
        service = VacationCalculationService()

        balance = service.calculate_balance(entries, settings, date(2026, 1, 1))

        assert balance.total_entitlement == Decimal("30.0")
        assert balance.days_used == Decimal("0")
        assert balance.days_remaining == Decimal("30.0")

    @pytest.mark.unit
    def test_carryover_valid_before_march_31(self):
        """Carryover days are valid before March 31."""
        entries = []
        settings = UserSettingsFactory.build(
            initial_vacation_days=Decimal("25.0"),
            annual_vacation_days=Decimal("30.0"),
            vacation_carryover_days=Decimal("5.0"),
            vacation_carryover_expires=date(2026, 3, 31),
            tracking_start_date=date(2026, 1, 1),
        )
        service = VacationCalculationService()
        as_of = date(2026, 2, 15)  # Before March 31

        balance = service.calculate_balance(entries, settings, as_of)

        assert balance.total_entitlement == Decimal("30.0")  # 25 + 5 carryover
        assert balance.carryover_days == Decimal("5.0")
        assert balance.carryover_expires == date(2026, 3, 31)

    @pytest.mark.unit
    def test_carryover_expires_after_march_31(self):
        """Carryover days expire after March 31."""
        entries = []
        settings = UserSettingsFactory.build(
            initial_vacation_days=Decimal("25.0"),
            annual_vacation_days=Decimal("30.0"),
            vacation_carryover_days=Decimal("5.0"),
            vacation_carryover_expires=date(2026, 3, 31),
            tracking_start_date=date(2026, 1, 1),
        )
        service = VacationCalculationService()
        as_of = date(2026, 4, 1)  # After March 31

        balance = service.calculate_balance(entries, settings, as_of)

        # Carryover expired, only initial days remain
        assert balance.total_entitlement == Decimal("25.0")
        assert balance.carryover_days == Decimal("0")
        assert balance.carryover_expires == date(2026, 3, 31)

    @pytest.mark.unit
    def test_used_carryover_does_not_reduce_base_entitlement_after_expiry(self):
        """Vacation taken before carryover expiry consumes carryover before annual entitlement."""
        entries = [
            VacationEntryFactory.build(work_date=date(2026, 1, 5)),
            VacationEntryFactory.build(work_date=date(2026, 1, 6)),
            VacationEntryFactory.build(work_date=date(2026, 1, 7)),
            VacationEntryFactory.build(work_date=date(2026, 1, 8)),
            VacationEntryFactory.build(work_date=date(2026, 1, 9)),
        ]
        settings = UserSettingsFactory.build(
            initial_vacation_days=Decimal("30.0"),
            annual_vacation_days=Decimal("30.0"),
            vacation_carryover_days=Decimal("5.0"),
            vacation_carryover_expires=date(2026, 3, 31),
            tracking_start_date=date(2026, 1, 1),
        )
        service = VacationCalculationService()
        as_of = date(2026, 4, 1)

        balance = service.calculate_balance(entries, settings, as_of)

        assert balance.total_entitlement == Decimal("30.0")
        assert balance.days_used == Decimal("5")
        assert balance.days_remaining == Decimal("30.0")

    @pytest.mark.unit
    def test_carryover_exactly_on_march_31_still_valid(self):
        """Carryover is valid on March 31 exactly (inclusive)."""
        entries = []
        settings = UserSettingsFactory.build(
            initial_vacation_days=Decimal("25.0"),
            annual_vacation_days=Decimal("30.0"),
            vacation_carryover_days=Decimal("5.0"),
            vacation_carryover_expires=date(2026, 3, 31),
            tracking_start_date=date(2026, 1, 1),
        )
        service = VacationCalculationService()
        as_of = date(2026, 3, 31)  # Exactly on expiry date

        balance = service.calculate_balance(entries, settings, as_of)

        assert balance.total_entitlement == Decimal("30.0")  # Carryover still valid
        assert balance.carryover_days == Decimal("5.0")
        assert balance.carryover_expires == date(2026, 3, 31)

    @pytest.mark.unit
    def test_carryover_days_reflect_remaining_expiring_days(self):
        """Returned carryover_days subtracts vacation already allocated to carryover."""
        entries = [
            VacationEntryFactory.build(work_date=date(2026, 1, 5)),
            VacationEntryFactory.build(work_date=date(2026, 1, 6)),
        ]
        settings = UserSettingsFactory.build(
            initial_vacation_days=Decimal("30.0"),
            annual_vacation_days=Decimal("30.0"),
            vacation_carryover_days=Decimal("5.0"),
            vacation_carryover_expires=date(2026, 3, 31),
            tracking_start_date=date(2026, 1, 1),
        )
        service = VacationCalculationService()
        as_of = date(2026, 3, 15)

        balance = service.calculate_balance(entries, settings, as_of)
        warning = service.get_expiry_warning(balance, as_of)

        assert balance.total_entitlement == Decimal("35.0")
        assert balance.days_remaining == Decimal("33.0")
        assert balance.carryover_days == Decimal("3.0")
        assert warning is not None
        assert warning.days_expiring == Decimal("3.0")


class TestGetExpiryWarning:
    """Tests for VacationCalculationService.get_expiry_warning method."""

    @pytest.mark.unit
    def test_no_warning_when_no_carryover(self):
        """No warning when carryover_days is 0."""
        balance = VacationBalance(
            total_entitlement=Decimal("30.0"),
            days_used=Decimal("5.0"),
            days_remaining=Decimal("25.0"),
            carryover_days=Decimal("0"),
            carryover_expires=date(2026, 3, 31),
        )
        service = VacationCalculationService()
        as_of = date(2026, 3, 15)

        warning = service.get_expiry_warning(balance, as_of)

        assert warning is None

    @pytest.mark.unit
    def test_no_warning_when_over_30_days_to_march(self):
        """No warning when more than 30 days until March 31."""
        balance = VacationBalance(
            total_entitlement=Decimal("30.0"),
            days_used=Decimal("0"),
            days_remaining=Decimal("30.0"),
            carryover_days=Decimal("5.0"),
            carryover_expires=date(2026, 3, 31),
        )
        service = VacationCalculationService()
        as_of = date(2026, 1, 15)  # 76 days until March 31

        warning = service.get_expiry_warning(balance, as_of)

        assert warning is None

    @pytest.mark.unit
    def test_info_warning_15_to_30_days(self):
        """Info warning when 15-30 days until expiry."""
        balance = VacationBalance(
            total_entitlement=Decimal("30.0"),
            days_used=Decimal("0"),
            days_remaining=Decimal("30.0"),
            carryover_days=Decimal("5.0"),
            carryover_expires=date(2026, 3, 31),
        )
        service = VacationCalculationService()
        as_of = date(2026, 3, 15)  # 16 days until March 31

        warning = service.get_expiry_warning(balance, as_of)

        assert warning is not None
        assert warning.severity == "info"
        assert warning.days_expiring == Decimal("5.0")
        assert warning.expiry_date == date(2026, 3, 31)
        assert "5.0" in warning.message
        assert "2026-03-31" in warning.message

    @pytest.mark.unit
    def test_warning_7_to_14_days(self):
        """Warning severity when 7-14 days until expiry."""
        balance = VacationBalance(
            total_entitlement=Decimal("30.0"),
            days_used=Decimal("0"),
            days_remaining=Decimal("30.0"),
            carryover_days=Decimal("8.5"),
            carryover_expires=date(2026, 3, 31),
        )
        service = VacationCalculationService()
        as_of = date(2026, 3, 24)  # 7 days until March 31

        warning = service.get_expiry_warning(balance, as_of)

        assert warning is not None
        assert warning.severity == "warning"
        assert warning.days_expiring == Decimal("8.5")
        assert warning.expiry_date == date(2026, 3, 31)

    @pytest.mark.unit
    def test_critical_warning_under_7_days(self):
        """Critical warning when 7 or fewer days until expiry."""
        balance = VacationBalance(
            total_entitlement=Decimal("30.0"),
            days_used=Decimal("0"),
            days_remaining=Decimal("30.0"),
            carryover_days=Decimal("3.0"),
            carryover_expires=date(2026, 3, 31),
        )
        service = VacationCalculationService()
        as_of = date(2026, 3, 28)  # 3 days until March 31

        warning = service.get_expiry_warning(balance, as_of)

        assert warning is not None
        assert warning.severity == "critical"
        assert warning.days_expiring == Decimal("3.0")
        assert warning.expiry_date == date(2026, 3, 31)

    @pytest.mark.unit
    def test_no_warning_after_march_31(self):
        """No warning after March 31 (carryover expired)."""
        balance = VacationBalance(
            total_entitlement=Decimal("25.0"),
            days_used=Decimal("0"),
            days_remaining=Decimal("25.0"),
            carryover_days=Decimal("0"),  # Expired
            carryover_expires=date(2026, 3, 31),
        )
        service = VacationCalculationService()
        as_of = date(2026, 4, 15)

        warning = service.get_expiry_warning(balance, as_of)

        assert warning is None


class TestVacationBalanceDataclass:
    """Tests for VacationBalance dataclass structure."""

    @pytest.mark.unit
    def test_vacation_balance_creation(self):
        """VacationBalance can be created with all fields."""
        balance = VacationBalance(
            total_entitlement=Decimal("30.0"),
            days_used=Decimal("10.5"),
            days_remaining=Decimal("19.5"),
            carryover_days=Decimal("5.0"),
            carryover_expires=date(2026, 3, 31),
        )

        assert balance.total_entitlement == Decimal("30.0")
        assert balance.days_used == Decimal("10.5")
        assert balance.days_remaining == Decimal("19.5")
        assert balance.carryover_days == Decimal("5.0")
        assert balance.carryover_expires == date(2026, 3, 31)

    @pytest.mark.unit
    def test_vacation_balance_carryover_expires_can_be_none(self):
        """VacationBalance carryover_expires can be None."""
        balance = VacationBalance(
            total_entitlement=Decimal("30.0"),
            days_used=Decimal("0"),
            days_remaining=Decimal("30.0"),
            carryover_days=Decimal("0"),
            carryover_expires=None,
        )

        assert balance.carryover_expires is None


class TestVacationWarningDataclass:
    """Tests for VacationWarning dataclass structure."""

    @pytest.mark.unit
    def test_vacation_warning_creation(self):
        """VacationWarning can be created with all fields."""
        warning = VacationWarning(
            severity="warning",
            message="5.0 Urlaubstage verfallen am 2026-03-31",
            days_expiring=Decimal("5.0"),
            expiry_date=date(2026, 3, 31),
        )

        assert warning.severity == "warning"
        assert warning.message == "5.0 Urlaubstage verfallen am 2026-03-31"
        assert warning.days_expiring == Decimal("5.0")
        assert warning.expiry_date == date(2026, 3, 31)

    @pytest.mark.unit
    def test_vacation_warning_severity_levels(self):
        """VacationWarning supports info, warning, critical severities."""
        info = VacationWarning(
            severity="info",
            message="Info message",
            days_expiring=Decimal("5.0"),
            expiry_date=date(2026, 3, 31),
        )
        warning = VacationWarning(
            severity="warning",
            message="Warning message",
            days_expiring=Decimal("5.0"),
            expiry_date=date(2026, 3, 31),
        )
        critical = VacationWarning(
            severity="critical",
            message="Critical message",
            days_expiring=Decimal("5.0"),
            expiry_date=date(2026, 3, 31),
        )

        assert info.severity == "info"
        assert warning.severity == "warning"
        assert critical.severity == "critical"
