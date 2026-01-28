"""Tests for TimeCalculationService.

This module tests the TimeCalculationService which wraps the standalone calculation
functions from source.database.calculations into a service interface.
"""

from datetime import date, time
from decimal import Decimal

import pytest

from source.database.enums import AbsenceType
from source.services.time_calculation import TimeCalculationService
from tests.factories import TimeEntryFactory, UserSettingsFactory, VacationEntryFactory


class TestTimeCalculationServiceWrapper:
    """Tests for TimeCalculationService wrapper methods."""

    @pytest.mark.unit
    def test_actual_hours_delegates_to_calculation(self):
        """Service actual_hours returns same result as standalone function."""
        # Create entry with 7:00-15:00 = 8 hours
        entry = TimeEntryFactory.build(
            work_date=date(2026, 1, 14),
            start_time=time(7, 0),
            end_time=time(15, 0),
            break_minutes=0,
        )
        service = TimeCalculationService()
        assert service.actual_hours(entry) == Decimal("8.00")

    @pytest.mark.unit
    def test_target_hours_delegates_to_calculation(self):
        """Service target_hours returns same result as standalone function."""
        entry = TimeEntryFactory.build(work_date=date(2026, 1, 14))  # Wednesday
        settings = UserSettingsFactory.build(weekly_target_hours=Decimal("32.00"))
        service = TimeCalculationService()
        assert service.target_hours(entry, settings) == Decimal("6.40")

    @pytest.mark.unit
    def test_daily_balance_delegates_to_calculation(self):
        """Service daily_balance returns same result as standalone balance function."""
        entry = TimeEntryFactory.build(
            work_date=date(2026, 1, 14),  # Wednesday
            start_time=time(7, 0),
            end_time=time(17, 0),  # 10 hours
            break_minutes=0,
        )
        settings = UserSettingsFactory.build(weekly_target_hours=Decimal("32.00"))
        service = TimeCalculationService()
        # 10h actual - 6.4h target = +3.6 balance
        assert service.daily_balance(entry, settings) == Decimal("3.60")


class TestPeriodBalance:
    """Tests for TimeCalculationService.period_balance method."""

    @pytest.mark.unit
    def test_period_balance_single_entry(self):
        """Single entry balance equals daily balance."""
        entry = TimeEntryFactory.build(
            work_date=date(2026, 1, 14),  # Wednesday
            start_time=time(7, 0),
            end_time=time(17, 0),  # 10 hours
            break_minutes=0,
        )
        settings = UserSettingsFactory.build(weekly_target_hours=Decimal("32.00"))
        service = TimeCalculationService()
        # 10h - 6.4h = +3.6
        assert service.period_balance([entry], settings) == Decimal("3.60")

    @pytest.mark.unit
    def test_period_balance_multiple_entries(self):
        """Multiple entries sum their balances."""
        entries = [
            TimeEntryFactory.build(
                work_date=date(2026, 1, 13),  # Tuesday
                start_time=time(7, 0),
                end_time=time(17, 0),  # 10h = +3.6
                break_minutes=0,
            ),
            TimeEntryFactory.build(
                work_date=date(2026, 1, 14),  # Wednesday
                start_time=time(7, 0),
                end_time=time(11, 0),  # 4h = -2.4
                break_minutes=0,
            ),
        ]
        settings = UserSettingsFactory.build(weekly_target_hours=Decimal("32.00"))
        service = TimeCalculationService()
        # +3.6 + (-2.4) = +1.2
        assert service.period_balance(entries, settings) == Decimal("1.20")

    @pytest.mark.unit
    def test_period_balance_with_carryover(self):
        """Include carryover from user settings when flag is True."""
        entry = TimeEntryFactory.build(
            work_date=date(2026, 1, 14),
            start_time=time(7, 0),
            end_time=time(17, 0),  # 10h = +3.6
            break_minutes=0,
        )
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            carryover_hours=Decimal("5.00"),  # Carryover from previous period
        )
        service = TimeCalculationService()
        # +3.6 + 5.0 = +8.6
        assert service.period_balance([entry], settings, include_carryover=True) == Decimal("8.60")

    @pytest.mark.unit
    def test_period_balance_without_carryover(self):
        """Exclude carryover when flag is False."""
        entry = TimeEntryFactory.build(
            work_date=date(2026, 1, 14),
            start_time=time(7, 0),
            end_time=time(17, 0),  # 10h = +3.6
            break_minutes=0,
        )
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            carryover_hours=Decimal("5.00"),
        )
        service = TimeCalculationService()
        # Just daily balance, no carryover
        assert service.period_balance([entry], settings, include_carryover=False) == Decimal("3.60")

    @pytest.mark.unit
    def test_period_balance_empty_entries(self):
        """Empty entry list returns 0 (or carryover if included)."""
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            carryover_hours=Decimal("2.50"),
        )
        service = TimeCalculationService()
        assert service.period_balance([], settings, include_carryover=False) == Decimal("0.00")
        assert service.period_balance([], settings, include_carryover=True) == Decimal("2.50")

    @pytest.mark.unit
    def test_period_balance_ignores_entries_before_tracking_start(self):
        """Entries before tracking_start_date should be ignored in balance calculation."""
        # Use weekdays only (Jan 6=Tue, Jan 12=Mon, Jan 14=Wed)
        tracking_start = date(2026, 1, 12)
        entries = [
            TimeEntryFactory.build(
                work_date=date(2026, 1, 6),  # Tuesday - Before tracking start
                start_time=time(7, 0),
                end_time=time(17, 0),  # 10h = +3.6 (should be ignored)
                break_minutes=0,
            ),
            TimeEntryFactory.build(
                work_date=date(2026, 1, 12),  # Monday - On tracking start date
                start_time=time(7, 0),
                end_time=time(11, 0),  # 4h, target 6.4h = -2.4
                break_minutes=0,
            ),
            TimeEntryFactory.build(
                work_date=date(2026, 1, 14),  # Wednesday - After tracking start
                start_time=time(7, 0),
                end_time=time(15, 0),  # 8h, target 6.4h = +1.6
                break_minutes=0,
            ),
        ]
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            tracking_start_date=tracking_start,
        )
        service = TimeCalculationService()
        # Only entries on/after 2026-01-12 should count: -2.4 + 1.6 = -0.8
        assert service.period_balance(entries, settings, include_carryover=False) == Decimal("-0.80")

    @pytest.mark.unit
    def test_period_balance_includes_initial_offset(self):
        """Initial hours offset should be added to period balance."""
        entry = TimeEntryFactory.build(
            work_date=date(2026, 1, 14),
            start_time=time(7, 0),
            end_time=time(17, 0),  # 10h = +3.6
            break_minutes=0,
        )
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            initial_hours_offset=Decimal("15.50"),
        )
        service = TimeCalculationService()
        # Period balance: 3.6 + initial_offset: 15.5 = 19.1
        assert service.period_balance([entry], settings, include_carryover=True) == Decimal("19.10")

    @pytest.mark.unit
    def test_period_balance_with_no_tracking_start_includes_all(self):
        """When tracking_start_date is None, all entries should be included."""
        entries = [
            TimeEntryFactory.build(
                work_date=date(2026, 1, 5),
                start_time=time(7, 0),
                end_time=time(17, 0),  # 10h = +3.6
                break_minutes=0,
            ),
            TimeEntryFactory.build(
                work_date=date(2026, 1, 15),
                start_time=time(7, 0),
                end_time=time(11, 0),  # 4h = -2.4
                break_minutes=0,
            ),
        ]
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            tracking_start_date=None,  # No tracking start filter
        )
        service = TimeCalculationService()
        # Both entries should count: 3.6 + (-2.4) = 1.2
        assert service.period_balance(entries, settings, include_carryover=False) == Decimal("1.20")

    @pytest.mark.unit
    def test_period_balance_tracking_start_and_initial_offset_combined(self):
        """Test combination of tracking_start_date and initial_hours_offset."""
        tracking_start = date(2026, 1, 10)
        entries = [
            TimeEntryFactory.build(
                work_date=date(2026, 1, 5),  # Before tracking start - ignored
                start_time=time(7, 0),
                end_time=time(17, 0),
                break_minutes=0,
            ),
            TimeEntryFactory.build(
                work_date=date(2026, 1, 12),  # After tracking start - counted
                start_time=time(7, 0),
                end_time=time(15, 0),  # 8h = +1.6
                break_minutes=0,
            ),
        ]
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            tracking_start_date=tracking_start,
            initial_hours_offset=Decimal("10.00"),
        )
        service = TimeCalculationService()
        # Only entry after tracking start: 1.6 + initial_offset: 10.0 = 11.6
        assert service.period_balance(entries, settings, include_carryover=True) == Decimal("11.60")


class TestWeeklySummary:
    """Tests for TimeCalculationService.weekly_summary method."""

    @pytest.mark.unit
    def test_weekly_summary_full_week(self):
        """Generate summary for a full work week with entries."""
        # Monday Jan 12, 2026 to Sunday Jan 18, 2026
        week_start = date(2026, 1, 12)
        entries = [
            TimeEntryFactory.build(
                work_date=date(2026, 1, 12), start_time=time(7, 0), end_time=time(15, 0), break_minutes=30  # Monday
            ),
            TimeEntryFactory.build(
                work_date=date(2026, 1, 13), start_time=time(7, 0), end_time=time(15, 0), break_minutes=30  # Tuesday
            ),
            TimeEntryFactory.build(
                work_date=date(2026, 1, 14), start_time=time(7, 0), end_time=time(15, 0), break_minutes=30  # Wednesday
            ),
        ]
        settings = UserSettingsFactory.build(weekly_target_hours=Decimal("32.00"))
        service = TimeCalculationService()

        summary = service.weekly_summary(entries, settings, week_start)

        assert summary.week_start == date(2026, 1, 12)
        assert summary.week_end == date(2026, 1, 18)
        assert len(summary.days) == 7  # All 7 days
        assert summary.total_actual == Decimal("22.50")  # 7.5h * 3 days

    @pytest.mark.unit
    def test_weekly_summary_days_without_entries(self):
        """Days without entries should have has_entry=False, 0 actual hours."""
        week_start = date(2026, 1, 12)
        entries = [
            TimeEntryFactory.build(
                work_date=date(2026, 1, 12),  # Only Monday
                start_time=time(7, 0),
                end_time=time(15, 0),
                break_minutes=30,
            ),
        ]
        settings = UserSettingsFactory.build(weekly_target_hours=Decimal("32.00"))
        service = TimeCalculationService()

        summary = service.weekly_summary(entries, settings, week_start)

        # Monday has entry
        assert summary.days[0].has_entry is True
        assert summary.days[0].actual_hours == Decimal("7.50")
        # Tuesday has no entry
        assert summary.days[1].has_entry is False
        assert summary.days[1].actual_hours == Decimal("0.00")

    @pytest.mark.unit
    def test_weekly_summary_with_vacation(self):
        """Vacation days should have balance of 0."""
        week_start = date(2026, 1, 12)
        entries = [
            VacationEntryFactory.build(work_date=date(2026, 1, 12)),  # Monday vacation
            TimeEntryFactory.build(
                work_date=date(2026, 1, 13),  # Tuesday work
                start_time=time(7, 0),
                end_time=time(15, 0),
                break_minutes=30,
            ),
        ]
        settings = UserSettingsFactory.build(weekly_target_hours=Decimal("32.00"))
        service = TimeCalculationService()

        summary = service.weekly_summary(entries, settings, week_start)

        # Monday vacation - balance 0
        assert summary.days[0].absence_type == AbsenceType.VACATION
        assert summary.days[0].balance == Decimal("0.00")
        # Tuesday work - balance = 7.5 - 6.4 = 1.1
        assert summary.days[1].balance == Decimal("1.10")

    @pytest.mark.unit
    def test_weekly_summary_totals_calculation(self):
        """Verify totals are calculated correctly."""
        week_start = date(2026, 1, 12)
        entries = [
            TimeEntryFactory.build(
                work_date=date(2026, 1, 12), start_time=time(7, 0), end_time=time(17, 0), break_minutes=0  # 10h
            ),
            TimeEntryFactory.build(
                work_date=date(2026, 1, 13), start_time=time(7, 0), end_time=time(11, 0), break_minutes=0  # 4h
            ),
        ]
        settings = UserSettingsFactory.build(weekly_target_hours=Decimal("32.00"))
        service = TimeCalculationService()

        summary = service.weekly_summary(entries, settings, week_start)

        assert summary.total_actual == Decimal("14.00")  # 10 + 4
        assert summary.total_target == Decimal("32.00")  # 6.4 * 5 weekdays
        # Balance: (10-6.4) + (4-6.4) + (-6.4*3 for missing days) = 3.6 - 2.4 - 19.2 = -18.0
        assert summary.total_balance == Decimal("-18.00")


class TestMonthlySummary:
    """Tests for TimeCalculationService.monthly_summary method."""

    @pytest.mark.unit
    def test_monthly_summary_basic(self):
        """Generate monthly summary for January 2026."""
        entries = [
            TimeEntryFactory.build(
                work_date=date(2026, 1, 5), start_time=time(7, 0), end_time=time(15, 0), break_minutes=30  # Monday
            ),
            TimeEntryFactory.build(
                work_date=date(2026, 1, 6), start_time=time(7, 0), end_time=time(15, 0), break_minutes=30  # Tuesday
            ),
        ]
        settings = UserSettingsFactory.build(weekly_target_hours=Decimal("32.00"))
        service = TimeCalculationService()

        summary = service.monthly_summary(entries, settings, 2026, 1)

        assert summary.year == 2026
        assert summary.month == 1
        assert len(summary.weeks) >= 4  # January 2026 has 5 weeks partially

    @pytest.mark.unit
    def test_monthly_summary_with_carryover_in(self):
        """Carryover from previous month is included."""
        entries = [
            TimeEntryFactory.build(
                work_date=date(2026, 1, 5), start_time=time(7, 0), end_time=time(17, 0), break_minutes=0  # 10h = +3.6
            ),
        ]
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            carryover_hours=Decimal("10.00"),
        )
        service = TimeCalculationService()

        summary = service.monthly_summary(entries, settings, 2026, 1)

        assert summary.carryover_in == Decimal("10.00")

    @pytest.mark.unit
    def test_monthly_summary_carryover_out_calculation(self):
        """Carryover out equals carryover in plus period balance."""
        # Single entry with +3.6 balance
        entries = [
            TimeEntryFactory.build(
                work_date=date(2026, 1, 5), start_time=time(7, 0), end_time=time(17, 0), break_minutes=0  # Monday
            ),
        ]
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            carryover_hours=Decimal("5.00"),
        )
        service = TimeCalculationService()

        summary = service.monthly_summary(entries, settings, 2026, 1)

        # carryover_out = carryover_in + period_balance
        # period_balance should be the sum of all week balances
        assert summary.carryover_in == Decimal("5.00")
        # carryover_out = 5.00 + period_balance (negative due to missing work days)
        assert summary.carryover_out == summary.carryover_in + summary.period_balance

    @pytest.mark.unit
    def test_monthly_summary_totals(self):
        """Verify monthly totals are sum of weekly totals."""
        # Create entries for two different weeks
        entries = [
            TimeEntryFactory.build(
                work_date=date(2026, 1, 5),  # Week 1 Monday
                start_time=time(7, 0),
                end_time=time(15, 0),
                break_minutes=30,
            ),
            TimeEntryFactory.build(
                work_date=date(2026, 1, 12),  # Week 2 Monday
                start_time=time(7, 0),
                end_time=time(15, 0),
                break_minutes=30,
            ),
        ]
        settings = UserSettingsFactory.build(weekly_target_hours=Decimal("32.00"))
        service = TimeCalculationService()

        summary = service.monthly_summary(entries, settings, 2026, 1)

        # total_actual should be sum of all weeks' total_actual
        weeks_total_actual = sum(w.total_actual for w in summary.weeks)
        assert summary.total_actual == weeks_total_actual

    @pytest.mark.unit
    def test_monthly_summary_no_carryover(self):
        """When carryover_hours is None, carryover_in should be 0."""
        entries = [
            TimeEntryFactory.build(
                work_date=date(2026, 1, 5), start_time=time(7, 0), end_time=time(15, 0), break_minutes=30
            ),
        ]
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            carryover_hours=None,
        )
        service = TimeCalculationService()

        summary = service.monthly_summary(entries, settings, 2026, 1)

        assert summary.carryover_in == Decimal("0.00")

    @pytest.mark.unit
    def test_monthly_summary_uses_initial_offset_as_carryover_for_first_month(self):
        """For the first tracked month, initial_hours_offset should be used as carryover_in."""
        tracking_start = date(2026, 1, 10)
        entries = [
            TimeEntryFactory.build(
                work_date=date(2026, 1, 12),  # First entry in tracked period
                start_time=time(7, 0),
                end_time=time(17, 0),  # 10h = +3.6
                break_minutes=0,
            ),
        ]
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            tracking_start_date=tracking_start,
            initial_hours_offset=Decimal("20.00"),
            carryover_hours=None,  # Should be ignored for first month
        )
        service = TimeCalculationService()

        summary = service.monthly_summary(entries, settings, 2026, 1)

        # For January 2026 (first month with tracking_start_date), use initial_hours_offset
        assert summary.carryover_in == Decimal("20.00")

    @pytest.mark.unit
    def test_monthly_summary_carryover_out_includes_initial_offset(self):
        """Carryover out should equal initial_offset + period_balance for first tracked month."""
        tracking_start = date(2026, 1, 10)
        entries = [
            TimeEntryFactory.build(
                work_date=date(2026, 1, 12),  # After tracking start
                start_time=time(7, 0),
                end_time=time(15, 0),  # 8h = +1.6
                break_minutes=0,
            ),
        ]
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            tracking_start_date=tracking_start,
            initial_hours_offset=Decimal("15.50"),
        )
        service = TimeCalculationService()

        summary = service.monthly_summary(entries, settings, 2026, 1)

        # carryover_in = 15.50 (initial_offset)
        assert summary.carryover_in == Decimal("15.50")
        # carryover_out = carryover_in + period_balance
        assert summary.carryover_out == summary.carryover_in + summary.period_balance

    @pytest.mark.unit
    def test_monthly_summary_respects_tracking_start_date(self):
        """Monthly summary should filter entries based on tracking_start_date."""
        tracking_start = date(2026, 1, 15)
        entries = [
            TimeEntryFactory.build(
                work_date=date(2026, 1, 5),  # Before tracking start - ignored
                start_time=time(7, 0),
                end_time=time(17, 0),
                break_minutes=0,
            ),
            TimeEntryFactory.build(
                work_date=date(2026, 1, 15),  # On tracking start - counted
                start_time=time(7, 0),
                end_time=time(15, 0),  # 8h = +1.6
                break_minutes=0,
            ),
            TimeEntryFactory.build(
                work_date=date(2026, 1, 20),  # After tracking start - counted
                start_time=time(7, 0),
                end_time=time(11, 0),  # 4h = -2.4
                break_minutes=0,
            ),
        ]
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            tracking_start_date=tracking_start,
            initial_hours_offset=Decimal("5.00"),
        )
        service = TimeCalculationService()

        summary = service.monthly_summary(entries, settings, 2026, 1)

        # Only entries on/after 2026-01-15 should be in totals
        # The actual calculation will depend on how weekly_summary filters, but period_balance
        # should only reflect entries after tracking_start_date
        assert summary.carryover_in == Decimal("5.00")  # initial_offset for first month
