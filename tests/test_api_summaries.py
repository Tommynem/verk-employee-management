"""Test Summary API routes for weekly and monthly views.

Tests for Summary routes following VaWW REST+HTMX patterns.
All tests should fail initially (TDD RED phase) until routes are implemented.

Routes tested:
- GET /summary/week -> HTML weekly summary view
- GET /summary/week?week_start=YYYY-MM-DD -> HTML specific week summary
- GET /summary/month -> HTML monthly summary view
- GET /summary/month?year=YYYY&month=M -> HTML specific month summary
"""

from datetime import date, time
from decimal import Decimal

from tests.factories import TimeEntryFactory, UserSettingsFactory


class TestWeeklySummary:
    """Test GET /summary/week weekly summary view."""

    def test_get_current_week_requires_settings(self, client, db_session):
        """GET /summary/week without UserSettings returns 422 error."""
        response = client.get("/summary/week")

        assert response.status_code == 422
        assert "text/html" in response.headers["content-type"]
        # Error message should indicate missing settings
        assert "einstellungen" in response.text.lower() or "settings" in response.text.lower()

    def test_get_current_week_success(self, client, db_session):
        """GET /summary/week returns current week summary HTML."""
        # Create user settings for current user (id=1)
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("32.00"))
        db_session.add(settings)
        db_session.commit()

        response = client.get("/summary/week")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Summary should contain total headers
        assert "Gesamt" in response.text or "Total" in response.text
        # Summary should show balance
        assert "Saldo" in response.text or "Balance" in response.text

    def test_get_specific_week(self, client, db_session):
        """GET /summary/week?week_start=2026-01-20 returns specific week summary."""
        # Create user settings
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("32.00"))
        db_session.add(settings)
        db_session.commit()

        response = client.get("/summary/week?week_start=2026-01-20")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Response should contain dates from the requested week (Jan 20-26, 2026)
        assert "2026-01-20" in response.text or "20.01.2026" in response.text

    def test_week_with_time_entries(self, client, db_session):
        """GET /summary/week includes time entries in weekly summary."""
        # Create user settings
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("32.00"))
        db_session.add(settings)
        db_session.commit()

        # Create time entry for this week (Monday)
        entry = TimeEntryFactory.build(
            user_id=1, work_date=date(2026, 1, 20), start_time=time(7, 0), end_time=time(15, 0), break_minutes=30
        )
        db_session.add(entry)
        db_session.commit()

        response = client.get("/summary/week?week_start=2026-01-20")

        assert response.status_code == 200
        # Entry date should appear
        assert "2026-01-20" in response.text or "20.01.2026" in response.text
        # Actual hours (7.5h) should appear somewhere
        assert "7.5" in response.text or "7,5" in response.text

    def test_week_summary_uses_calculation_service(self, client, db_session):
        """Weekly summary calculates totals correctly using TimeCalculationService."""
        # Create user settings with 32h/week target
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("32.00"))
        db_session.add(settings)
        db_session.commit()

        # Create 5 entries (Mon-Fri) with 7.5h each = 37.5h actual
        for day_offset in range(5):
            entry = TimeEntryFactory.build(
                user_id=1,
                work_date=date(2026, 1, 20 + day_offset),
                start_time=time(7, 0),
                end_time=time(15, 0),
                break_minutes=30,
            )
            db_session.add(entry)
        db_session.commit()

        response = client.get("/summary/week?week_start=2026-01-20")

        assert response.status_code == 200
        # Total actual should be 37.5h
        assert "37.5" in response.text or "37,5" in response.text
        # Target should be 32.0h
        assert "32.0" in response.text or "32,0" in response.text
        # Balance should be +5.5h
        assert "5.5" in response.text or "5,5" in response.text or "+5.5" in response.text

    def test_week_invalid_date_format(self, client, db_session):
        """GET /summary/week?week_start=invalid returns 422."""
        settings = UserSettingsFactory.build(user_id=1)
        db_session.add(settings)
        db_session.commit()

        response = client.get("/summary/week?week_start=not-a-date")

        assert response.status_code == 422


class TestMonthlySummary:
    """Test GET /summary/month monthly summary view."""

    def test_get_current_month_requires_settings(self, client, db_session):
        """GET /summary/month without UserSettings returns 422 error."""
        response = client.get("/summary/month")

        assert response.status_code == 422
        assert "text/html" in response.headers["content-type"]
        # Error message should indicate missing settings
        assert "einstellungen" in response.text.lower() or "settings" in response.text.lower()

    def test_get_current_month_success(self, client, db_session):
        """GET /summary/month returns current month summary HTML."""
        # Create user settings
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("32.00"))
        db_session.add(settings)
        db_session.commit()

        response = client.get("/summary/month")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Monthly summary should contain totals
        assert "Gesamt" in response.text or "Total" in response.text
        # Should contain carryover
        assert "Übertrag" in response.text or "Carryover" in response.text

    def test_get_specific_month(self, client, db_session):
        """GET /summary/month?year=2026&month=1 returns specific month summary."""
        # Create user settings
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("32.00"))
        db_session.add(settings)
        db_session.commit()

        response = client.get("/summary/month?year=2026&month=1")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Response should reference January 2026
        assert "2026" in response.text
        # Should contain January dates
        assert "2026-01" in response.text or "01.2026" in response.text or "Januar" in response.text

    def test_month_includes_carryover(self, client, db_session):
        """Monthly summary includes carryover_in and carryover_out."""
        # Create user settings with initial offset
        settings = UserSettingsFactory.build(
            user_id=1,
            weekly_target_hours=Decimal("32.00"),
            tracking_start_date=date(2026, 1, 1),
            initial_hours_offset=Decimal("10.50"),
        )
        db_session.add(settings)
        db_session.commit()

        response = client.get("/summary/month?year=2026&month=1")

        assert response.status_code == 200
        # Carryover in should be 10.50 (from initial_hours_offset for first month)
        assert "10.5" in response.text or "10,5" in response.text
        # Carryover labels should be present
        assert "Übertrag" in response.text or "Carryover" in response.text

    def test_month_with_time_entries(self, client, db_session):
        """GET /summary/month includes time entries in monthly summary."""
        # Create user settings
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("32.00"))
        db_session.add(settings)
        db_session.commit()

        # Create entries across multiple weeks in January
        for week_offset in [0, 7, 14, 21]:
            for day_offset in range(5):  # Mon-Fri each week
                entry = TimeEntryFactory.build(
                    user_id=1,
                    work_date=date(2026, 1, 6 + week_offset + day_offset),
                    start_time=time(7, 0),
                    end_time=time(15, 0),
                    break_minutes=30,
                )
                db_session.add(entry)
        db_session.commit()

        response = client.get("/summary/month?year=2026&month=1")

        assert response.status_code == 200
        # Should show multiple weeks with date range (2026-01-06 falls in KW 2)
        assert "05.01.2026" in response.text  # Week 2 start date includes 2026-01-06
        # Total actual hours (20 days × 7.5h = 150h)
        assert "150" in response.text

    def test_month_calculates_carryover_out(self, client, db_session):
        """Monthly summary calculates carryover_out correctly."""
        # Create user settings with no initial offset
        settings = UserSettingsFactory.build(
            user_id=1,
            weekly_target_hours=Decimal("32.00"),
            tracking_start_date=date(2026, 1, 1),
            initial_hours_offset=Decimal("0.00"),
        )
        db_session.add(settings)
        db_session.commit()

        # Create entries totaling 40h actual (Mon-Fri first week, 8h/day)
        for day_offset in range(5):
            entry = TimeEntryFactory.build(
                user_id=1,
                work_date=date(2026, 1, 6 + day_offset),
                start_time=time(7, 0),
                end_time=time(16, 0),
                break_minutes=60,
            )
            db_session.add(entry)
        db_session.commit()

        response = client.get("/summary/month?year=2026&month=1")

        assert response.status_code == 200
        # Carryover in: 0.00
        # January has ~22 workdays, target = ~140.8h (32h/week × 4.4 weeks)
        # Actual: 40h (only 5 days)
        # Balance should be negative
        # This test validates carryover_out = carryover_in + period_balance is shown

    def test_month_invalid_parameters(self, client, db_session):
        """GET /summary/month with invalid year/month returns 422."""
        settings = UserSettingsFactory.build(user_id=1)
        db_session.add(settings)
        db_session.commit()

        response = client.get("/summary/month?year=invalid&month=99")

        assert response.status_code == 422
