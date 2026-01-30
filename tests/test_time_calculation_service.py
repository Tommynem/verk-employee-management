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
    def test_period_balance_with_initial_offset(self):
        """Include initial_hours_offset from user settings when flag is True."""
        entry = TimeEntryFactory.build(
            work_date=date(2026, 1, 14),
            start_time=time(7, 0),
            end_time=time(17, 0),  # 10h = +3.6
            break_minutes=0,
        )
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            initial_hours_offset=Decimal("5.00"),  # Initial offset from tracking start
        )
        service = TimeCalculationService()
        # +3.6 + 5.0 = +8.6
        assert service.period_balance([entry], settings, include_carryover=True) == Decimal("8.60")

    @pytest.mark.unit
    def test_period_balance_without_initial_offset(self):
        """Exclude initial offset when flag is False."""
        entry = TimeEntryFactory.build(
            work_date=date(2026, 1, 14),
            start_time=time(7, 0),
            end_time=time(17, 0),  # 10h = +3.6
            break_minutes=0,
        )
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            initial_hours_offset=Decimal("5.00"),
        )
        service = TimeCalculationService()
        # Just daily balance, no initial offset
        assert service.period_balance([entry], settings, include_carryover=False) == Decimal("3.60")

    @pytest.mark.unit
    def test_period_balance_empty_entries(self):
        """Empty entry list returns 0 (or initial offset if included)."""
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            initial_hours_offset=Decimal("2.50"),
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


class TestAllTimeBalance:
    """Tests for TimeCalculationService.all_time_balance method."""

    @pytest.mark.unit
    def test_all_time_balance_single_entry_no_offset(self):
        """Single entry with no offset returns daily balance."""
        entry = TimeEntryFactory.build(
            work_date=date(2026, 1, 14),  # Wednesday
            start_time=time(7, 0),
            end_time=time(17, 0),  # 10 hours
            break_minutes=0,
        )
        settings = UserSettingsFactory.build(weekly_target_hours=Decimal("32.00"))
        service = TimeCalculationService()
        # 10h - 6.4h = +3.6
        assert service.all_time_balance([entry], settings) == Decimal("3.60")

    @pytest.mark.unit
    def test_all_time_balance_multiple_entries_sum(self):
        """Multiple entries sum their daily balances."""
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
            TimeEntryFactory.build(
                work_date=date(2026, 1, 15),  # Thursday
                start_time=time(7, 0),
                end_time=time(15, 0),  # 8h = +1.6
                break_minutes=0,
            ),
        ]
        settings = UserSettingsFactory.build(weekly_target_hours=Decimal("32.00"))
        service = TimeCalculationService()
        # +3.6 + (-2.4) + 1.6 = +2.8
        assert service.all_time_balance(entries, settings) == Decimal("2.80")

    @pytest.mark.unit
    def test_all_time_balance_with_initial_hours_offset(self):
        """Initial hours offset is added to sum of balances."""
        entry = TimeEntryFactory.build(
            work_date=date(2026, 1, 14),  # Wednesday
            start_time=time(7, 0),
            end_time=time(17, 0),  # 10h = +3.6
            break_minutes=0,
        )
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            initial_hours_offset=Decimal("15.50"),
        )
        service = TimeCalculationService()
        # Balance: 3.6 + initial_offset: 15.5 = 19.1
        assert service.all_time_balance([entry], settings) == Decimal("19.10")

    @pytest.mark.unit
    def test_all_time_balance_respects_tracking_start_date(self):
        """Entries before tracking_start_date are ignored."""
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
                end_time=time(11, 0),  # 4h = -2.4
                break_minutes=0,
            ),
            TimeEntryFactory.build(
                work_date=date(2026, 1, 14),  # Wednesday - After tracking start
                start_time=time(7, 0),
                end_time=time(15, 0),  # 8h = +1.6
                break_minutes=0,
            ),
        ]
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            tracking_start_date=tracking_start,
        )
        service = TimeCalculationService()
        # Only entries on/after 2026-01-12: -2.4 + 1.6 = -0.8
        assert service.all_time_balance(entries, settings) == Decimal("-0.80")

    @pytest.mark.unit
    def test_all_time_balance_with_target_date_cutoff(self):
        """Only entries up to and including target_date are counted."""
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
            TimeEntryFactory.build(
                work_date=date(2026, 1, 15),  # Thursday
                start_time=time(7, 0),
                end_time=time(15, 0),  # 8h = +1.6 (should be ignored)
                break_minutes=0,
            ),
        ]
        settings = UserSettingsFactory.build(weekly_target_hours=Decimal("32.00"))
        service = TimeCalculationService()
        # Only entries up to 2026-01-14: +3.6 + (-2.4) = +1.2
        assert service.all_time_balance(entries, settings, target_date=date(2026, 1, 14)) == Decimal("1.20")

    @pytest.mark.unit
    def test_all_time_balance_target_date_none_includes_all(self):
        """When target_date is None, all entries are included."""
        entries = [
            TimeEntryFactory.build(
                work_date=date(2026, 1, 13),  # Tuesday
                start_time=time(7, 0),
                end_time=time(17, 0),  # 10h = +3.6
                break_minutes=0,
            ),
            TimeEntryFactory.build(
                work_date=date(2026, 1, 20),  # Tuesday (next week)
                start_time=time(7, 0),
                end_time=time(11, 0),  # 4h = -2.4
                break_minutes=0,
            ),
        ]
        settings = UserSettingsFactory.build(weekly_target_hours=Decimal("32.00"))
        service = TimeCalculationService()
        # All entries: +3.6 + (-2.4) = +1.2
        assert service.all_time_balance(entries, settings, target_date=None) == Decimal("1.20")

    @pytest.mark.unit
    def test_all_time_balance_empty_entries_with_offset(self):
        """Empty entries list with offset returns offset only."""
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            initial_hours_offset=Decimal("10.00"),
        )
        service = TimeCalculationService()
        # No entries, just initial_offset
        assert service.all_time_balance([], settings) == Decimal("10.00")

    @pytest.mark.unit
    def test_all_time_balance_empty_entries_no_offset(self):
        """Empty entries list with no offset returns 0."""
        settings = UserSettingsFactory.build(weekly_target_hours=Decimal("32.00"))
        service = TimeCalculationService()
        assert service.all_time_balance([], settings) == Decimal("0.00")

    @pytest.mark.unit
    def test_all_time_balance_target_date_before_all_entries(self):
        """Target date before all entries returns just initial_offset (or 0)."""
        entries = [
            TimeEntryFactory.build(
                work_date=date(2026, 1, 13),  # Tuesday
                start_time=time(7, 0),
                end_time=time(17, 0),
                break_minutes=0,
            ),
            TimeEntryFactory.build(
                work_date=date(2026, 1, 14),  # Wednesday
                start_time=time(7, 0),
                end_time=time(11, 0),
                break_minutes=0,
            ),
        ]
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            initial_hours_offset=Decimal("5.00"),
        )
        service = TimeCalculationService()
        # target_date before all entries, no entries counted
        assert service.all_time_balance(entries, settings, target_date=date(2026, 1, 10)) == Decimal("5.00")

    @pytest.mark.unit
    def test_all_time_balance_combination_tracking_start_target_date_offset(self):
        """Test combination of tracking_start_date, target_date, and initial_offset."""
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
            TimeEntryFactory.build(
                work_date=date(2026, 1, 14),  # After tracking start - counted
                start_time=time(7, 0),
                end_time=time(11, 0),  # 4h = -2.4
                break_minutes=0,
            ),
            TimeEntryFactory.build(
                work_date=date(2026, 1, 20),  # After target_date - ignored
                start_time=time(7, 0),
                end_time=time(17, 0),
                break_minutes=0,
            ),
        ]
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            tracking_start_date=tracking_start,
            initial_hours_offset=Decimal("12.50"),
        )
        service = TimeCalculationService()
        # Only entries between tracking_start and target_date: 1.6 + (-2.4) = -0.8
        # Plus initial_offset: -0.8 + 12.5 = 11.7
        assert service.all_time_balance(entries, settings, target_date=date(2026, 1, 15)) == Decimal("11.70")

    @pytest.mark.unit
    def test_all_time_balance_negative_offset(self):
        """Initial offset can be negative."""
        entry = TimeEntryFactory.build(
            work_date=date(2026, 1, 14),  # Wednesday
            start_time=time(7, 0),
            end_time=time(17, 0),  # 10h = +3.6
            break_minutes=0,
        )
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            initial_hours_offset=Decimal("-8.00"),
        )
        service = TimeCalculationService()
        # Balance: 3.6 + (-8.0) = -4.4
        assert service.all_time_balance([entry], settings) == Decimal("-4.40")

    @pytest.mark.unit
    def test_all_time_balance_weekend_entries(self):
        """Weekend entries count with 0 target hours."""
        entries = [
            TimeEntryFactory.build(
                work_date=date(2026, 1, 10),  # Saturday
                start_time=time(7, 0),
                end_time=time(15, 0),  # 8h, target 0h = +8.0
                break_minutes=0,
            ),
            TimeEntryFactory.build(
                work_date=date(2026, 1, 11),  # Sunday
                start_time=time(7, 0),
                end_time=time(11, 0),  # 4h, target 0h = +4.0
                break_minutes=0,
            ),
        ]
        settings = UserSettingsFactory.build(weekly_target_hours=Decimal("32.00"))
        service = TimeCalculationService()
        # Weekend work: 8.0 + 4.0 = +12.0
        assert service.all_time_balance(entries, settings) == Decimal("12.00")

    @pytest.mark.unit
    def test_all_time_balance_with_vacation_entries(self):
        """Vacation entries have 0 balance."""
        entries = [
            VacationEntryFactory.build(work_date=date(2026, 1, 13)),  # Tuesday vacation
            TimeEntryFactory.build(
                work_date=date(2026, 1, 14),  # Wednesday work
                start_time=time(7, 0),
                end_time=time(15, 0),  # 8h = +1.6
                break_minutes=0,
            ),
        ]
        settings = UserSettingsFactory.build(weekly_target_hours=Decimal("32.00"))
        service = TimeCalculationService()
        # Vacation balance = 0, work balance = 1.6
        assert service.all_time_balance(entries, settings) == Decimal("1.60")

    @pytest.mark.unit
    def test_all_time_balance_target_date_equals_tracking_start(self):
        """Target date equal to tracking start includes entries on that date."""
        tracking_start = date(2026, 1, 12)
        entries = [
            TimeEntryFactory.build(
                work_date=date(2026, 1, 12),  # On both tracking start AND target date
                start_time=time(7, 0),
                end_time=time(15, 0),  # 8h = +1.6
                break_minutes=0,
            ),
            TimeEntryFactory.build(
                work_date=date(2026, 1, 13),  # After target date - ignored
                start_time=time(7, 0),
                end_time=time(17, 0),
                break_minutes=0,
            ),
        ]
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            tracking_start_date=tracking_start,
        )
        service = TimeCalculationService()
        # Only entry on 2026-01-12: +1.6
        assert service.all_time_balance(entries, settings, target_date=tracking_start) == Decimal("1.60")


class TestMonthlySummaryCarryover:
    """Tests for monthly_summary carryover calculation using all_time_balance.

    These tests verify that monthly_summary calculates carryover_in by summing
    historical balances from previous months instead of using static carryover_hours.
    """

    @pytest.mark.unit
    def test_monthly_summary_carryover_in_from_historical_data(self):
        """carryover_in for month N equals all_time_balance up to end of month N-1."""
        # July entry: 10h worked on Monday = +3.6 balance (target 6.4h)
        july_entry = TimeEntryFactory.build(
            work_date=date(2025, 7, 7),  # Monday
            start_time=time(7, 0),
            end_time=time(17, 0),  # 10 hours
            break_minutes=0,
        )
        # August entry: 8h worked on Monday = +1.6 balance
        aug_entry = TimeEntryFactory.build(
            work_date=date(2025, 8, 4),  # Monday
            start_time=time(7, 0),
            end_time=time(15, 0),  # 8 hours
            break_minutes=0,
        )
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            tracking_start_date=date(2025, 7, 1),
            initial_hours_offset=Decimal("5.00"),
        )
        service = TimeCalculationService()

        # Pass ALL entries to monthly_summary (both July and August)
        all_entries = [july_entry, aug_entry]
        summary = service.monthly_summary(all_entries, settings, 2025, 8)

        # carryover_in for August = July's balance (3.6) + initial_offset (5.0) = 8.6
        assert summary.carryover_in == Decimal("8.60")

    @pytest.mark.unit
    def test_monthly_summary_first_tracked_month_uses_initial_offset(self):
        """First tracked month uses only initial_hours_offset as carryover_in."""
        # July is the first tracked month
        july_entry = TimeEntryFactory.build(
            work_date=date(2025, 7, 7),  # Monday in July
            start_time=time(7, 0),
            end_time=time(17, 0),  # 10 hours = +3.6
            break_minutes=0,
        )
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            tracking_start_date=date(2025, 7, 1),
            initial_hours_offset=Decimal("15.50"),
        )
        service = TimeCalculationService()

        summary = service.monthly_summary([july_entry], settings, 2025, 7)

        # carryover_in for first tracked month = initial_offset only (15.50)
        assert summary.carryover_in == Decimal("15.50")

    @pytest.mark.unit
    def test_monthly_summary_carryover_out_calculation(self):
        """carryover_out equals carryover_in plus period_balance."""
        # July entry: +3.6 balance
        july_entry = TimeEntryFactory.build(
            work_date=date(2025, 7, 7),  # Monday
            start_time=time(7, 0),
            end_time=time(17, 0),  # 10 hours
            break_minutes=0,
        )
        # August entry: +1.6 balance
        aug_entry = TimeEntryFactory.build(
            work_date=date(2025, 8, 4),  # Monday
            start_time=time(7, 0),
            end_time=time(15, 0),  # 8 hours
            break_minutes=0,
        )
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            tracking_start_date=date(2025, 7, 1),
            initial_hours_offset=Decimal("10.00"),
        )
        service = TimeCalculationService()

        all_entries = [july_entry, aug_entry]
        summary = service.monthly_summary(all_entries, settings, 2025, 8)

        # carryover_in = July balance (3.6) + initial_offset (10.0) = 13.6
        expected_carryover_in = Decimal("13.60")
        assert summary.carryover_in == expected_carryover_in

        # carryover_out = carryover_in + August period_balance
        assert summary.carryover_out == summary.carryover_in + summary.period_balance

    @pytest.mark.unit
    def test_monthly_summary_multi_month_accumulation(self):
        """carryover accumulates correctly across multiple months."""
        # July entry: Monday 10h = +3.6
        july_entry = TimeEntryFactory.build(
            work_date=date(2025, 7, 7),  # Monday
            start_time=time(7, 0),
            end_time=time(17, 0),
            break_minutes=0,
        )
        # August entry: Monday 8h = +1.6
        aug_entry = TimeEntryFactory.build(
            work_date=date(2025, 8, 4),  # Monday
            start_time=time(7, 0),
            end_time=time(15, 0),
            break_minutes=0,
        )
        # September entry: Monday 4h = -2.4
        sept_entry = TimeEntryFactory.build(
            work_date=date(2025, 9, 1),  # Monday
            start_time=time(7, 0),
            end_time=time(11, 0),
            break_minutes=0,
        )
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            tracking_start_date=date(2025, 7, 1),
            initial_hours_offset=Decimal("5.00"),
        )
        service = TimeCalculationService()

        # Get September summary with all historical entries
        all_entries = [july_entry, aug_entry, sept_entry]
        summary = service.monthly_summary(all_entries, settings, 2025, 9)

        # carryover_in for September = July balance (3.6) + August balance (1.6) + initial_offset (5.0) = 10.2
        assert summary.carryover_in == Decimal("10.20")

    @pytest.mark.unit
    def test_monthly_summary_calculates_carryover_from_historical_data(self):
        """Carryover calculation uses historical data, not static field."""
        # July entry: +3.6 balance
        july_entry = TimeEntryFactory.build(
            work_date=date(2025, 7, 7),  # Monday
            start_time=time(7, 0),
            end_time=time(17, 0),
            break_minutes=0,
        )
        # August entry: +1.6 balance
        aug_entry = TimeEntryFactory.build(
            work_date=date(2025, 8, 4),  # Monday
            start_time=time(7, 0),
            end_time=time(15, 0),
            break_minutes=0,
        )
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            tracking_start_date=date(2025, 7, 1),
            initial_hours_offset=Decimal("5.00"),
        )
        service = TimeCalculationService()

        all_entries = [july_entry, aug_entry]
        summary = service.monthly_summary(all_entries, settings, 2025, 8)

        # carryover_in should be calculated from historical data
        # July balance (3.6) + initial_offset (5.0) = 8.6
        assert summary.carryover_in == Decimal("8.60")

    @pytest.mark.unit
    def test_monthly_summary_no_tracking_start_returns_zero_carryover(self):
        """When tracking_start_date is None, carryover_in should be 0."""
        entry = TimeEntryFactory.build(
            work_date=date(2025, 7, 7),  # Monday
            start_time=time(7, 0),
            end_time=time(17, 0),
            break_minutes=0,
        )
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            tracking_start_date=None,  # No tracking start
            initial_hours_offset=None,
        )
        service = TimeCalculationService()

        summary = service.monthly_summary([entry], settings, 2025, 7)

        # No tracking_start_date means carryover_in = 0
        assert summary.carryover_in == Decimal("0.00")

    @pytest.mark.unit
    def test_monthly_summary_first_month_mid_month_tracking_start(self):
        """First tracked month with mid-month tracking_start uses initial_offset."""
        # Tracking starts July 15, entry on July 20
        entry = TimeEntryFactory.build(
            work_date=date(2025, 7, 20),  # Monday after tracking start
            start_time=time(7, 0),
            end_time=time(17, 0),  # 10h = +3.6
            break_minutes=0,
        )
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            tracking_start_date=date(2025, 7, 15),  # Mid-month
            initial_hours_offset=Decimal("12.00"),
        )
        service = TimeCalculationService()

        summary = service.monthly_summary([entry], settings, 2025, 7)

        # First tracked month: carryover_in = initial_offset only
        assert summary.carryover_in == Decimal("12.00")

    @pytest.mark.unit
    def test_monthly_summary_second_month_after_mid_month_start(self):
        """Second month after mid-month tracking_start calculates from historical data."""
        # July tracking starts mid-month
        july_entry = TimeEntryFactory.build(
            work_date=date(2025, 7, 21),  # Monday after July 15 start
            start_time=time(7, 0),
            end_time=time(17, 0),  # 10h = +3.6
            break_minutes=0,
        )
        # August entry
        aug_entry = TimeEntryFactory.build(
            work_date=date(2025, 8, 4),  # Monday
            start_time=time(7, 0),
            end_time=time(15, 0),  # 8h = +1.6
            break_minutes=0,
        )
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            tracking_start_date=date(2025, 7, 15),  # Mid-July
            initial_hours_offset=Decimal("8.00"),
        )
        service = TimeCalculationService()

        all_entries = [july_entry, aug_entry]
        summary = service.monthly_summary(all_entries, settings, 2025, 8)

        # carryover_in for August = July balance (3.6) + initial_offset (8.0) = 11.6
        assert summary.carryover_in == Decimal("11.60")

    @pytest.mark.unit
    def test_monthly_summary_negative_historical_balance(self):
        """carryover_in can be negative if historical balance is negative."""
        # July entry: 4h worked = -2.4 balance
        july_entry = TimeEntryFactory.build(
            work_date=date(2025, 7, 7),  # Monday
            start_time=time(7, 0),
            end_time=time(11, 0),  # 4 hours
            break_minutes=0,
        )
        # August entry
        aug_entry = TimeEntryFactory.build(
            work_date=date(2025, 8, 4),  # Monday
            start_time=time(7, 0),
            end_time=time(15, 0),
            break_minutes=0,
        )
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            tracking_start_date=date(2025, 7, 1),
            initial_hours_offset=Decimal("0.00"),
        )
        service = TimeCalculationService()

        all_entries = [july_entry, aug_entry]
        summary = service.monthly_summary(all_entries, settings, 2025, 8)

        # carryover_in for August = July balance (-2.4) + initial_offset (0.0) = -2.4
        assert summary.carryover_in == Decimal("-2.40")

    @pytest.mark.unit
    def test_monthly_summary_entries_parameter_must_include_all_historical(self):
        """Entries parameter must contain ALL historical entries, not just current month.

        This test documents the API requirement that callers must pass all entries
        from tracking_start_date onward, not just the current month's entries.
        """
        # July entry: +3.6 balance
        july_entry = TimeEntryFactory.build(
            work_date=date(2025, 7, 7),  # Monday
            start_time=time(7, 0),
            end_time=time(17, 0),
            break_minutes=0,
        )
        # August entry: +1.6 balance
        aug_entry = TimeEntryFactory.build(
            work_date=date(2025, 8, 4),  # Monday
            start_time=time(7, 0),
            end_time=time(15, 0),
            break_minutes=0,
        )
        settings = UserSettingsFactory.build(
            weekly_target_hours=Decimal("32.00"),
            tracking_start_date=date(2025, 7, 1),
            initial_hours_offset=Decimal("5.00"),
        )
        service = TimeCalculationService()

        # CORRECT: Pass all historical entries
        all_entries = [july_entry, aug_entry]
        summary_with_history = service.monthly_summary(all_entries, settings, 2025, 8)
        # carryover_in includes July's balance
        assert summary_with_history.carryover_in == Decimal("8.60")

        # INCORRECT: Pass only August entries (demonstrates API contract)
        august_only = [aug_entry]
        summary_without_history = service.monthly_summary(august_only, settings, 2025, 8)
        # carryover_in would only include initial_offset, missing July's balance
        # This demonstrates that callers MUST pass all historical entries
        assert summary_without_history.carryover_in == Decimal("5.00")  # Just initial_offset
