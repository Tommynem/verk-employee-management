"""Test Data Transfer API routes for CSV export/import.

Tests for Data Transfer routes following TDD RED phase.
All tests should fail initially until routes are implemented.

Routes tested:
- GET /time-entries/export -> CSV file download
- POST /time-entries/import -> CSV file upload with validation

TDD RED Phase: These tests define the expected API behavior.
"""

from datetime import date, time
from io import BytesIO

from tests.factories import TimeEntryFactory


class TestExportEndpoint:
    """Test GET /time-entries/export CSV export endpoint.

    Export endpoint should:
    - Accept month, year, user_id query parameters
    - Return StreamingResponse with CSV content
    - Set correct Content-Type and Content-Disposition headers
    - Include all time entries for the specified month
    """

    def test_export_returns_200_with_csv_content(self, client, db_session):
        """GET /time-entries/export returns 200 with CSV content."""
        # Create time entries for January 2026
        entry1 = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            start_time=time(8, 0),
            end_time=time(16, 0),
            break_minutes=30,
        )
        entry2 = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 20),
            start_time=time(9, 0),
            end_time=time(17, 0),
            break_minutes=45,
        )
        db_session.add_all([entry1, entry2])
        db_session.commit()

        response = client.get("/time-entries/export?month=1&year=2026&user_id=1")

        assert response.status_code == 200

    def test_export_has_correct_content_type(self, client, db_session):
        """Export response has Content-Type: text/csv; charset=utf-8."""
        # Create test entry
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries/export?month=1&year=2026&user_id=1")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"

    def test_export_has_content_disposition_header(self, client, db_session):
        """Export response has Content-Disposition with correct filename."""
        # Create test entry
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries/export?month=1&year=2026&user_id=1")

        assert response.status_code == 200
        assert "content-disposition" in response.headers
        # Filename format: zeiterfassung_{user_id}_{YYYY-MM}.csv
        assert "zeiterfassung_1_2026-01.csv" in response.headers["content-disposition"]
        assert "attachment" in response.headers["content-disposition"]

    def test_export_csv_contains_correct_entries(self, client, db_session):
        """CSV contains correct entries for the specified month."""
        # Create entries for January 2026
        entry1 = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            start_time=time(8, 0),
            end_time=time(16, 0),
            break_minutes=30,
            notes="Test entry 1",
        )
        entry2 = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 20),
            start_time=time(9, 0),
            end_time=time(17, 0),
            break_minutes=45,
            notes="Test entry 2",
        )
        # Entry from different month (should not be included)
        entry3 = TimeEntryFactory.build(user_id=1, work_date=date(2026, 2, 10))
        db_session.add_all([entry1, entry2, entry3])
        db_session.commit()

        response = client.get("/time-entries/export?month=1&year=2026&user_id=1")

        assert response.status_code == 200
        csv_content = response.text
        # Should contain January entries
        assert "2026-01-15" in csv_content
        assert "2026-01-20" in csv_content
        assert "Test entry 1" in csv_content
        assert "Test entry 2" in csv_content
        # Should NOT contain February entry
        assert "2026-02-10" not in csv_content

    def test_export_missing_month_parameter_returns_422(self, client, db_session):
        """Missing month parameter returns 422."""
        response = client.get("/time-entries/export?year=2026&user_id=1")

        assert response.status_code == 422

    def test_export_missing_year_parameter_returns_422(self, client, db_session):
        """Missing year parameter returns 422."""
        response = client.get("/time-entries/export?month=1&user_id=1")

        assert response.status_code == 422

    def test_export_invalid_month_returns_422(self, client, db_session):
        """Invalid month (13) returns 422."""
        response = client.get("/time-entries/export?month=13&year=2026&user_id=1")

        assert response.status_code == 422

    def test_export_empty_month_returns_headers_only(self, client, db_session):
        """Export with no entries returns CSV with headers only."""
        # No entries for March 2026
        response = client.get("/time-entries/export?month=3&year=2026&user_id=1")

        assert response.status_code == 200
        csv_content = response.text
        # Should have CSV headers
        assert "work_date" in csv_content or "Datum" in csv_content
        # Should have minimal content (just headers, maybe one line)
        assert len(csv_content.split("\n")) <= 2

    def test_export_user_id_defaults_to_1(self, client, db_session):
        """Export defaults to user_id=1 when not specified."""
        # Create entry for user 1
        entry1 = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        # Create entry for user 2 (should not be included)
        entry2 = TimeEntryFactory.build(user_id=2, work_date=date(2026, 1, 15))
        db_session.add_all([entry1, entry2])
        db_session.commit()

        response = client.get("/time-entries/export?month=1&year=2026")

        assert response.status_code == 200
        # Filename should show user_id=1
        assert "zeiterfassung_1_2026-01.csv" in response.headers["content-disposition"]

    def test_export_csv_format_explicitly(self, client, db_session):
        """Export with format=csv explicitly specified returns CSV."""
        # Create test entry
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries/export?month=1&year=2026&format=csv")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "zeiterfassung_1_2026-01.csv" in response.headers["content-disposition"]

    def test_export_pdf_format(self, client, db_session):
        """Export with format=pdf returns PDF."""
        from tests.factories import UserSettingsFactory

        # Create user settings for the user
        settings = UserSettingsFactory.build(user_id=1)
        db_session.add(settings)

        # Create test entry
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries/export?month=1&year=2026&format=pdf")

        assert response.status_code == 200

    def test_export_pdf_content_type(self, client, db_session):
        """PDF format returns application/pdf content type."""
        from tests.factories import UserSettingsFactory

        # Create user settings for the user
        settings = UserSettingsFactory.build(user_id=1)
        db_session.add(settings)

        # Create test entry
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries/export?month=1&year=2026&format=pdf")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_export_pdf_filename(self, client, db_session):
        """PDF has correct filename format with .pdf extension."""
        from tests.factories import UserSettingsFactory

        # Create user settings for the user
        settings = UserSettingsFactory.build(user_id=1)
        db_session.add(settings)

        # Create test entry
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries/export?month=1&year=2026&format=pdf")

        assert response.status_code == 200
        assert "content-disposition" in response.headers
        # Filename format: zeiterfassung_{user_id}_{YYYY-MM}.pdf
        assert "zeiterfassung_1_2026-01.pdf" in response.headers["content-disposition"]
        assert "attachment" in response.headers["content-disposition"]

    def test_export_invalid_format(self, client, db_session):
        """Invalid format returns 422 error."""
        # Create test entry
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries/export?month=1&year=2026&format=invalid")

        assert response.status_code == 422


class TestImportEndpoint:
    """Test POST /time-entries/import CSV import endpoint.

    Import endpoint should:
    - Accept multipart/form-data with file upload
    - Accept query parameters: user_id, dry_run, skip_duplicates
    - Validate CSV structure and content
    - Return JSON with import result
    - Persist entries to database (unless dry_run=true)
    """

    def test_import_valid_csv_returns_200(self, client, db_session):
        """POST /time-entries/import with valid CSV returns 200 with success."""
        csv_content = b"work_date,start_time,end_time,break_minutes,absence_type,notes\n2026-01-15,08:00,16:00,30,Keine,Test entry"

        response = client.post(
            "/time-entries/import?user_id=1",
            files={"file": ("test.csv", BytesIO(csv_content), "text/csv")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_import_response_contains_counts(self, client, db_session):
        """Import response contains imported_count, skipped_count, success."""
        csv_content = b"work_date,start_time,end_time,break_minutes,absence_type,notes\n2026-01-15,08:00,16:00,30,Keine,Test entry"

        response = client.post(
            "/time-entries/import?user_id=1",
            files={"file": ("test.csv", BytesIO(csv_content), "text/csv")},
        )

        assert response.status_code == 200
        data = response.json()
        assert "imported_count" in data
        assert "skipped_count" in data
        assert "success" in data
        assert data["imported_count"] == 1
        assert data["skipped_count"] == 0

    def test_import_persists_valid_entries_to_database(self, client, db_session):
        """Valid entries are persisted to database."""
        csv_content = b"work_date,start_time,end_time,break_minutes,absence_type,notes\n2026-01-15,08:00,16:00,30,Keine,Test entry"

        response = client.post(
            "/time-entries/import?user_id=1",
            files={"file": ("test.csv", BytesIO(csv_content), "text/csv")},
        )

        assert response.status_code == 200

        # Verify entry was persisted
        from source.database.models import TimeEntry

        entry = db_session.query(TimeEntry).filter(TimeEntry.work_date == date(2026, 1, 15)).first()
        assert entry is not None
        assert entry.user_id == 1
        assert entry.start_time == time(8, 0)
        assert entry.end_time == time(16, 0)
        assert entry.break_minutes == 30
        assert entry.notes == "Test entry"

    def test_import_invalid_csv_returns_422_with_errors(self, client, db_session):
        """Invalid CSV returns 422 with error details."""
        # Missing required columns
        csv_content = b"wrong_header,another_header\nvalue1,value2"

        response = client.post(
            "/time-entries/import?user_id=1",
            files={"file": ("test.csv", BytesIO(csv_content), "text/csv")},
        )

        assert response.status_code == 422
        data = response.json()
        assert "errors" in data or "detail" in data

    def test_import_dry_run_validates_without_persisting(self, client, db_session):
        """dry_run=true validates CSV without persisting to database."""
        csv_content = b"work_date,start_time,end_time,break_minutes,absence_type,notes\n2026-01-15,08:00,16:00,30,Keine,Test entry"

        response = client.post(
            "/time-entries/import?user_id=1&dry_run=true",
            files={"file": ("test.csv", BytesIO(csv_content), "text/csv")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify entry was NOT persisted
        from source.database.models import TimeEntry

        entry = db_session.query(TimeEntry).filter(TimeEntry.work_date == date(2026, 1, 15)).first()
        assert entry is None

    def test_import_skip_duplicates_skips_existing_dates(self, client, db_session):
        """skip_duplicates=true skips entries for dates that already exist."""
        # Create existing entry
        existing = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(existing)
        db_session.commit()

        # Try to import duplicate date
        csv_content = b"work_date,start_time,end_time,break_minutes,absence_type,notes\n2026-01-15,08:00,16:00,30,Keine,Test entry"

        response = client.post(
            "/time-entries/import?user_id=1&skip_duplicates=true",
            files={"file": ("test.csv", BytesIO(csv_content), "text/csv")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["skipped_count"] == 1
        assert data["imported_count"] == 0

    def test_import_duplicate_date_returns_error_with_row_number(self, client, db_session):
        """Duplicate date returns error with row number when skip_duplicates=false."""
        # Create existing entry
        existing = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(existing)
        db_session.commit()

        # Try to import duplicate date
        csv_content = b"work_date,start_time,end_time,break_minutes,absence_type,notes\n2026-01-15,08:00,16:00,30,Keine,Test entry"

        response = client.post(
            "/time-entries/import?user_id=1&skip_duplicates=false",
            files={"file": ("test.csv", BytesIO(csv_content), "text/csv")},
        )

        assert response.status_code == 422
        data = response.json()
        assert "errors" in data or "detail" in data
        # Error should mention duplicate or row number
        error_text = str(data).lower()
        assert "duplicate" in error_text or "bereits" in error_text or "row" in error_text

    def test_import_missing_file_returns_422(self, client, db_session):
        """Missing file parameter returns 422."""
        response = client.post("/time-entries/import?user_id=1")

        assert response.status_code == 422

    def test_import_entries_get_correct_user_id(self, client, db_session):
        """Imported entries are assigned the correct user_id."""
        csv_content = b"work_date,start_time,end_time,break_minutes,absence_type,notes\n2026-01-15,08:00,16:00,30,Keine,Test entry"

        response = client.post(
            "/time-entries/import?user_id=42",
            files={"file": ("test.csv", BytesIO(csv_content), "text/csv")},
        )

        assert response.status_code == 200

        # Verify entry has correct user_id
        from source.database.models import TimeEntry

        entry = db_session.query(TimeEntry).filter(TimeEntry.work_date == date(2026, 1, 15)).first()
        assert entry is not None
        assert entry.user_id == 42

    def test_import_user_id_defaults_to_1(self, client, db_session):
        """Import defaults to user_id=1 when not specified."""
        csv_content = b"work_date,start_time,end_time,break_minutes,absence_type,notes\n2026-01-15,08:00,16:00,30,Keine,Test entry"

        response = client.post(
            "/time-entries/import",
            files={"file": ("test.csv", BytesIO(csv_content), "text/csv")},
        )

        assert response.status_code == 200

        # Verify entry has user_id=1
        from source.database.models import TimeEntry

        entry = db_session.query(TimeEntry).filter(TimeEntry.work_date == date(2026, 1, 15)).first()
        assert entry is not None
        assert entry.user_id == 1


class TestImportValidation:
    """Test CSV import validation error cases.

    Import should validate:
    - CSV structure (headers, columns)
    - Date formats
    - Time formats
    - Business rules (end > start, break < duration)
    - Duplicate dates in file
    """

    def test_import_invalid_date_format(self, client, db_session):
        """Invalid date format returns 422 with error."""
        csv_content = (
            b"work_date,start_time,end_time,break_minutes,absence_type,notes\ninvalid-date,08:00,16:00,30,Keine,Test"
        )

        response = client.post(
            "/time-entries/import?user_id=1",
            files={"file": ("test.csv", BytesIO(csv_content), "text/csv")},
        )

        assert response.status_code == 422

    def test_import_invalid_time_format(self, client, db_session):
        """Invalid time format returns 422 with error."""
        csv_content = (
            b"work_date,start_time,end_time,break_minutes,absence_type,notes\n2026-01-15,25:00,16:00,30,Keine,Test"
        )

        response = client.post(
            "/time-entries/import?user_id=1",
            files={"file": ("test.csv", BytesIO(csv_content), "text/csv")},
        )

        assert response.status_code == 422

    def test_import_end_before_start_returns_422(self, client, db_session):
        """End time before start time returns 422."""
        csv_content = (
            b"work_date,start_time,end_time,break_minutes,absence_type,notes\n2026-01-15,16:00,08:00,30,Keine,Test"
        )

        response = client.post(
            "/time-entries/import?user_id=1",
            files={"file": ("test.csv", BytesIO(csv_content), "text/csv")},
        )

        assert response.status_code == 422

    def test_import_break_exceeds_duration_returns_422(self, client, db_session):
        """Break time exceeding work duration returns 422."""
        # 8:00 to 10:00 = 120 minutes, break = 180 minutes (invalid)
        csv_content = (
            b"work_date,start_time,end_time,break_minutes,absence_type,notes\n2026-01-15,08:00,10:00,180,Keine,Test"
        )

        response = client.post(
            "/time-entries/import?user_id=1",
            files={"file": ("test.csv", BytesIO(csv_content), "text/csv")},
        )

        assert response.status_code == 422

    def test_import_duplicate_date_in_file_returns_422(self, client, db_session):
        """Multiple entries for same date in file returns 422."""
        csv_content = b"""work_date,start_time,end_time,break_minutes,absence_type,notes
2026-01-15,08:00,16:00,30,Keine,First entry
2026-01-15,09:00,17:00,45,Keine,Duplicate date"""

        response = client.post(
            "/time-entries/import?user_id=1",
            files={"file": ("test.csv", BytesIO(csv_content), "text/csv")},
        )

        assert response.status_code == 422
        data = response.json()
        # Error should mention duplicate or row number
        error_text = str(data).lower()
        assert "duplicate" in error_text or "mehrfach" in error_text or "row" in error_text

    def test_import_missing_required_column(self, client, db_session):
        """Missing required column returns 422."""
        # Missing work_date column
        csv_content = b"start_time,end_time,break_minutes,absence_type,notes\n08:00,16:00,30,Keine,Test"

        response = client.post(
            "/time-entries/import?user_id=1",
            files={"file": ("test.csv", BytesIO(csv_content), "text/csv")},
        )

        assert response.status_code == 422


class TestImportMultipleEntries:
    """Test importing CSV files with multiple entries."""

    def test_import_multiple_valid_entries(self, client, db_session):
        """Import successfully processes multiple valid entries."""
        csv_content = b"""work_date,start_time,end_time,break_minutes,absence_type,notes
2026-01-15,08:00,16:00,30,Keine,First entry
2026-01-16,09:00,17:00,45,Keine,Second entry
2026-01-17,07:30,15:30,30,Keine,Third entry"""

        response = client.post(
            "/time-entries/import?user_id=1",
            files={"file": ("test.csv", BytesIO(csv_content), "text/csv")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["imported_count"] == 3

    def test_import_all_or_nothing_validation(self, client, db_session):
        """Import fails all entries if any single entry is invalid."""
        # Second entry has invalid time format
        csv_content = b"""work_date,start_time,end_time,break_minutes,absence_type,notes
2026-01-15,08:00,16:00,30,Keine,Valid entry
2026-01-16,invalid,17:00,45,Keine,Invalid entry
2026-01-17,07:30,15:30,30,Keine,Another valid"""

        response = client.post(
            "/time-entries/import?user_id=1",
            files={"file": ("test.csv", BytesIO(csv_content), "text/csv")},
        )

        assert response.status_code == 422

        # Verify no entries were persisted
        from source.database.models import TimeEntry

        count = db_session.query(TimeEntry).filter(TimeEntry.user_id == 1).count()
        assert count == 0
