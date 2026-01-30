"""Test optimistic locking for race condition prevention (C11/C12).

Tests verify that concurrent edits are detected and rejected using updated_at timestamp.
Covers both TimeEntry updates (C11) and Settings updates (C12).

Issues:
- C11: Last-Write-Wins Race Condition for Time Entries
- C12: Settings Race Condition - Same pattern

TDD RED phase: Tests should fail until optimistic locking is implemented.
"""

from datetime import date, time
from decimal import Decimal

from source.database.enums import RecordStatus
from tests.factories import TimeEntryFactory, UserSettingsFactory


class TestTimeEntryOptimisticLocking:
    """Test optimistic locking for TimeEntry updates (Issue C11)."""

    def test_update_with_current_timestamp_succeeds(self, client, db_session):
        """Update with current updated_at timestamp succeeds."""
        # Create entry
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            start_time=time(8, 0),
            end_time=time(16, 0),
            break_minutes=30,
            status=RecordStatus.DRAFT,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        # Store current updated_at
        current_updated_at = entry.updated_at

        # Update with current timestamp
        response = client.patch(
            f"/time-entries/{entry.id}",
            data={
                "start_time": "09:00",
                "end_time": "17:00",
                "break_minutes": 45,
                "updated_at": current_updated_at.isoformat(),
            },
        )

        assert response.status_code == 200
        assert "09:00" in response.text
        assert "17:00" in response.text

    def test_update_with_stale_timestamp_fails_409(self, client, db_session):
        """Update with stale updated_at timestamp fails with 409 Conflict."""
        # Create entry
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            start_time=time(8, 0),
            end_time=time(16, 0),
            break_minutes=30,
            status=RecordStatus.DRAFT,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        # Store original timestamp
        original_updated_at = entry.updated_at

        # Simulate concurrent update (modify entry directly in DB)
        entry.break_minutes = 60
        db_session.commit()
        db_session.refresh(entry)

        # Attempt update with stale timestamp
        response = client.patch(
            f"/time-entries/{entry.id}",
            data={
                "start_time": "09:00",
                "end_time": "17:00",
                "break_minutes": 45,
                "updated_at": original_updated_at.isoformat(),
            },
        )

        assert response.status_code == 409
        assert "zwischenzeitlich geändert" in response.text.lower()

    def test_update_without_timestamp_fails_422(self, client, db_session):
        """Update without updated_at timestamp fails with 422 Unprocessable Entity."""
        # Create entry
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            start_time=time(8, 0),
            end_time=time(16, 0),
            status=RecordStatus.DRAFT,
        )
        db_session.add(entry)
        db_session.commit()

        # Attempt update without timestamp
        response = client.patch(
            f"/time-entries/{entry.id}",
            data={
                "start_time": "09:00",
                "end_time": "17:00",
            },
        )

        assert response.status_code == 422
        assert "updated_at" in response.text.lower() or "zeitstempel" in response.text.lower()

    def test_concurrent_updates_second_fails(self, client, db_session):
        """Simulate two concurrent updates - second update fails with 409."""
        # Create entry
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            start_time=time(8, 0),
            end_time=time(16, 0),
            break_minutes=30,
            status=RecordStatus.DRAFT,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        # Both users fetch entry at same time
        user1_timestamp = entry.updated_at
        user2_timestamp = entry.updated_at

        # User 1 updates successfully
        response1 = client.patch(
            f"/time-entries/{entry.id}",
            data={
                "break_minutes": 45,
                "updated_at": user1_timestamp.isoformat(),
            },
        )
        assert response1.status_code == 200

        # User 2 attempts update with stale timestamp
        response2 = client.patch(
            f"/time-entries/{entry.id}",
            data={
                "break_minutes": 60,
                "updated_at": user2_timestamp.isoformat(),
            },
        )
        assert response2.status_code == 409
        assert "zwischenzeitlich geändert" in response2.text.lower()

        # Verify first user's change persisted
        db_session.refresh(entry)
        assert entry.break_minutes == 45

    def test_error_message_in_german(self, client, db_session):
        """409 error message is in German."""
        # Create entry
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            start_time=time(8, 0),
            end_time=time(16, 0),
            status=RecordStatus.DRAFT,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        # Store original timestamp
        original_updated_at = entry.updated_at

        # Modify entry
        entry.break_minutes = 60
        db_session.commit()

        # Attempt update with stale timestamp
        response = client.patch(
            f"/time-entries/{entry.id}",
            data={
                "break_minutes": 45,
                "updated_at": original_updated_at.isoformat(),
            },
        )

        assert response.status_code == 409
        # Verify German error message
        assert "Dieser Eintrag wurde zwischenzeitlich geändert" in response.text
        assert "Bitte laden Sie die Seite neu" in response.text


class TestSettingsOptimisticLocking:
    """Test optimistic locking for Settings updates (Issue C12)."""

    def test_weekday_defaults_update_with_current_timestamp_succeeds(self, client, db_session):
        """Update weekday defaults with current timestamp succeeds."""
        # Create settings
        settings = UserSettingsFactory.build(
            user_id=1,
            weekly_target_hours=Decimal("40.00"),
            schedule_json={"weekday_defaults": {}},
        )
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        current_updated_at = settings.updated_at

        # Update with current timestamp
        response = client.patch(
            "/settings/weekday-defaults",
            data={
                "weekday_0_start_time": "08:00",
                "weekday_0_end_time": "16:00",
                "weekday_0_break_minutes": "30",
                "updated_at": current_updated_at.isoformat(),
            },
        )

        assert response.status_code == 200

    def test_weekday_defaults_update_with_stale_timestamp_fails_409(self, client, db_session):
        """Update weekday defaults with stale timestamp fails with 409."""
        # Create settings
        settings = UserSettingsFactory.build(
            user_id=1,
            weekly_target_hours=Decimal("40.00"),
            schedule_json={"weekday_defaults": {}},
        )
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        original_updated_at = settings.updated_at

        # Simulate concurrent update
        settings.schedule_json = {"weekday_defaults": {"0": {"start_time": "07:00"}}}
        db_session.commit()

        # Attempt update with stale timestamp
        response = client.patch(
            "/settings/weekday-defaults",
            data={
                "weekday_0_start_time": "08:00",
                "weekday_0_end_time": "16:00",
                "updated_at": original_updated_at.isoformat(),
            },
        )

        assert response.status_code == 409
        assert "zwischenzeitlich geändert" in response.text.lower()

    def test_tracking_settings_update_with_current_timestamp_succeeds(self, client, db_session):
        """Update tracking settings with current timestamp succeeds."""
        # Create settings
        settings = UserSettingsFactory.build(
            user_id=1,
            weekly_target_hours=Decimal("40.00"),
        )
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        current_updated_at = settings.updated_at

        # Update with current timestamp
        response = client.patch(
            "/settings/tracking",
            data={
                "weekly_target_hours": "38.5",
                "updated_at": current_updated_at.isoformat(),
            },
        )

        assert response.status_code == 200

    def test_tracking_settings_update_with_stale_timestamp_fails_409(self, client, db_session):
        """Update tracking settings with stale timestamp fails with 409."""
        # Create settings
        settings = UserSettingsFactory.build(
            user_id=1,
            weekly_target_hours=Decimal("40.00"),
        )
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        original_updated_at = settings.updated_at

        # Simulate concurrent update
        settings.weekly_target_hours = Decimal("35.00")
        db_session.commit()

        # Attempt update with stale timestamp
        response = client.patch(
            "/settings/tracking",
            data={
                "weekly_target_hours": "38.5",
                "updated_at": original_updated_at.isoformat(),
            },
        )

        assert response.status_code == 409
        assert "zwischenzeitlich geändert" in response.text.lower()

    def test_settings_error_message_in_german(self, client, db_session):
        """409 error message for settings is in German."""
        # Create settings
        settings = UserSettingsFactory.build(
            user_id=1,
            weekly_target_hours=Decimal("40.00"),
        )
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        original_updated_at = settings.updated_at

        # Modify settings
        settings.weekly_target_hours = Decimal("35.00")
        db_session.commit()

        # Attempt update with stale timestamp
        response = client.patch(
            "/settings/tracking",
            data={
                "weekly_target_hours": "38.5",
                "updated_at": original_updated_at.isoformat(),
            },
        )

        assert response.status_code == 409
        # Verify German error message
        assert "Einstellungen wurden zwischenzeitlich geändert" in response.text
        assert "Bitte laden Sie die Seite neu" in response.text
