"""Tests for break_minutes bug on non-working days.

BUG: When adding weekend days or national holidays (non-working days with 0 working hours),
the system incorrectly inserts 30 minutes of break time. The default should be 0 for
non-working days.

Root cause: source/api/routers/time_entries.py lines 411-428
- default_break_minutes always defaults to 30
- When day_defaults is None (non-workday), it stays at 30 instead of becoming 0

These tests verify that the /time-entries/new-row endpoint returns 0 break_minutes for:
1. Weekend days (Saturday/Sunday when configured as None/disabled)
2. German public holidays
3. Explicitly disabled weekdays in user settings

The endpoint tested is GET /time-entries/new-row which is used by the inline row editor.
"""

from datetime import date

from source.core.holidays import get_german_holidays
from tests.factories import UserSettingsFactory


class TestBreakMinutesNonWorkingDays:
    """Test break_minutes defaults to 0 for non-working days."""

    def test_saturday_returns_zero_break_minutes(self, client, db_session):
        """Saturday (weekend) should have 0 break_minutes default when disabled."""
        # Setup: Configure weekday defaults with Saturday (weekday=5) as None (disabled)
        settings = UserSettingsFactory.build(
            user_id=1,
            schedule_json={
                "weekday_defaults": {
                    "0": {"start_time": "08:00", "end_time": "16:00", "break_minutes": 30},  # Monday
                    "1": {"start_time": "08:00", "end_time": "16:00", "break_minutes": 30},  # Tuesday
                    "2": {"start_time": "08:00", "end_time": "16:00", "break_minutes": 30},  # Wednesday
                    "3": {"start_time": "08:00", "end_time": "16:00", "break_minutes": 30},  # Thursday
                    "4": {"start_time": "08:00", "end_time": "16:00", "break_minutes": 30},  # Friday
                    "5": None,  # Saturday - disabled
                    "6": None,  # Sunday - disabled
                }
            },
        )
        db_session.add(settings)
        db_session.commit()

        # Saturday, 2026-01-31
        saturday = date(2026, 1, 31)
        assert saturday.weekday() == 5  # Verify it's actually Saturday

        # Call: GET /time-entries/new-row with Saturday date
        response = client.get(f"/time-entries/new-row?date={saturday.isoformat()}")

        assert response.status_code == 200
        # Assert: break_minutes input should have value="0" (not value="30")
        assert 'name="break_minutes"' in response.text
        # The bug would show value="30", correct behavior is value="0"
        assert 'value="0"' in response.text, "Saturday should default to 0 break minutes"
        assert 'value="30"' not in response.text, "Saturday should NOT have 30 minute break default"

    def test_sunday_returns_zero_break_minutes(self, client, db_session):
        """Sunday (weekend) should have 0 break_minutes default when disabled."""
        # Setup: Configure weekday defaults with Sunday (weekday=6) as None (disabled)
        settings = UserSettingsFactory.build(
            user_id=1,
            schedule_json={
                "weekday_defaults": {
                    "0": {"start_time": "08:00", "end_time": "16:00", "break_minutes": 30},
                    "1": {"start_time": "08:00", "end_time": "16:00", "break_minutes": 30},
                    "2": {"start_time": "08:00", "end_time": "16:00", "break_minutes": 30},
                    "3": {"start_time": "08:00", "end_time": "16:00", "break_minutes": 30},
                    "4": {"start_time": "08:00", "end_time": "16:00", "break_minutes": 30},
                    "5": None,  # Saturday - disabled
                    "6": None,  # Sunday - disabled
                }
            },
        )
        db_session.add(settings)
        db_session.commit()

        # Sunday, 2026-02-01
        sunday = date(2026, 2, 1)
        assert sunday.weekday() == 6  # Verify it's actually Sunday

        # Call: GET /time-entries/new-row with Sunday date
        response = client.get(f"/time-entries/new-row?date={sunday.isoformat()}")

        assert response.status_code == 200
        # Assert: break_minutes input should have value="0"
        assert 'name="break_minutes"' in response.text
        assert 'value="0"' in response.text, "Sunday should default to 0 break minutes"
        assert 'value="30"' not in response.text, "Sunday should NOT have 30 minute break default"

    def test_german_holiday_returns_zero_break_minutes(self, client, db_session):
        """German public holidays should have 0 break_minutes default."""
        # Setup: Configure all weekdays as working days (Mon-Fri enabled, Sat-Sun disabled)
        settings = UserSettingsFactory.build(
            user_id=1,
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

        # Use Tag der Deutschen Einheit (October 3) - always a German holiday
        holiday = date(2026, 10, 3)
        # Verify it's actually a German holiday
        german_holidays = get_german_holidays(2026)
        assert holiday in german_holidays, "2026-10-03 should be German Unity Day"

        # Call: GET /time-entries/new-row with holiday date
        response = client.get(f"/time-entries/new-row?date={holiday.isoformat()}")

        assert response.status_code == 200
        # Assert: break_minutes should be 0 for public holidays
        # NOTE: Current implementation may not check for holidays - this test will fail
        # until holiday detection is added to new_entry_row
        assert 'name="break_minutes"' in response.text
        assert 'value="0"' in response.text, "German holiday should default to 0 break minutes"
        assert 'value="30"' not in response.text, "German holiday should NOT have 30 minute break default"

    def test_disabled_weekday_returns_zero_break_minutes(self, client, db_session):
        """Explicitly disabled weekday should have 0 break_minutes default."""
        # Setup: Configure Wednesday (weekday=2) as disabled (None)
        settings = UserSettingsFactory.build(
            user_id=1,
            schedule_json={
                "weekday_defaults": {
                    "0": {"start_time": "08:00", "end_time": "16:00", "break_minutes": 30},
                    "1": {"start_time": "08:00", "end_time": "16:00", "break_minutes": 30},
                    "2": None,  # Wednesday - explicitly disabled
                    "3": {"start_time": "08:00", "end_time": "16:00", "break_minutes": 30},
                    "4": {"start_time": "08:00", "end_time": "16:00", "break_minutes": 30},
                    "5": None,
                    "6": None,
                }
            },
        )
        db_session.add(settings)
        db_session.commit()

        # Wednesday, 2026-01-28
        wednesday = date(2026, 1, 28)
        assert wednesday.weekday() == 2  # Verify it's actually Wednesday

        # Call: GET /time-entries/new-row with disabled Wednesday
        response = client.get(f"/time-entries/new-row?date={wednesday.isoformat()}")

        assert response.status_code == 200
        # Assert: break_minutes should be 0 for disabled weekdays
        assert 'name="break_minutes"' in response.text
        assert 'value="0"' in response.text, "Disabled weekday should default to 0 break minutes"
        assert 'value="30"' not in response.text, "Disabled weekday should NOT have 30 minute break default"

    def test_enabled_weekday_returns_configured_break_minutes(self, client, db_session):
        """Enabled workday should use configured break_minutes (regression test)."""
        # Setup: Configure Monday with 45 minute break
        settings = UserSettingsFactory.build(
            user_id=1,
            schedule_json={
                "weekday_defaults": {
                    "0": {"start_time": "08:00", "end_time": "17:00", "break_minutes": 45},  # Monday - 45 min break
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

        # Monday, 2026-02-02
        monday = date(2026, 2, 2)
        assert monday.weekday() == 0  # Verify it's actually Monday

        # Call: GET /time-entries/new-row with Monday date
        response = client.get(f"/time-entries/new-row?date={monday.isoformat()}")

        assert response.status_code == 200
        # Assert: break_minutes should use configured value (45)
        assert 'name="break_minutes"' in response.text
        assert 'value="45"' in response.text, "Enabled Monday should use configured 45 minute break"
        assert 'value="0"' not in response.text, "Enabled workday should NOT default to 0"

    def test_no_settings_defaults_to_30_break_minutes(self, client, db_session):
        """When no user settings exist, should default to 30 break_minutes (existing behavior)."""
        # No settings created - db_session is empty

        # Monday, 2026-02-02
        monday = date(2026, 2, 2)

        # Call: GET /time-entries/new-row without user settings
        response = client.get(f"/time-entries/new-row?date={monday.isoformat()}")

        assert response.status_code == 200
        # Assert: should fall back to default 30 minutes
        assert 'name="break_minutes"' in response.text
        assert 'value="30"' in response.text, "No settings should default to 30 minute break"
