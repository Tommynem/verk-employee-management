"""Tests for summary dataclasses (DaySummary, WeeklySummary, MonthlySummary).

These dataclasses represent aggregated time tracking data for display and reporting.
Following TDD RED phase - tests are written before implementation exists.
"""

from datetime import date
from decimal import Decimal

import pytest

from source.database.enums import AbsenceType
from source.services.summaries import DaySummary, MonthlySummary, WeeklySummary


class TestDaySummary:
    """Tests for DaySummary dataclass."""

    @pytest.mark.unit
    def test_day_summary_creation(self):
        """DaySummary can be created with all required fields."""
        summary = DaySummary(
            date=date(2026, 1, 14),
            actual_hours=Decimal("8.00"),
            target_hours=Decimal("6.40"),
            balance=Decimal("1.60"),
            absence_type=AbsenceType.NONE,
            has_entry=True,
        )

        assert summary.date == date(2026, 1, 14)
        assert summary.actual_hours == Decimal("8.00")
        assert summary.target_hours == Decimal("6.40")
        assert summary.balance == Decimal("1.60")
        assert summary.absence_type == AbsenceType.NONE
        assert summary.has_entry is True

    @pytest.mark.unit
    def test_day_summary_with_absence(self):
        """DaySummary correctly represents a vacation day with no actual work."""
        summary = DaySummary(
            date=date(2026, 1, 15),
            actual_hours=Decimal("0.00"),
            target_hours=Decimal("6.40"),
            balance=Decimal("0.00"),
            absence_type=AbsenceType.VACATION,
            has_entry=True,
        )

        assert summary.date == date(2026, 1, 15)
        assert summary.actual_hours == Decimal("0.00")
        assert summary.target_hours == Decimal("6.40")
        assert summary.balance == Decimal("0.00")
        assert summary.absence_type == AbsenceType.VACATION
        assert summary.has_entry is True


class TestWeeklySummary:
    """Tests for WeeklySummary dataclass."""

    @pytest.mark.unit
    def test_weekly_summary_creation(self):
        """WeeklySummary can be created with a list of DaySummary objects."""
        monday = DaySummary(
            date=date(2026, 1, 12),
            actual_hours=Decimal("8.00"),
            target_hours=Decimal("6.40"),
            balance=Decimal("1.60"),
            absence_type=AbsenceType.NONE,
            has_entry=True,
        )
        tuesday = DaySummary(
            date=date(2026, 1, 13),
            actual_hours=Decimal("7.00"),
            target_hours=Decimal("6.40"),
            balance=Decimal("0.60"),
            absence_type=AbsenceType.NONE,
            has_entry=True,
        )

        summary = WeeklySummary(
            week_start=date(2026, 1, 12),
            week_end=date(2026, 1, 18),
            days=[monday, tuesday],
            total_actual=Decimal("15.00"),
            total_target=Decimal("12.80"),
            total_balance=Decimal("2.20"),
        )

        assert summary.week_start == date(2026, 1, 12)
        assert summary.week_end == date(2026, 1, 18)
        assert len(summary.days) == 2
        assert summary.days[0].date == date(2026, 1, 12)
        assert summary.days[1].date == date(2026, 1, 13)

    @pytest.mark.unit
    def test_weekly_summary_totals(self):
        """WeeklySummary totals are accessible and correct."""
        day = DaySummary(
            date=date(2026, 1, 14),
            actual_hours=Decimal("8.00"),
            target_hours=Decimal("6.40"),
            balance=Decimal("1.60"),
            absence_type=AbsenceType.NONE,
            has_entry=True,
        )

        summary = WeeklySummary(
            week_start=date(2026, 1, 12),
            week_end=date(2026, 1, 18),
            days=[day],
            total_actual=Decimal("40.00"),
            total_target=Decimal("32.00"),
            total_balance=Decimal("8.00"),
        )

        assert summary.total_actual == Decimal("40.00")
        assert summary.total_target == Decimal("32.00")
        assert summary.total_balance == Decimal("8.00")


class TestMonthlySummary:
    """Tests for MonthlySummary dataclass."""

    @pytest.mark.unit
    def test_monthly_summary_creation(self):
        """MonthlySummary can be created with weeks list and carryover values."""
        day = DaySummary(
            date=date(2026, 1, 14),
            actual_hours=Decimal("8.00"),
            target_hours=Decimal("6.40"),
            balance=Decimal("1.60"),
            absence_type=AbsenceType.NONE,
            has_entry=True,
        )
        week = WeeklySummary(
            week_start=date(2026, 1, 12),
            week_end=date(2026, 1, 18),
            days=[day],
            total_actual=Decimal("40.00"),
            total_target=Decimal("32.00"),
            total_balance=Decimal("8.00"),
        )

        summary = MonthlySummary(
            year=2026,
            month=1,
            weeks=[week],
            total_actual=Decimal("160.00"),
            total_target=Decimal("128.00"),
            period_balance=Decimal("32.00"),
            carryover_in=Decimal("10.00"),
            carryover_out=Decimal("42.00"),
        )

        assert summary.year == 2026
        assert summary.month == 1
        assert len(summary.weeks) == 1
        assert summary.weeks[0].week_start == date(2026, 1, 12)
        assert summary.total_actual == Decimal("160.00")
        assert summary.total_target == Decimal("128.00")
        assert summary.period_balance == Decimal("32.00")
        assert summary.carryover_in == Decimal("10.00")
        assert summary.carryover_out == Decimal("42.00")
