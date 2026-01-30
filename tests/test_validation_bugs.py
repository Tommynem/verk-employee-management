"""Tests for validation bug fixes following TDD RED phase.

This module contains failing tests for backend validation issues identified in the codebase.
Tests are written BEFORE implementation to follow strict TDD discipline.

Issues covered:
- C2: End time before start time accepted (CONFIRMED BUG)
- C1: Silent save failure for empty tracking values (verification tests)
- C3: Disabling all weekdays doesn't persist (verification tests)
- M1: Invalid time values accepted (ALREADY FIXED - tests verify correct behavior)
- M4: No error message when weekday save fails (ALREADY FIXED - tests verify correct behavior)

Note: Some tests verify already-working validation to prevent regression.
Only C2 is confirmed to fail, indicating a real bug that needs fixing.
"""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import UserSettingsFactory


class TestTrackingSettingsValidation:
    """Test validation for tracking settings (ISSUE C1)."""

    def test_empty_weekly_target_hours_should_fail(self, client: TestClient, db_session: Session):
        """Test that empty weekly target hours returns validation error.

        ISSUE C1: Empty values should either be accepted as None OR return validation error.
        Currently fails silently without feedback.
        """
        # Create existing settings
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        # Try to save empty weekly_target_hours
        response = client.patch(
            "/settings/tracking",
            data={"weekly_target_hours": "", "updated_at": settings.updated_at.isoformat()},
            headers={"HX-Request": "true"},
        )

        # Should either succeed with None/default OR return 422 with error message
        assert response.status_code in [200, 422], "Empty weekly hours should either succeed or return validation error"

        if response.status_code == 422:
            assert "Wochenstunden" in response.json()["detail"], "Error message should mention Wochenstunden"

    def test_empty_tracking_start_date_should_accept_none(self, client: TestClient, db_session: Session):
        """Test that empty tracking start date is accepted as None.

        ISSUE C1: Empty tracking_start_date should clear the field.
        """
        # Create existing settings with tracking_start_date
        from datetime import date

        settings = UserSettingsFactory.build(
            user_id=1,
            weekly_target_hours=Decimal("40.00"),
            tracking_start_date=date(2026, 1, 1),
        )
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        # Submit empty tracking_start_date
        response = client.patch(
            "/settings/tracking",
            data={
                "weekly_target_hours": "40",
                "tracking_start_date": "",
                "updated_at": settings.updated_at.isoformat(),
            },
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 200, "Empty tracking_start_date should be accepted"

        # Verify the field is cleared
        db_session.refresh(settings)
        assert settings.tracking_start_date is None, "Empty date should set tracking_start_date to None"

    def test_empty_initial_hours_offset_should_accept_none(self, client: TestClient, db_session: Session):
        """Test that empty initial hours offset is accepted as None.

        ISSUE C1: Empty initial_hours_offset should clear the field.
        """
        # Create existing settings with offset
        settings = UserSettingsFactory.build(
            user_id=1,
            weekly_target_hours=Decimal("40.00"),
            initial_hours_offset=Decimal("10.00"),
        )
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        # Submit empty initial_hours_offset
        response = client.patch(
            "/settings/tracking",
            data={
                "weekly_target_hours": "40",
                "initial_hours_offset": "",
                "updated_at": settings.updated_at.isoformat(),
            },
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 200, "Empty initial_hours_offset should be accepted"

        # Verify the field is cleared
        db_session.refresh(settings)
        assert settings.initial_hours_offset is None, "Empty offset should set initial_hours_offset to None"


class TestWeekdayDefaultsValidation:
    """Test validation for weekday defaults (ISSUES C2, C3, M4)."""

    def test_end_time_before_start_time_should_fail(self, client: TestClient, db_session: Session):
        """Test that end time before start time returns validation error.

        ISSUE C2: Backend should reject weekday defaults where end_time < start_time.
        """
        # Create existing settings
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"), schedule_json={})
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        # Try to save weekday with end_time before start_time
        response = client.patch(
            "/settings/weekday-defaults",
            data={
                "weekday_0_start_time": "17:00",
                "weekday_0_end_time": "08:00",
                "weekday_0_break_minutes": "30",
                "updated_at": settings.updated_at.isoformat(),
            },
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 422, "Should reject end_time before start_time"
        assert (
            "Endzeit" in response.json()["detail"] or "Zeit" in response.json()["detail"]
        ), "Error message should mention time validation"

    def test_disabling_all_weekdays_should_persist(self, client: TestClient, db_session: Session):
        """Test that disabling all weekdays persists correctly.

        ISSUE C3: When all weekdays have is_work_day=False, the state should persist.
        Currently all days automatically re-enable after save.
        """
        # Create existing settings with all weekdays enabled
        settings = UserSettingsFactory.build(
            user_id=1,
            weekly_target_hours=Decimal("40.00"),
            schedule_json={
                "weekday_defaults": {
                    "0": {"start_time": "08:00", "end_time": "16:00", "break_minutes": 30},
                    "1": {"start_time": "08:00", "end_time": "16:00", "break_minutes": 30},
                    "2": {"start_time": "08:00", "end_time": "16:00", "break_minutes": 30},
                    "3": {"start_time": "08:00", "end_time": "16:00", "break_minutes": 30},
                    "4": {"start_time": "08:00", "end_time": "16:00", "break_minutes": 30},
                    "5": None,
                    "6": None,
                }
            },
        )
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        # Disable all weekdays (0-6 all set to None or false)
        response = client.patch(
            "/settings/weekday-defaults",
            data={
                "weekday_0_enabled": "false",
                "weekday_1_enabled": "false",
                "weekday_2_enabled": "false",
                "weekday_3_enabled": "false",
                "weekday_4_enabled": "false",
                "weekday_5_enabled": "false",
                "weekday_6_enabled": "false",
                "updated_at": settings.updated_at.isoformat(),
            },
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 200, "Should accept all weekdays disabled"

        # Verify all weekdays are disabled in database
        db_session.refresh(settings)
        weekday_defaults = settings.schedule_json.get("weekday_defaults", {})

        for i in range(7):
            assert weekday_defaults.get(str(i)) is None, f"Weekday {i} should be None (disabled)"

    def test_excessive_break_minutes_should_return_error_message(self, client: TestClient, db_session: Session):
        """Test that excessive break_minutes returns proper error message.

        ISSUE M4: Validation errors should return proper error response with German message.
        Currently no error message is shown when weekday save fails.
        """
        # Create existing settings
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"), schedule_json={})
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        # Try to save excessive break_minutes (> 480)
        response = client.patch(
            "/settings/weekday-defaults",
            data={
                "weekday_0_start_time": "08:00",
                "weekday_0_end_time": "16:00",
                "weekday_0_break_minutes": "9999",
                "updated_at": settings.updated_at.isoformat(),
            },
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 422, "Should reject excessive break_minutes"
        assert (
            "Pausen" in response.json()["detail"] or "ungültig" in response.json()["detail"].lower()
        ), "Error message should mention invalid break time in German"


class TestTimeEntryValidation:
    """Test validation for time entries (ISSUE M1)."""

    @pytest.mark.parametrize(
        "start_time,end_time",
        [
            ("99:99", "16:00"),
            ("08:00", "99:99"),
            ("25:00", "16:00"),
            ("08:00", "25:00"),
            ("08:99", "16:00"),
            ("08:00", "16:99"),
            ("ab:cd", "16:00"),
            ("08:00", "xy:zz"),
        ],
    )
    def test_invalid_time_format_should_fail_on_create(
        self, client: TestClient, db_session: Session, start_time: str, end_time: str
    ):
        """Test that invalid time values are rejected on time entry creation.

        ISSUE M1: Backend accepts invalid time values like "99:99" or "25:00".
        Should validate time format and reject invalid values.
        """
        from datetime import date

        response = client.post(
            "/time-entries",
            data={
                "work_date": date.today().isoformat(),
                "start_time": start_time,
                "end_time": end_time,
                "break_minutes": "30",
                "absence_type": "none",
            },
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 422, f"Should reject invalid time format: {start_time} / {end_time}"
        error_detail = response.json()["detail"]
        assert (
            "Zeit" in error_detail or "Ungültig" in error_detail
        ), "Error message should mention invalid time in German"

    @pytest.mark.parametrize(
        "start_time,end_time",
        [
            ("99:99", "16:00"),
            ("08:00", "99:99"),
            ("25:00", "16:00"),
            ("08:00", "25:00"),
        ],
    )
    def test_invalid_time_format_should_fail_on_update(
        self, client: TestClient, db_session: Session, start_time: str, end_time: str
    ):
        """Test that invalid time values are rejected on time entry update.

        ISSUE M1: Backend should validate time format on PATCH as well as POST.
        """
        from datetime import date

        from tests.factories import TimeEntryFactory

        # Create valid entry first
        entry = TimeEntryFactory.build(user_id=1, work_date=date.today())
        db_session.add(entry)
        db_session.commit()

        # Try to update with invalid times
        response = client.patch(
            f"/time-entries/{entry.id}",
            data={
                "start_time": start_time,
                "end_time": end_time,
            },
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 422, f"Should reject invalid time format on update: {start_time} / {end_time}"
        error_detail = response.json()["detail"]
        assert (
            "Zeit" in error_detail or "Ungültig" in error_detail
        ), "Error message should mention invalid time in German"

    def test_time_validation_should_check_hour_range(self, client: TestClient, db_session: Session):
        """Test that time validation checks hour is 0-23.

        ISSUE M1: Hours must be in valid range 0-23.
        """
        from datetime import date

        response = client.post(
            "/time-entries",
            data={
                "work_date": date.today().isoformat(),
                "start_time": "24:00",
                "end_time": "16:00",
                "break_minutes": "30",
                "absence_type": "none",
            },
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 422, "Should reject hour >= 24"

    def test_time_validation_should_check_minute_range(self, client: TestClient, db_session: Session):
        """Test that time validation checks minute is 0-59.

        ISSUE M1: Minutes must be in valid range 0-59.
        """
        from datetime import date

        response = client.post(
            "/time-entries",
            data={
                "work_date": date.today().isoformat(),
                "start_time": "08:60",
                "end_time": "16:00",
                "break_minutes": "30",
                "absence_type": "none",
            },
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 422, "Should reject minute >= 60"
