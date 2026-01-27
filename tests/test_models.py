"""Tests for SQLAlchemy models."""

from datetime import date, time
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from source.database.enums import AbsenceType, RecordStatus
from source.database.models import TimeEntry, UserSettings


class TestTimeEntryModel:
    """Tests for TimeEntry model."""

    @pytest.mark.database
    def test_create_time_entry_minimal(self, db_session):
        """Test creating time entry with required fields only."""
        entry = TimeEntry(
            user_id=1,
            work_date=date(2026, 1, 27),
            status=RecordStatus.DRAFT,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        assert entry.id is not None
        assert entry.user_id == 1
        assert entry.work_date == date(2026, 1, 27)
        assert entry.status == RecordStatus.DRAFT
        assert entry.absence_type == AbsenceType.NONE  # Default
        assert entry.break_minutes == 0  # Default
        assert entry.start_time is None
        assert entry.end_time is None
        assert entry.notes is None

    @pytest.mark.database
    def test_create_time_entry_full(self, db_session):
        """Test creating time entry with all fields."""
        entry = TimeEntry(
            user_id=1,
            work_date=date(2026, 1, 27),
            start_time=time(9, 0),
            end_time=time(17, 30),
            break_minutes=45,
            notes="Worked on time tracking feature",
            absence_type=AbsenceType.NONE,
            status=RecordStatus.DRAFT,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        assert entry.id is not None
        assert entry.user_id == 1
        assert entry.work_date == date(2026, 1, 27)
        assert entry.start_time == time(9, 0)
        assert entry.end_time == time(17, 30)
        assert entry.break_minutes == 45
        assert entry.notes == "Worked on time tracking feature"
        assert entry.absence_type == AbsenceType.NONE
        assert entry.status == RecordStatus.DRAFT

    @pytest.mark.database
    def test_time_entry_has_created_at(self, db_session):
        """Test time entry gets created_at timestamp."""
        entry = TimeEntry(
            user_id=1,
            work_date=date(2026, 1, 27),
            status=RecordStatus.DRAFT,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        assert entry.created_at is not None
        assert isinstance(entry.created_at, type(entry.created_at))

    @pytest.mark.database
    def test_time_entry_has_updated_at(self, db_session):
        """Test time entry gets updated_at timestamp."""
        entry = TimeEntry(
            user_id=1,
            work_date=date(2026, 1, 27),
            status=RecordStatus.DRAFT,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        assert entry.updated_at is not None
        assert isinstance(entry.updated_at, type(entry.updated_at))

    @pytest.mark.database
    def test_time_entry_unique_constraint_user_date(self, db_session):
        """Test unique constraint prevents duplicate user_id + work_date."""
        entry1 = TimeEntry(
            user_id=1,
            work_date=date(2026, 1, 27),
            status=RecordStatus.DRAFT,
        )
        db_session.add(entry1)
        db_session.commit()

        entry2 = TimeEntry(
            user_id=1,
            work_date=date(2026, 1, 27),
            status=RecordStatus.DRAFT,
        )
        db_session.add(entry2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    @pytest.mark.database
    def test_time_entry_allows_same_date_different_user(self, db_session):
        """Test same date allowed for different users."""
        entry1 = TimeEntry(
            user_id=1,
            work_date=date(2026, 1, 27),
            status=RecordStatus.DRAFT,
        )
        db_session.add(entry1)
        db_session.commit()

        entry2 = TimeEntry(
            user_id=2,
            work_date=date(2026, 1, 27),
            status=RecordStatus.DRAFT,
        )
        db_session.add(entry2)
        db_session.commit()
        db_session.refresh(entry2)

        assert entry2.id is not None
        assert entry2.user_id == 2

    @pytest.mark.database
    def test_time_entry_vacation_nullable_times(self, db_session):
        """Test vacation entry doesn't require start/end times."""
        entry = TimeEntry(
            user_id=1,
            work_date=date(2026, 1, 27),
            absence_type=AbsenceType.VACATION,
            status=RecordStatus.DRAFT,
            start_time=None,
            end_time=None,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        assert entry.id is not None
        assert entry.absence_type == AbsenceType.VACATION
        assert entry.start_time is None
        assert entry.end_time is None


class TestUserSettingsModel:
    """Tests for UserSettings model."""

    @pytest.mark.database
    def test_create_user_settings_minimal(self, db_session):
        """Test creating user settings with required fields."""
        settings = UserSettings(
            user_id=1,
            weekly_target_hours=Decimal("32.00"),
        )
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        assert settings.id is not None
        assert settings.user_id == 1
        assert settings.weekly_target_hours == Decimal("32.00")
        assert settings.carryover_hours is None
        assert settings.schedule_json is None

    @pytest.mark.database
    def test_create_user_settings_with_carryover(self, db_session):
        """Test creating user settings with carryover hours."""
        settings = UserSettings(
            user_id=1,
            weekly_target_hours=Decimal("40.00"),
            carryover_hours=Decimal("15.50"),
        )
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        assert settings.id is not None
        assert settings.user_id == 1
        assert settings.weekly_target_hours == Decimal("40.00")
        assert settings.carryover_hours == Decimal("15.50")

    @pytest.mark.database
    def test_create_user_settings_with_schedule(self, db_session):
        """Test creating user settings with JSON schedule."""
        schedule = {
            "monday": {"start": "07:00", "end": "15:00"},
            "tuesday": {"start": "07:00", "end": "15:00"},
            "wednesday": {"start": "07:00", "end": "15:00"},
        }
        settings = UserSettings(
            user_id=1,
            weekly_target_hours=Decimal("32.00"),
            schedule_json=schedule,
        )
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        assert settings.id is not None
        assert settings.schedule_json is not None
        assert settings.schedule_json["monday"]["start"] == "07:00"
        assert settings.schedule_json["monday"]["end"] == "15:00"
        assert settings.schedule_json["tuesday"]["start"] == "07:00"

    @pytest.mark.database
    def test_user_settings_unique_user_id(self, db_session):
        """Test user_id must be unique."""
        settings1 = UserSettings(
            user_id=1,
            weekly_target_hours=Decimal("40.00"),
        )
        db_session.add(settings1)
        db_session.commit()

        settings2 = UserSettings(
            user_id=1,
            weekly_target_hours=Decimal("32.00"),
        )
        db_session.add(settings2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    @pytest.mark.database
    def test_user_settings_carryover_default_none(self, db_session):
        """Test carryover_hours defaults to None."""
        settings = UserSettings(
            user_id=1,
            weekly_target_hours=Decimal("40.00"),
        )
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        assert settings.carryover_hours is None

    @pytest.mark.database
    def test_user_settings_timestamps(self, db_session):
        """Test user settings gets timestamps."""
        settings = UserSettings(
            user_id=1,
            weekly_target_hours=Decimal("40.00"),
        )
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        assert settings.created_at is not None
        assert settings.updated_at is not None
        assert isinstance(settings.created_at, type(settings.created_at))
        assert isinstance(settings.updated_at, type(settings.updated_at))
