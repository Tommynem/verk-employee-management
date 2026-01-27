"""Tests for TimeEntry Pydantic schemas.

These tests verify the behavior of TimeEntry schemas following VaWW pattern:
Update -> Create -> Response

Schema Structure:
- TimeEntryUpdate: Base with all mutable fields (all optional)
- TimeEntryCreate: Adds required field work_date (inherits from Update)
- TimeEntryResponse: Adds read-only database fields and calculated fields
"""

from datetime import date, datetime, time
from decimal import Decimal

import pytest
from pydantic import ValidationError

from source.api.schemas.time_entry import TimeEntryCreate, TimeEntryResponse, TimeEntryUpdate
from source.database.enums import AbsenceType, RecordStatus
from tests.factories import TimeEntryFactory


class TestTimeEntryUpdate:
    """Tests for TimeEntryUpdate schema (base with all mutable fields)."""

    def test_all_fields_optional(self):
        """Test TimeEntryUpdate accepts empty dict (all fields optional)."""
        schema = TimeEntryUpdate()

        assert schema.start_time is None
        assert schema.end_time is None
        assert schema.break_minutes is None
        assert schema.notes is None
        assert schema.absence_type == AbsenceType.NONE  # Default

    def test_valid_update_with_times(self):
        """Test TimeEntryUpdate accepts valid time fields."""
        schema = TimeEntryUpdate(
            start_time=time(9, 0),
            end_time=time(17, 30),
            break_minutes=45,
            notes="Working on schemas",
        )

        assert schema.start_time == time(9, 0)
        assert schema.end_time == time(17, 30)
        assert schema.break_minutes == 45
        assert schema.notes == "Working on schemas"
        assert schema.absence_type == AbsenceType.NONE

    def test_break_minutes_rejects_negative(self):
        """Test break_minutes validation rejects negative values."""
        with pytest.raises(ValidationError) as exc_info:
            TimeEntryUpdate(break_minutes=-1)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("break_minutes",)
        assert errors[0]["type"] == "greater_than_equal"

    def test_break_minutes_rejects_over_limit(self):
        """Test break_minutes validation rejects values over 480 minutes (8 hours)."""
        with pytest.raises(ValidationError) as exc_info:
            TimeEntryUpdate(break_minutes=481)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("break_minutes",)
        assert errors[0]["type"] == "less_than_equal"

    def test_break_minutes_accepts_zero(self):
        """Test break_minutes accepts 0 (valid for no break)."""
        schema = TimeEntryUpdate(break_minutes=0)

        assert schema.break_minutes == 0

    def test_break_minutes_accepts_max_value(self):
        """Test break_minutes accepts 480 (8 hours max)."""
        schema = TimeEntryUpdate(break_minutes=480)

        assert schema.break_minutes == 480

    def test_notes_rejects_over_500_chars(self):
        """Test notes validation rejects strings over 500 characters."""
        long_notes = "x" * 501

        with pytest.raises(ValidationError) as exc_info:
            TimeEntryUpdate(notes=long_notes)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("notes",)
        assert errors[0]["type"] == "string_too_long"

    def test_notes_accepts_500_chars(self):
        """Test notes accepts exactly 500 characters."""
        notes = "x" * 500
        schema = TimeEntryUpdate(notes=notes)

        assert schema.notes == notes
        assert len(schema.notes) == 500

    def test_absence_type_defaults_to_none(self):
        """Test absence_type defaults to NONE (regular work day)."""
        schema = TimeEntryUpdate()

        assert schema.absence_type == AbsenceType.NONE

    def test_absence_type_accepts_vacation(self):
        """Test absence_type accepts VACATION enum value."""
        schema = TimeEntryUpdate(absence_type=AbsenceType.VACATION)

        assert schema.absence_type == AbsenceType.VACATION

    def test_absence_type_accepts_all_enum_values(self):
        """Test absence_type accepts all AbsenceType enum values."""
        for absence_type in AbsenceType:
            schema = TimeEntryUpdate(absence_type=absence_type)
            assert schema.absence_type == absence_type


class TestTimeEntryCreate:
    """Tests for TimeEntryCreate schema (adds required fields for creation)."""

    def test_requires_work_date(self):
        """Test TimeEntryCreate requires work_date field."""
        with pytest.raises(ValidationError) as exc_info:
            TimeEntryCreate()

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("work_date",)
        assert errors[0]["type"] == "missing"

    def test_valid_create_minimal(self):
        """Test TimeEntryCreate accepts minimal valid data (work_date only)."""
        schema = TimeEntryCreate(work_date=date(2026, 1, 27))

        assert schema.work_date == date(2026, 1, 27)
        assert schema.start_time is None
        assert schema.end_time is None
        assert schema.break_minutes is None
        assert schema.notes is None
        assert schema.absence_type == AbsenceType.NONE

    def test_valid_create_full(self):
        """Test TimeEntryCreate accepts all fields."""
        schema = TimeEntryCreate(
            work_date=date(2026, 1, 27),
            start_time=time(7, 0),
            end_time=time(15, 0),
            break_minutes=30,
            notes="Regular work day",
            absence_type=AbsenceType.NONE,
        )

        assert schema.work_date == date(2026, 1, 27)
        assert schema.start_time == time(7, 0)
        assert schema.end_time == time(15, 0)
        assert schema.break_minutes == 30
        assert schema.notes == "Regular work day"
        assert schema.absence_type == AbsenceType.NONE

    def test_inherits_update_validation(self):
        """Test TimeEntryCreate inherits validation from TimeEntryUpdate."""
        with pytest.raises(ValidationError) as exc_info:
            TimeEntryCreate(
                work_date=date(2026, 1, 27),
                break_minutes=-1,  # Should fail inherited validation
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("break_minutes",) for error in errors)


class TestTimeEntryResponse:
    """Tests for TimeEntryResponse schema (adds read-only database fields)."""

    def test_model_validate_from_orm(self):
        """Test TimeEntryResponse.model_validate works with ORM TimeEntry model."""
        # Build ORM instance (not persisted)
        entry = TimeEntryFactory.build(
            id=1,
            user_id=42,
            work_date=date(2026, 1, 27),
            start_time=time(7, 0),
            end_time=time(15, 0),
            break_minutes=30,
            notes="Test entry",
            absence_type=AbsenceType.NONE,
            status=RecordStatus.DRAFT,
        )

        # Should successfully convert ORM model to Pydantic schema
        schema = TimeEntryResponse.model_validate(entry)

        assert schema.id == 1
        assert schema.user_id == 42
        assert schema.work_date == date(2026, 1, 27)
        assert schema.start_time == time(7, 0)
        assert schema.end_time == time(15, 0)
        assert schema.break_minutes == 30
        assert schema.notes == "Test entry"
        assert schema.absence_type == AbsenceType.NONE
        assert schema.status == RecordStatus.DRAFT

    def test_response_includes_calculated_fields(self):
        """Test TimeEntryResponse includes calculated fields (actual_hours, target_hours, balance)."""
        # Build ORM instance
        entry = TimeEntryFactory.build(
            id=1,
            user_id=42,
            work_date=date(2026, 1, 27),
            start_time=time(7, 0),
            end_time=time(15, 0),
            break_minutes=30,
        )

        # Convert to response schema
        schema = TimeEntryResponse.model_validate(entry)

        # Should have calculated fields (actual implementation will compute these)
        # For now, just verify the attributes exist and are Decimal type
        assert hasattr(schema, "actual_hours")
        assert hasattr(schema, "target_hours")
        assert hasattr(schema, "balance")
        assert isinstance(schema.actual_hours, Decimal)
        assert isinstance(schema.target_hours, Decimal)
        assert isinstance(schema.balance, Decimal)

    def test_response_includes_timestamps(self):
        """Test TimeEntryResponse includes created_at and updated_at timestamps."""
        entry = TimeEntryFactory.build(
            id=1,
            user_id=42,
            work_date=date(2026, 1, 27),
        )

        schema = TimeEntryResponse.model_validate(entry)

        assert hasattr(schema, "created_at")
        assert hasattr(schema, "updated_at")
        assert isinstance(schema.created_at, datetime)
        assert isinstance(schema.updated_at, datetime)

    def test_response_requires_database_fields(self):
        """Test TimeEntryResponse requires database-generated fields (id, user_id, status)."""
        # Cannot construct Response directly without database fields
        with pytest.raises(ValidationError) as exc_info:
            TimeEntryResponse(work_date=date(2026, 1, 27))

        errors = exc_info.value.errors()
        # Should fail on missing required fields: id, user_id, status, created_at, updated_at
        missing_fields = {error["loc"][0] for error in errors if error["type"] == "missing"}
        assert "id" in missing_fields
        assert "user_id" in missing_fields
        assert "status" in missing_fields
