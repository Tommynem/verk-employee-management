"""Tests for ExportService.

This module tests the ExportService that orchestrates exporting time entries
to various formats using format handlers.
"""

from datetime import date, time
from unittest.mock import Mock

from source.services.data_transfer.base import FormatHandler
from source.services.data_transfer.csv_format import CSVFormatHandler
from source.services.data_transfer.dataclasses import TimeEntryRow
from source.services.data_transfer.export_service import ExportService
from tests.factories import HolidayEntryFactory, SickEntryFactory, TimeEntryFactory, VacationEntryFactory


class TestExportServiceInitialization:
    """Tests for ExportService initialization."""

    def test_default_constructor_uses_csv_handler(self):
        """Test that default constructor uses CSVFormatHandler."""
        service = ExportService()

        assert isinstance(service.handler, CSVFormatHandler)

    def test_can_provide_custom_format_handler(self):
        """Test that custom format handler can be provided."""
        mock_handler = Mock(spec=FormatHandler)
        service = ExportService(handler=mock_handler)

        assert service.handler is mock_handler


class TestExportServiceExportEntries:
    """Tests for ExportService.export_entries() method."""

    def test_export_empty_list_returns_success_with_headers_only(self):
        """Test export empty list returns success with headers only."""
        service = ExportService()
        entries = []

        result = service.export_entries(entries, user_id=1, year=2026, month=1)

        assert result.success is True
        assert result.content.startswith(b"\xef\xbb\xbf")  # UTF-8 BOM
        csv_text = result.content.decode("utf-8-sig")
        lines = csv_text.strip().split("\n")
        assert len(lines) == 1  # Only headers
        assert lines[0] == "Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen"

    def test_export_single_regular_entry_returns_correct_csv(self):
        """Test export single regular entry returns correct CSV."""
        service = ExportService()
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            start_time=time(7, 0),
            end_time=time(15, 30),
            break_minutes=30,
            notes="Productive day",
        )
        entries = [entry]

        result = service.export_entries(entries, user_id=1, year=2026, month=1)

        assert result.success is True
        csv_text = result.content.decode("utf-8-sig")
        lines = csv_text.strip().split("\n")
        assert len(lines) == 2
        assert lines[0] == "Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen"
        assert lines[1] == "2026-01-15;07:00;15:30;30;Keine;Productive day"

    def test_export_single_vacation_entry_no_times_returns_correct_csv(self):
        """Test export single vacation entry (no times) returns correct CSV."""
        service = ExportService()
        entry = VacationEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 16),
        )
        entries = [entry]

        result = service.export_entries(entries, user_id=1, year=2026, month=1)

        assert result.success is True
        csv_text = result.content.decode("utf-8-sig")
        lines = csv_text.strip().split("\n")
        assert len(lines) == 2
        assert lines[1] == "2026-01-16;;;0;Urlaub;"

    def test_export_multiple_entries_preserves_order(self):
        """Test export multiple entries preserves order."""
        service = ExportService()
        entry1 = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 13),
            start_time=time(7, 0),
            end_time=time(15, 0),
            break_minutes=30,
            notes="Monday",
        )
        entry2 = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 14),
            start_time=time(8, 0),
            end_time=time(16, 0),
            break_minutes=45,
            notes="Tuesday",
        )
        entry3 = VacationEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
        )
        entries = [entry1, entry2, entry3]

        result = service.export_entries(entries, user_id=1, year=2026, month=1)

        assert result.success is True
        csv_text = result.content.decode("utf-8-sig")
        lines = csv_text.strip().split("\n")
        assert len(lines) == 4  # Header + 3 entries
        assert "2026-01-13" in lines[1]
        assert "Monday" in lines[1]
        assert "2026-01-14" in lines[2]
        assert "Tuesday" in lines[2]
        assert "2026-01-15" in lines[3]
        assert "Urlaub" in lines[3]

    def test_generates_correct_filename_format(self):
        """Test generates correct filename: zeiterfassung_{user_id}_{YYYY-MM}.csv"""
        service = ExportService()
        entry = TimeEntryFactory.build(user_id=42, work_date=date(2026, 1, 15))
        entries = [entry]

        result = service.export_entries(entries, user_id=42, year=2026, month=1)

        assert result.filename == "zeiterfassung_42_2026-01.csv"

    def test_filename_uses_handler_file_extension(self):
        """Test filename uses handler's file_extension."""
        mock_handler = Mock(spec=FormatHandler)
        mock_handler.file_extension = "xlsx"
        mock_handler.content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        mock_handler.serialize.return_value = b"fake excel data"

        service = ExportService(handler=mock_handler)
        entry = TimeEntryFactory.build(user_id=5, work_date=date(2026, 1, 15))
        entries = [entry]

        result = service.export_entries(entries, user_id=5, year=2026, month=1)

        assert result.filename == "zeiterfassung_5_2026-01.xlsx"

    def test_returns_correct_content_type_from_handler(self):
        """Test returns correct content_type from handler."""
        service = ExportService()
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        entries = [entry]

        result = service.export_entries(entries, user_id=1, year=2026, month=1)

        assert result.content_type == "text/csv; charset=utf-8"

    def test_converts_time_entry_orm_to_time_entry_row_dto(self):
        """Test converts TimeEntry ORM objects to TimeEntryRow DTOs."""
        mock_handler = Mock(spec=FormatHandler)
        mock_handler.file_extension = "csv"
        mock_handler.content_type = "text/csv"
        mock_handler.serialize.return_value = b"csv data"

        service = ExportService(handler=mock_handler)
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            start_time=time(7, 0),
            end_time=time(15, 0),
            break_minutes=30,
            notes="Test note",
        )
        entries = [entry]

        service.export_entries(entries, user_id=1, year=2026, month=1)

        # Verify handler.serialize was called with TimeEntryRow objects
        mock_handler.serialize.assert_called_once()
        rows = mock_handler.serialize.call_args[0][0]
        assert len(rows) == 1
        assert isinstance(rows[0], TimeEntryRow)
        assert rows[0].work_date == date(2026, 1, 15)
        assert rows[0].start_time == time(7, 0)
        assert rows[0].end_time == time(15, 0)
        assert rows[0].break_minutes == 30
        assert rows[0].absence_type == "none"
        assert rows[0].notes == "Test note"

    def test_handles_entries_with_notes_containing_special_characters(self):
        """Test handles entries with notes containing special characters.

        Per RFC 4180, quotes in CSV are escaped by doubling them.
        """
        service = ExportService()
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            start_time=time(7, 0),
            end_time=time(15, 0),
            break_minutes=30,
            notes='Meeting with "client"; discuss costs & timeline',
        )
        entries = [entry]

        result = service.export_entries(entries, user_id=1, year=2026, month=1)

        assert result.success is True
        csv_text = result.content.decode("utf-8-sig")
        # RFC 4180: quotes are escaped by doubling, field wrapped in quotes
        assert 'Meeting with ""client""' in csv_text
        assert "costs & timeline" in csv_text

    def test_handles_all_absence_types_correctly(self):
        """Test handles all absence types correctly."""
        service = ExportService()
        entry_vacation = VacationEntryFactory.build(user_id=1, work_date=date(2026, 1, 13))
        entry_sick = SickEntryFactory.build(user_id=1, work_date=date(2026, 1, 14))
        entry_holiday = HolidayEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        entries = [entry_vacation, entry_sick, entry_holiday]

        result = service.export_entries(entries, user_id=1, year=2026, month=1)

        assert result.success is True
        csv_text = result.content.decode("utf-8-sig")
        lines = csv_text.strip().split("\n")
        assert "Urlaub" in lines[1]  # vacation
        assert "Krank" in lines[2]  # sick
        assert "Feiertag" in lines[3]  # holiday


class TestExportServiceEdgeCases:
    """Tests for ExportService edge cases."""

    def test_month_with_single_digit_gets_zero_padded(self):
        """Test month with single digit gets zero-padded (e.g., 2026-01 not 2026-1)."""
        service = ExportService()
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        entries = [entry]

        result = service.export_entries(entries, user_id=1, year=2026, month=1)

        assert result.filename == "zeiterfassung_1_2026-01.csv"
        assert "2026-1." not in result.filename  # Should not have single digit

    def test_month_december_gets_formatted_correctly(self):
        """Test month December (12) gets formatted correctly."""
        service = ExportService()
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 12, 25))
        entries = [entry]

        result = service.export_entries(entries, user_id=1, year=2026, month=12)

        assert result.filename == "zeiterfassung_1_2026-12.csv"

    def test_export_preserves_entry_order_by_work_date(self):
        """Test export preserves entry order (by work_date)."""
        service = ExportService()
        # Create entries out of order
        entry3 = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15), notes="Third")
        entry1 = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 13), notes="First")
        entry2 = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 14), notes="Second")
        entries = [entry3, entry1, entry2]

        result = service.export_entries(entries, user_id=1, year=2026, month=1)

        assert result.success is True
        csv_text = result.content.decode("utf-8-sig")
        lines = csv_text.strip().split("\n")
        # Should maintain order as provided, not sort
        assert "Third" in lines[1]
        assert "First" in lines[2]
        assert "Second" in lines[3]

    def test_handles_entry_with_no_notes(self):
        """Test handles entry with no notes (None)."""
        service = ExportService()
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            start_time=time(7, 0),
            end_time=time(15, 0),
            break_minutes=30,
            notes=None,
        )
        entries = [entry]

        result = service.export_entries(entries, user_id=1, year=2026, month=1)

        assert result.success is True
        csv_text = result.content.decode("utf-8-sig")
        lines = csv_text.strip().split("\n")
        # Should have empty notes field
        assert lines[1].endswith(";")

    def test_handles_entry_with_zero_break_minutes(self):
        """Test handles entry with zero break minutes."""
        service = ExportService()
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            start_time=time(7, 0),
            end_time=time(15, 0),
            break_minutes=0,
            notes="No break",
        )
        entries = [entry]

        result = service.export_entries(entries, user_id=1, year=2026, month=1)

        assert result.success is True
        csv_text = result.content.decode("utf-8-sig")
        lines = csv_text.strip().split("\n")
        assert ";0;" in lines[1]


__all__ = [
    "TestExportServiceInitialization",
    "TestExportServiceExportEntries",
    "TestExportServiceEdgeCases",
]
