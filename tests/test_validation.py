"""Tests for time entry validation rules."""

from datetime import date, time, timedelta

import pytest

from source.services.validation import VALIDATION_ERRORS, validate_time_entry
from tests.factories import TimeEntryFactory


class TestTimeEntryValidation:
    """Tests for validate_time_entry function."""

    @pytest.mark.unit
    def test_valid_entry_passes(self):
        """Valid entry data returns empty error list."""
        entry_data = {
            "user_id": 1,
            "work_date": date(2026, 1, 14),
            "start_time": time(7, 0),
            "end_time": time(15, 0),
            "break_minutes": 30,
        }
        errors = validate_time_entry(entry_data, existing_entries=[])
        assert errors == []

    @pytest.mark.unit
    def test_end_before_start_fails(self):
        """End time before start time is rejected."""
        entry_data = {
            "user_id": 1,
            "work_date": date(2026, 1, 14),
            "start_time": time(15, 0),
            "end_time": time(7, 0),  # Before start
            "break_minutes": 0,
        }
        errors = validate_time_entry(entry_data, existing_entries=[])
        assert VALIDATION_ERRORS["end_before_start"] in errors

    @pytest.mark.unit
    def test_break_exceeds_duration_fails(self):
        """Break longer than work period is rejected."""
        entry_data = {
            "user_id": 1,
            "work_date": date(2026, 1, 14),
            "start_time": time(9, 0),
            "end_time": time(10, 0),  # 1 hour
            "break_minutes": 90,  # 1.5 hours
        }
        errors = validate_time_entry(entry_data, existing_entries=[])
        assert VALIDATION_ERRORS["break_exceeds_duration"] in errors

    @pytest.mark.unit
    def test_duplicate_date_fails(self):
        """Two entries for same user and date is rejected."""
        existing = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 14))
        entry_data = {
            "user_id": 1,
            "work_date": date(2026, 1, 14),  # Same date
            "start_time": time(7, 0),
            "end_time": time(15, 0),
            "break_minutes": 0,
        }
        errors = validate_time_entry(entry_data, existing_entries=[existing])
        assert VALIDATION_ERRORS["duplicate_entry"] in errors

    @pytest.mark.unit
    def test_future_date_fails(self):
        """Future date is rejected by default."""
        future_date = date.today() + timedelta(days=7)
        entry_data = {
            "user_id": 1,
            "work_date": future_date,
            "start_time": time(7, 0),
            "end_time": time(15, 0),
            "break_minutes": 0,
        }
        errors = validate_time_entry(entry_data, existing_entries=[], allow_future=False)
        assert VALIDATION_ERRORS["future_date"] in errors

    @pytest.mark.unit
    def test_future_date_allowed(self):
        """Future date passes when allow_future=True."""
        future_date = date.today() + timedelta(days=7)
        entry_data = {
            "user_id": 1,
            "work_date": future_date,
            "start_time": time(7, 0),
            "end_time": time(15, 0),
            "break_minutes": 0,
        }
        errors = validate_time_entry(entry_data, existing_entries=[], allow_future=True)
        assert VALIDATION_ERRORS["future_date"] not in errors

    @pytest.mark.unit
    def test_missing_end_time_fails(self):
        """Start time without end time is rejected."""
        entry_data = {
            "user_id": 1,
            "work_date": date(2026, 1, 14),
            "start_time": time(7, 0),
            "end_time": None,  # Missing
            "break_minutes": 0,
        }
        errors = validate_time_entry(entry_data, existing_entries=[])
        assert VALIDATION_ERRORS["missing_end_time"] in errors

    @pytest.mark.unit
    def test_missing_start_time_fails(self):
        """End time without start time is rejected."""
        entry_data = {
            "user_id": 1,
            "work_date": date(2026, 1, 14),
            "start_time": None,  # Missing
            "end_time": time(15, 0),
            "break_minutes": 0,
        }
        errors = validate_time_entry(entry_data, existing_entries=[])
        assert VALIDATION_ERRORS["missing_start_time"] in errors
