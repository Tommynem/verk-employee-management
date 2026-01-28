"""Tests for data transfer objects.

This module tests the DTOs used in import/export operations:
- TimeEntryRow: Format-agnostic row representation
- ValidationError: Error with location information
- ImportResult: Result of import operation
- ExportResult: Result of export operation
"""

from datetime import date, time

from source.services.data_transfer.dataclasses import (
    ExportResult,
    ImportResult,
    TimeEntryRow,
    ValidationError,
)
from tests.factories import TimeEntryFactory


class TestTimeEntryRow:
    """Tests for TimeEntryRow dataclass."""

    def test_create_with_required_fields(self):
        """Test creating TimeEntryRow with only required fields."""
        row = TimeEntryRow(work_date=date(2026, 1, 28))

        assert row.work_date == date(2026, 1, 28)
        assert row.start_time is None
        assert row.end_time is None
        assert row.break_minutes == 0
        assert row.absence_type == "none"
        assert row.notes is None

    def test_create_with_all_fields(self):
        """Test creating TimeEntryRow with all fields specified."""
        row = TimeEntryRow(
            work_date=date(2026, 1, 28),
            start_time=time(8, 0),
            end_time=time(16, 30),
            break_minutes=30,
            absence_type="vacation",
            notes="Approved vacation",
        )

        assert row.work_date == date(2026, 1, 28)
        assert row.start_time == time(8, 0)
        assert row.end_time == time(16, 30)
        assert row.break_minutes == 30
        assert row.absence_type == "vacation"
        assert row.notes == "Approved vacation"

    def test_create_work_entry(self):
        """Test creating TimeEntryRow for regular work day."""
        row = TimeEntryRow(
            work_date=date(2026, 1, 28),
            start_time=time(7, 0),
            end_time=time(15, 0),
            break_minutes=30,
        )

        assert row.work_date == date(2026, 1, 28)
        assert row.start_time == time(7, 0)
        assert row.end_time == time(15, 0)
        assert row.break_minutes == 30
        assert row.absence_type == "none"

    def test_create_absence_entry(self):
        """Test creating TimeEntryRow for absence day."""
        row = TimeEntryRow(
            work_date=date(2026, 1, 28),
            absence_type="sick",
            notes="Doctor's appointment",
        )

        assert row.work_date == date(2026, 1, 28)
        assert row.start_time is None
        assert row.end_time is None
        assert row.break_minutes == 0
        assert row.absence_type == "sick"
        assert row.notes == "Doctor's appointment"

    def test_break_minutes_defaults_to_zero(self):
        """Test that break_minutes defaults to 0 if not provided."""
        row = TimeEntryRow(work_date=date(2026, 1, 28))

        assert row.break_minutes == 0

    def test_absence_type_defaults_to_none(self):
        """Test that absence_type defaults to 'none' if not provided."""
        row = TimeEntryRow(work_date=date(2026, 1, 28))

        assert row.absence_type == "none"


class TestValidationError:
    """Tests for ValidationError dataclass."""

    def test_create_validation_error(self):
        """Test creating ValidationError with all fields."""
        error = ValidationError(
            row_number=5,
            field="start_time",
            message="Startzeit fehlt",
            code="missing_start_time",
        )

        assert error.row_number == 5
        assert error.field == "start_time"
        assert error.message == "Startzeit fehlt"
        assert error.code == "missing_start_time"

    def test_german_error_messages(self):
        """Test that ValidationError uses German error messages."""
        errors = [
            ValidationError(
                row_number=1,
                field="work_date",
                message="Ungültiges Datum",
                code="invalid_date",
            ),
            ValidationError(
                row_number=2,
                field="end_time",
                message="Endzeit muss nach Startzeit liegen",
                code="end_before_start",
            ),
            ValidationError(
                row_number=3,
                field="break_minutes",
                message="Pausenzeit überschreitet Arbeitszeit",
                code="break_exceeds_duration",
            ),
        ]

        assert errors[0].message == "Ungültiges Datum"
        assert errors[1].message == "Endzeit muss nach Startzeit liegen"
        assert errors[2].message == "Pausenzeit überschreitet Arbeitszeit"

    def test_error_codes_are_machine_readable(self):
        """Test that error codes are consistent machine-readable strings."""
        error = ValidationError(
            row_number=1,
            field="work_date",
            message="Datum darf nicht in der Zukunft liegen",
            code="future_date",
        )

        assert error.code == "future_date"
        assert isinstance(error.code, str)


class TestImportResult:
    """Tests for ImportResult dataclass."""

    def test_create_successful_import_result(self):
        """Test creating successful ImportResult."""
        entries = [
            TimeEntryFactory.build(work_date=date(2026, 1, 27)),
            TimeEntryFactory.build(work_date=date(2026, 1, 28)),
        ]

        result = ImportResult(
            success=True,
            imported_count=2,
            skipped_count=0,
            errors=[],
            entries=entries,
        )

        assert result.success is True
        assert result.imported_count == 2
        assert result.skipped_count == 0
        assert len(result.errors) == 0
        assert len(result.entries) == 2

    def test_create_failed_import_result(self):
        """Test creating failed ImportResult with validation errors."""
        errors = [
            ValidationError(
                row_number=2,
                field="start_time",
                message="Startzeit fehlt",
                code="missing_start_time",
            ),
            ValidationError(
                row_number=5,
                field="work_date",
                message="Ungültiges Datum",
                code="invalid_date",
            ),
        ]

        result = ImportResult(
            success=False,
            imported_count=0,
            skipped_count=2,
            errors=errors,
            entries=[],
        )

        assert result.success is False
        assert result.imported_count == 0
        assert result.skipped_count == 2
        assert len(result.errors) == 2
        assert len(result.entries) == 0

    def test_partial_import_result(self):
        """Test ImportResult with some successful, some failed imports."""
        entries = [TimeEntryFactory.build(work_date=date(2026, 1, 27))]
        errors = [
            ValidationError(
                row_number=2,
                field="end_time",
                message="Endzeit muss nach Startzeit liegen",
                code="end_before_start",
            ),
        ]

        result = ImportResult(
            success=True,
            imported_count=1,
            skipped_count=1,
            errors=errors,
            entries=entries,
        )

        assert result.success is True
        assert result.imported_count == 1
        assert result.skipped_count == 1
        assert len(result.errors) == 1
        assert len(result.entries) == 1

    def test_empty_import_result(self):
        """Test ImportResult with no entries imported."""
        result = ImportResult(
            success=True,
            imported_count=0,
            skipped_count=0,
            errors=[],
            entries=[],
        )

        assert result.success is True
        assert result.imported_count == 0
        assert result.skipped_count == 0
        assert len(result.errors) == 0
        assert len(result.entries) == 0


class TestExportResult:
    """Tests for ExportResult dataclass."""

    def test_create_successful_export_result(self):
        """Test creating successful ExportResult."""
        content = b"work_date,start_time,end_time,break_minutes\n2026-01-28,07:00,15:00,30\n"

        result = ExportResult(
            success=True,
            content=content,
            filename="time_entries_2026-01.csv",
            content_type="text/csv",
        )

        assert result.success is True
        assert result.content == content
        assert result.filename == "time_entries_2026-01.csv"
        assert result.content_type == "text/csv"

    def test_create_failed_export_result(self):
        """Test creating failed ExportResult."""
        result = ExportResult(
            success=False,
            content=b"",
            filename="",
            content_type="",
        )

        assert result.success is False
        assert result.content == b""
        assert result.filename == ""
        assert result.content_type == ""

    def test_export_result_with_xlsx_content(self):
        """Test ExportResult with Excel (XLSX) content."""
        content = b"\x50\x4b\x03\x04"  # Mock XLSX file header (PK zip signature)

        result = ExportResult(
            success=True,
            content=content,
            filename="time_entries_2026-01.xlsx",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        assert result.success is True
        assert result.content.startswith(b"\x50\x4b\x03\x04")
        assert result.filename.endswith(".xlsx")
        assert "spreadsheetml.sheet" in result.content_type

    def test_export_result_content_is_bytes(self):
        """Test that ExportResult content is always bytes."""
        result = ExportResult(
            success=True,
            content=b"test content",
            filename="test.csv",
            content_type="text/csv",
        )

        assert isinstance(result.content, bytes)
