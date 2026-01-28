"""Tests for Import Service.

This module tests the ImportService implementation for importing time entries
from CSV files with validation, duplicate checking, and persistence.
"""

from datetime import date, time

from source.services.data_transfer.csv_format import CSVFormatHandler
from source.services.data_transfer.import_service import ImportService
from tests.factories import TimeEntryFactory


class TestImportServiceInitialization:
    """Tests for ImportService initialization."""

    def test_default_constructor_uses_csv_handler(self):
        """Test that default constructor uses CSVFormatHandler."""
        service = ImportService()

        assert isinstance(service.handler, CSVFormatHandler)

    def test_can_provide_custom_format_handler(self):
        """Test that custom format handler can be provided."""
        custom_handler = CSVFormatHandler()
        service = ImportService(handler=custom_handler)

        assert service.handler is custom_handler


class TestImportServiceStructureValidation:
    """Tests for import file structure validation."""

    def test_invalid_structure_missing_columns_returns_errors(self, db_session):
        """Test that invalid CSV structure returns errors immediately."""
        service = ImportService()
        # CSV missing required columns
        content = b"Datum;Startzeit\n2026-01-15;07:00\n"

        result = service.import_file(content, user_id=1, db=db_session)

        assert result.success is False
        assert len(result.errors) > 0
        assert any(error.code == "missing_column" for error in result.errors)
        assert result.imported_count == 0

    def test_empty_file_returns_error(self, db_session):
        """Test that empty file returns error."""
        service = ImportService()
        content = b""

        result = service.import_file(content, user_id=1, db=db_session)

        assert result.success is False
        assert len(result.errors) > 0
        assert any(error.code == "empty_file" for error in result.errors)
        assert result.imported_count == 0

    def test_invalid_encoding_returns_error(self, db_session):
        """Test that invalid encoding returns error."""
        service = ImportService()
        # Invalid UTF-8 bytes
        content = b"\xff\xfe Invalid encoding"

        result = service.import_file(content, user_id=1, db=db_session)

        assert result.success is False
        assert len(result.errors) > 0
        assert any(error.code == "invalid_encoding" for error in result.errors)
        assert result.imported_count == 0


class TestImportServiceParseErrors:
    """Tests for parsing errors during import."""

    def test_invalid_date_format_returns_error(self, db_session):
        """Test that invalid date format returns error."""
        service = ImportService()
        # Date in German format instead of ISO
        content = b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n" b"15.01.2026;07:00;15:00;30;Keine;\n"

        result = service.import_file(content, user_id=1, db=db_session)

        assert result.success is False
        assert len(result.errors) > 0
        error = result.errors[0]
        assert error.code == "invalid_date"
        assert error.field == "work_date"
        assert error.row_number == 2
        assert "Ungültiges Datumsformat" in error.message

    def test_invalid_time_format_returns_error(self, db_session):
        """Test that invalid time format returns error."""
        service = ImportService()
        # Invalid time format
        content = b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n" b"2026-01-15;abc;15:00;30;Keine;\n"

        result = service.import_file(content, user_id=1, db=db_session)

        assert result.success is False
        assert len(result.errors) > 0
        error = result.errors[0]
        assert error.code == "invalid_time"
        assert error.field == "start_time"
        assert error.row_number == 2
        assert "Ungültiges Zeitformat" in error.message

    def test_invalid_break_minutes_non_integer_returns_error(self, db_session):
        """Test that non-integer break_minutes returns error."""
        service = ImportService()
        # Break minutes is not a number
        content = b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n" b"2026-01-15;07:00;15:00;abc;Keine;\n"

        result = service.import_file(content, user_id=1, db=db_session)

        assert result.success is False
        assert len(result.errors) > 0
        error = result.errors[0]
        assert error.code == "invalid_break_minutes"
        assert error.field == "break_minutes"
        assert error.row_number == 2
        assert "Pausenzeit muss eine Zahl sein" in error.message

    def test_invalid_absence_type_returns_error(self, db_session):
        """Test that invalid absence type returns error."""
        service = ImportService()
        # Unknown absence type
        content = (
            b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n" b"2026-01-15;07:00;15:00;30;InvalidType;\n"
        )

        result = service.import_file(content, user_id=1, db=db_session)

        assert result.success is False
        assert len(result.errors) > 0
        error = result.errors[0]
        assert error.code == "invalid_absence_type"
        assert error.field == "absence_type"
        assert error.row_number == 2
        assert "Ungültiger Abwesenheitstyp" in error.message


class TestImportServiceBusinessValidation:
    """Tests for business rule validation during import."""

    def test_end_before_start_returns_error(self, db_session):
        """Test that end time before start time returns error."""
        service = ImportService()
        # End time is before start time
        content = b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n" b"2026-01-15;15:00;07:00;30;Keine;\n"

        result = service.import_file(content, user_id=1, db=db_session)

        assert result.success is False
        assert len(result.errors) > 0
        error = result.errors[0]
        assert error.code == "end_before_start"
        assert error.row_number == 2
        assert "Endzeit muss nach Startzeit liegen" in error.message

    def test_missing_end_time_returns_error(self, db_session):
        """Test that start time without end time returns error."""
        service = ImportService()
        # Has start but no end
        content = b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n" b"2026-01-15;07:00;;30;Keine;\n"

        result = service.import_file(content, user_id=1, db=db_session)

        assert result.success is False
        assert len(result.errors) > 0
        error = result.errors[0]
        assert error.code == "missing_end_time"
        assert error.field == "end_time"
        assert error.row_number == 2
        assert "Endzeit fehlt" in error.message

    def test_missing_start_time_returns_error(self, db_session):
        """Test that end time without start time returns error."""
        service = ImportService()
        # Has end but no start
        content = b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n" b"2026-01-15;;15:00;30;Keine;\n"

        result = service.import_file(content, user_id=1, db=db_session)

        assert result.success is False
        assert len(result.errors) > 0
        error = result.errors[0]
        assert error.code == "missing_start_time"
        assert error.field == "start_time"
        assert error.row_number == 2
        assert "Startzeit fehlt" in error.message

    def test_break_exceeds_duration_returns_error(self, db_session):
        """Test that break longer than work duration returns error."""
        service = ImportService()
        # Break is 60 minutes, but work duration is only 1 hour
        content = b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n" b"2026-01-15;07:00;08:00;90;Keine;\n"

        result = service.import_file(content, user_id=1, db=db_session)

        assert result.success is False
        assert len(result.errors) > 0
        error = result.errors[0]
        assert error.code == "break_exceeds_duration"
        assert error.field == "break_minutes"
        assert error.row_number == 2
        assert "Pausenzeit überschreitet Arbeitszeit" in error.message


class TestImportServiceDuplicateHandling:
    """Tests for duplicate date handling during import."""

    def test_duplicate_date_in_db_without_skip_returns_error(self, db_session):
        """Test that duplicate date in DB without skip_duplicates returns error."""
        # Create existing entry for 2026-01-15
        existing = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(existing)
        db_session.commit()

        service = ImportService()
        # Try to import entry for same date
        content = b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n" b"2026-01-15;07:00;15:00;30;Keine;\n"

        result = service.import_file(content, user_id=1, db=db_session, skip_duplicates=False)

        assert result.success is False
        assert len(result.errors) > 0
        error = result.errors[0]
        assert error.code == "duplicate_date"
        assert error.row_number == 2
        assert "Für diesen Tag existiert bereits ein Eintrag" in error.message

    def test_duplicate_date_in_db_with_skip_skips_entry(self, db_session):
        """Test that duplicate date in DB with skip_duplicates=True skips entry."""
        # Create existing entry for 2026-01-15
        existing = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(existing)
        db_session.commit()

        service = ImportService()
        # Try to import entry for same date with skip_duplicates
        content = b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n" b"2026-01-15;07:00;15:00;30;Keine;\n"

        result = service.import_file(content, user_id=1, db=db_session, skip_duplicates=True)

        assert result.success is True
        assert result.imported_count == 0
        assert result.skipped_count == 1
        assert len(result.errors) == 0

    def test_intra_file_duplicate_always_returns_error(self, db_session):
        """Test that same date twice in file always returns error."""
        service = ImportService()
        # Same date appears twice in the file
        content = (
            b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n"
            b"2026-01-15;07:00;12:00;30;Keine;\n"
            b"2026-01-15;13:00;18:00;30;Keine;\n"
        )

        result = service.import_file(content, user_id=1, db=db_session, skip_duplicates=True)

        assert result.success is False
        assert len(result.errors) > 0
        # Should have error for the duplicate in file
        assert any(error.code == "duplicate_date_in_file" for error in result.errors)
        assert any("Datum kommt mehrfach in der Datei vor" in error.message for error in result.errors)


class TestImportServicePersistence:
    """Tests for persistence behavior during import."""

    def test_dry_run_validates_but_does_not_persist(self, db_session):
        """Test that dry_run=True validates but doesn't persist."""
        service = ImportService()
        content = (
            b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n" b"2026-01-15;07:00;15:00;30;Keine;Test entry\n"
        )

        result = service.import_file(content, user_id=1, db=db_session, dry_run=True)

        assert result.success is True
        assert result.imported_count == 1
        # Check nothing was persisted to DB
        from source.database.models import TimeEntry

        count = db_session.query(TimeEntry).count()
        assert count == 0

    def test_dry_run_false_persists_valid_entries(self, db_session):
        """Test that dry_run=False persists valid entries."""
        service = ImportService()
        content = (
            b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n" b"2026-01-15;07:00;15:00;30;Keine;Test entry\n"
        )

        result = service.import_file(content, user_id=1, db=db_session, dry_run=False)

        assert result.success is True
        assert result.imported_count == 1
        # Check entry was persisted
        from source.database.models import TimeEntry

        count = db_session.query(TimeEntry).count()
        assert count == 1

        entry = db_session.query(TimeEntry).first()
        assert entry.user_id == 1
        assert entry.work_date == date(2026, 1, 15)
        assert entry.notes == "Test entry"

    def test_validation_errors_prevent_any_persistence(self, db_session):
        """Test that validation errors prevent all entries from being persisted."""
        service = ImportService()
        # First entry valid, second entry has validation error
        content = (
            b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n"
            b"2026-01-15;07:00;15:00;30;Keine;Valid entry\n"
            b"2026-01-16;15:00;07:00;30;Keine;Invalid - end before start\n"
        )

        result = service.import_file(content, user_id=1, db=db_session, dry_run=False)

        assert result.success is False
        assert len(result.errors) > 0
        # NO entries should be persisted (all-or-nothing)
        from source.database.models import TimeEntry

        count = db_session.query(TimeEntry).count()
        assert count == 0

    def test_entries_have_correct_user_id_set(self, db_session):
        """Test that imported entries have correct user_id."""
        service = ImportService()
        content = b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n" b"2026-01-15;07:00;15:00;30;Keine;\n"

        result = service.import_file(content, user_id=42, db=db_session, dry_run=False)

        assert result.success is True
        from source.database.models import TimeEntry

        entry = db_session.query(TimeEntry).first()
        assert entry.user_id == 42


class TestImportServiceSuccess:
    """Tests for successful import scenarios."""

    def test_import_single_valid_entry(self, db_session):
        """Test importing single valid entry returns success."""
        service = ImportService()
        content = (
            b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n"
            b"2026-01-15;07:00;15:00;30;Keine;Productive day\n"
        )

        result = service.import_file(content, user_id=1, db=db_session)

        assert result.success is True
        assert result.imported_count == 1
        assert result.skipped_count == 0
        assert len(result.errors) == 0
        assert len(result.entries) == 1

        entry = result.entries[0]
        assert entry.work_date == date(2026, 1, 15)
        assert entry.start_time == time(7, 0)
        assert entry.end_time == time(15, 0)
        assert entry.break_minutes == 30
        assert entry.notes == "Productive day"

    def test_import_multiple_valid_entries(self, db_session):
        """Test importing multiple valid entries returns success."""
        service = ImportService()
        content = (
            b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n"
            b"2026-01-15;07:00;15:00;30;Keine;Day 1\n"
            b"2026-01-16;08:00;16:00;45;Keine;Day 2\n"
            b"2026-01-17;07:30;15:30;30;Keine;Day 3\n"
        )

        result = service.import_file(content, user_id=1, db=db_session)

        assert result.success is True
        assert result.imported_count == 3
        assert len(result.entries) == 3
        # Check dates are correct
        dates = [entry.work_date for entry in result.entries]
        assert date(2026, 1, 15) in dates
        assert date(2026, 1, 16) in dates
        assert date(2026, 1, 17) in dates

    def test_import_mixed_entries_work_and_absences(self, db_session):
        """Test importing mix of work days and absences."""
        service = ImportService()
        content = (
            b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n"
            b"2026-01-15;07:00;15:00;30;Keine;Work day\n"
            b"2026-01-16;;;0;Urlaub;Vacation\n"
            b"2026-01-17;07:00;15:00;30;Keine;Work day\n"
            b"2026-01-18;;;0;Krank;Sick day\n"
        )

        result = service.import_file(content, user_id=1, db=db_session)

        assert result.success is True
        assert result.imported_count == 4
        assert len(result.entries) == 4

    def test_returns_created_time_entry_objects(self, db_session):
        """Test that result.entries contains created TimeEntry objects."""
        service = ImportService()
        content = b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n" b"2026-01-15;07:00;15:00;30;Keine;\n"

        result = service.import_file(content, user_id=1, db=db_session, dry_run=False)

        assert result.success is True
        assert len(result.entries) == 1
        from source.database.models import TimeEntry

        assert isinstance(result.entries[0], TimeEntry)
        # Should have ID if persisted
        assert result.entries[0].id is not None


class TestImportServiceEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_notes_field_handled_correctly(self, db_session):
        """Test that empty notes field is handled correctly."""
        service = ImportService()
        content = b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n" b"2026-01-15;07:00;15:00;30;Keine;\n"

        result = service.import_file(content, user_id=1, db=db_session)

        assert result.success is True
        entry = result.entries[0]
        # Empty string should be stored as None or empty string
        assert entry.notes in (None, "")

    def test_zero_break_minutes_handled_correctly(self, db_session):
        """Test that zero break minutes is handled correctly."""
        service = ImportService()
        content = b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n" b"2026-01-15;07:00;15:00;0;Keine;\n"

        result = service.import_file(content, user_id=1, db=db_session)

        assert result.success is True
        entry = result.entries[0]
        assert entry.break_minutes == 0

    def test_absence_entry_with_no_times_handled_correctly(self, db_session):
        """Test that absence entry with no times is handled correctly."""
        service = ImportService()
        content = b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n" b"2026-01-15;;;0;Urlaub;Vacation day\n"

        result = service.import_file(content, user_id=1, db=db_session)

        assert result.success is True
        entry = result.entries[0]
        assert entry.start_time is None
        assert entry.end_time is None
        assert entry.break_minutes == 0
        from source.database.enums import AbsenceType

        assert entry.absence_type == AbsenceType.VACATION
