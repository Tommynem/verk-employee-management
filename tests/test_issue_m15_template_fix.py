"""Tests for ISSUE M15: Actual Hours Display for Absence Days."""

from datetime import date, time
from decimal import Decimal

from fastapi.testclient import TestClient

from source.database.enums import AbsenceType
from source.database.models import UserSettings
from tests.factories import TimeEntryFactory


class TestAbsenceDayActualHoursDisplay:
    """Test that absence days show credited hours instead of actual work hours."""

    def test_vacation_day_shows_target_hours_not_actual(self, client: TestClient, db_session):
        """ISSUE M15: Vacation day should show credited hours (8h), not work time (7.5h)."""
        # Create settings
        settings = UserSettings(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()

        # Create vacation day with existing times (08:00-16:00, 30min break = 7.5h work)
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),  # Wednesday
            start_time=time(8, 0),
            end_time=time(16, 0),
            break_minutes=30,
            absence_type=AbsenceType.VACATION,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        # Get row HTML
        response = client.get(f"/time-entries/{entry.id}/row")
        assert response.status_code == 200

        html = response.text

        # Should show target hours (8:00h), not actual hours (7:30h)
        assert "8:00h" in html  # Target hours in Actual Hours column
        assert "7:30h" not in html  # Should NOT show calculated actual hours

    def test_sick_day_shows_target_hours(self, client: TestClient, db_session):
        """Sick day should show credited hours."""
        settings = UserSettings(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()

        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            start_time=time(8, 0),
            end_time=time(16, 0),
            break_minutes=30,
            absence_type=AbsenceType.SICK,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/row")
        assert response.status_code == 200

        html = response.text
        assert "8:00h" in html
        assert "7:30h" not in html

    def test_holiday_shows_target_hours_zero(self, client: TestClient, db_session):
        """Holiday should show 0:00h (target for holidays is 0)."""
        settings = UserSettings(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()

        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            start_time=None,
            end_time=None,
            break_minutes=0,
            absence_type=AbsenceType.HOLIDAY,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/row")
        assert response.status_code == 200

        html = response.text
        # Holiday target is 0.00h
        assert "0:00h" in html

    def test_flex_time_shows_target_hours(self, client: TestClient, db_session):
        """Flex time (taking time off) should show target hours."""
        settings = UserSettings(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()

        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            start_time=None,
            end_time=None,
            break_minutes=0,
            absence_type=AbsenceType.FLEX_TIME,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/row")
        assert response.status_code == 200

        html = response.text
        assert "8:00h" in html

    def test_normal_work_day_shows_actual_hours(self, client: TestClient, db_session):
        """Normal work day (no absence) should still show actual work hours."""
        settings = UserSettings(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()

        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            start_time=time(8, 0),
            end_time=time(16, 0),
            break_minutes=30,
            absence_type=AbsenceType.NONE,  # Normal work day
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/row")
        assert response.status_code == 200

        html = response.text
        # Normal day should show actual hours (7.5h)
        assert "7:30h" in html

    def test_vacation_day_with_no_times_shows_target(self, client: TestClient, db_session):
        """Vacation day without times should show target hours."""
        settings = UserSettings(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()

        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            start_time=None,
            end_time=None,
            break_minutes=0,
            absence_type=AbsenceType.VACATION,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/row")
        assert response.status_code == 200

        html = response.text
        assert "8:00h" in html
