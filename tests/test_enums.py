"""Tests for time tracking enums."""

import pytest

from source.database.enums import AbsenceType, RecordStatus


class TestAbsenceType:
    """Tests for AbsenceType enum."""

    @pytest.mark.unit
    def test_absence_type_none_value(self):
        """Test NONE absence type has correct value."""
        assert AbsenceType.NONE.value == "none"

    @pytest.mark.unit
    def test_absence_type_vacation_value(self):
        """Test VACATION absence type has correct value."""
        assert AbsenceType.VACATION.value == "vacation"

    @pytest.mark.unit
    def test_absence_type_sick_value(self):
        """Test SICK absence type has correct value."""
        assert AbsenceType.SICK.value == "sick"

    @pytest.mark.unit
    def test_absence_type_holiday_value(self):
        """Test HOLIDAY absence type has correct value."""
        assert AbsenceType.HOLIDAY.value == "holiday"

    @pytest.mark.unit
    def test_absence_type_flex_time_value(self):
        """Test FLEX_TIME absence type has correct value."""
        assert AbsenceType.FLEX_TIME.value == "flex_time"


class TestRecordStatus:
    """Tests for RecordStatus enum."""

    @pytest.mark.unit
    def test_record_status_draft_value(self):
        """Test DRAFT status has correct value."""
        assert RecordStatus.DRAFT.value == "draft"

    @pytest.mark.unit
    def test_record_status_submitted_value(self):
        """Test SUBMITTED status has correct value."""
        assert RecordStatus.SUBMITTED.value == "submitted"
