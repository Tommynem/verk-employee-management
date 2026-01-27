"""Tests for calculated fields (actual_hours, target_hours, balance)."""

from datetime import date, time
from decimal import Decimal

import pytest

from source.database.calculations import actual_hours, balance, target_hours
from source.database.enums import AbsenceType, RecordStatus
from source.database.models import TimeEntry, UserSettings


class TestActualHours:
    @pytest.mark.unit
    def test_actual_hours_normal_day(self):
        """7:00-15:00 with no break = 8 hours."""
        entry = TimeEntry(
            work_date=date(2026, 1, 14),
            start_time=time(7, 0),
            end_time=time(15, 0),
            break_minutes=0,
            status=RecordStatus.DRAFT,
        )
        assert actual_hours(entry) == Decimal("8.00")

    @pytest.mark.unit
    def test_actual_hours_with_break(self):
        """7:00-15:30 with 30min break = 8 hours."""
        entry = TimeEntry(
            work_date=date(2026, 1, 14),
            start_time=time(7, 0),
            end_time=time(15, 30),
            break_minutes=30,
            status=RecordStatus.DRAFT,
        )
        assert actual_hours(entry) == Decimal("8.00")

    @pytest.mark.unit
    def test_actual_hours_nullable_times(self):
        """No start/end time = 0 hours."""
        entry = TimeEntry(
            work_date=date(2026, 1, 14),
            start_time=None,
            end_time=None,
            break_minutes=0,
            status=RecordStatus.DRAFT,
        )
        assert actual_hours(entry) == Decimal("0.00")

    @pytest.mark.unit
    def test_actual_hours_partial_null(self):
        """Only start_time set = 0 hours."""
        entry = TimeEntry(
            work_date=date(2026, 1, 14),
            start_time=time(7, 0),
            end_time=None,
            break_minutes=0,
            status=RecordStatus.DRAFT,
        )
        assert actual_hours(entry) == Decimal("0.00")


class TestTargetHours:
    @pytest.mark.unit
    def test_target_hours_weekday(self):
        """32h/week = 6.4h/day on Wednesday."""
        entry = TimeEntry(
            work_date=date(2026, 1, 14),  # Wednesday
            status=RecordStatus.DRAFT,
        )
        settings = UserSettings(
            user_id=1,
            weekly_target_hours=Decimal("32.00"),
        )
        assert target_hours(entry, settings) == Decimal("6.40")

    @pytest.mark.unit
    def test_target_hours_saturday(self):
        """Saturday = 0 hours."""
        entry = TimeEntry(
            work_date=date(2026, 1, 17),  # Saturday
            status=RecordStatus.DRAFT,
        )
        settings = UserSettings(
            user_id=1,
            weekly_target_hours=Decimal("32.00"),
        )
        assert target_hours(entry, settings) == Decimal("0.00")

    @pytest.mark.unit
    def test_target_hours_sunday(self):
        """Sunday = 0 hours."""
        entry = TimeEntry(
            work_date=date(2026, 1, 18),  # Sunday
            status=RecordStatus.DRAFT,
        )
        settings = UserSettings(
            user_id=1,
            weekly_target_hours=Decimal("32.00"),
        )
        assert target_hours(entry, settings) == Decimal("0.00")


class TestBalance:
    @pytest.mark.unit
    def test_balance_positive(self):
        """Worked 10h with 6.4h target = +3.6."""
        entry = TimeEntry(
            work_date=date(2026, 1, 14),  # Wednesday
            start_time=time(7, 0),
            end_time=time(17, 0),
            break_minutes=0,
            status=RecordStatus.DRAFT,
        )
        settings = UserSettings(
            user_id=1,
            weekly_target_hours=Decimal("32.00"),
        )
        assert balance(entry, settings) == Decimal("3.60")

    @pytest.mark.unit
    def test_balance_negative(self):
        """Worked 4h with 6.4h target = -2.4."""
        entry = TimeEntry(
            work_date=date(2026, 1, 14),  # Wednesday
            start_time=time(9, 0),
            end_time=time(13, 0),
            break_minutes=0,
            status=RecordStatus.DRAFT,
        )
        settings = UserSettings(
            user_id=1,
            weekly_target_hours=Decimal("32.00"),
        )
        assert balance(entry, settings) == Decimal("-2.40")

    @pytest.mark.unit
    def test_balance_vacation_counts_as_worked(self):
        """Vacation = 0 balance (neutral)."""
        entry = TimeEntry(
            work_date=date(2026, 1, 14),  # Wednesday
            absence_type=AbsenceType.VACATION,
            status=RecordStatus.DRAFT,
        )
        settings = UserSettings(
            user_id=1,
            weekly_target_hours=Decimal("32.00"),
        )
        assert balance(entry, settings) == Decimal("0.00")

    @pytest.mark.unit
    def test_balance_sick_counts_as_worked(self):
        """Sick = 0 balance (neutral)."""
        entry = TimeEntry(
            work_date=date(2026, 1, 14),  # Wednesday
            absence_type=AbsenceType.SICK,
            status=RecordStatus.DRAFT,
        )
        settings = UserSettings(
            user_id=1,
            weekly_target_hours=Decimal("32.00"),
        )
        assert balance(entry, settings) == Decimal("0.00")

    @pytest.mark.unit
    def test_balance_holiday_counts_as_worked(self):
        """Holiday = 0 balance (neutral)."""
        entry = TimeEntry(
            work_date=date(2026, 1, 14),  # Wednesday
            absence_type=AbsenceType.HOLIDAY,
            status=RecordStatus.DRAFT,
        )
        settings = UserSettings(
            user_id=1,
            weekly_target_hours=Decimal("32.00"),
        )
        assert balance(entry, settings) == Decimal("0.00")
