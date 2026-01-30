"""Tests for import-related issues M6 and M7.

ISSUE M6: Import Month Mismatch - Poor Error Handling
ISSUE M7: Import Fails Silently with "Skip Existing" for Duplicate Data
"""

from datetime import date

from source.database.models import TimeEntry


class TestIssueM6MonthMismatch:
    """Tests for ISSUE M6: Import month mismatch validation."""

    def test_import_from_different_month_should_show_clear_error(self, db_session, client):
        """Test importing CSV with entries from a different month shows clear German error.

        When viewing December 2025, importing CSV with January 2026 entries
        should return a clear error message explaining the month mismatch.
        """
        # CSV content with January 2026 entries
        csv_content = b"""work_date,start_time,end_time,break_minutes,absence_type,notes
2026-01-13,08:00,17:00,30,Keine,Test entry for January
2026-01-14,08:00,17:00,30,Keine,Another January entry
"""

        # POST to import endpoint with December 2025 as context (month=12, year=2025)
        response = client.post(
            "/time-entries/import?month=12&year=2025&user_id=1&skip_duplicates=false",
            files={"file": ("test.csv", csv_content, "text/csv")},
        )

        # Should return 422 with clear error
        assert response.status_code == 422

        # Check for German error message explaining month mismatch
        # Expected: "Die CSV-Datei enthält Einträge für Januar 2026, aber Sie befinden sich auf der Seite für Dezember 2025"
        json_response = response.json()
        assert "detail" in json_response

        # For HTMX, check HTML contains error message
        if "errors" in json_response.get("detail", {}):
            errors = json_response["detail"]["errors"]
            assert len(errors) > 0
            # Should have month mismatch error
            month_errors = [e for e in errors if "monat" in e["message"].lower() or "januar" in e["message"].lower()]
            assert len(month_errors) > 0

    def test_import_from_same_month_should_succeed(self, db_session, client):
        """Test importing CSV with entries from the viewed month succeeds."""
        # CSV content with December 2025 entries
        csv_content = b"""work_date,start_time,end_time,break_minutes,absence_type,notes
2025-12-16,08:00,17:00,30,Keine,Test entry for December
2025-12-17,08:00,17:00,30,Keine,Another December entry
"""

        # POST to import endpoint with December 2025 as context
        response = client.post(
            "/time-entries/import?month=12&year=2025&user_id=1&skip_duplicates=false",
            files={"file": ("test.csv", csv_content, "text/csv")},
        )

        # Should succeed
        assert response.status_code in (200, 201)

    def test_import_mixed_months_should_show_which_entries_mismatch(self, db_session, client):
        """Test importing CSV with mixed months shows which entries don't match."""
        # CSV content with both December 2025 and January 2026 entries
        csv_content = b"""work_date,start_time,end_time,break_minutes,absence_type,notes
2025-12-16,08:00,17:00,30,Keine,December entry (valid)
2026-01-13,08:00,17:00,30,Keine,January entry (invalid)
2025-12-17,08:00,17:00,30,Keine,December entry (valid)
2026-01-14,08:00,17:00,30,Keine,January entry (invalid)
"""

        # POST to import endpoint with December 2025 as context
        response = client.post(
            "/time-entries/import?month=12&year=2025&user_id=1&skip_duplicates=false",
            files={"file": ("test.csv", csv_content, "text/csv")},
        )

        # Should return 422 with errors for January entries
        assert response.status_code == 422

        json_response = response.json()
        if "errors" in json_response.get("detail", {}):
            errors = json_response["detail"]["errors"]
            # Should have 2 errors (row 2 and row 4, 0-indexed as rows 1 and 3)
            month_errors = [e for e in errors if e.get("code") == "month_mismatch"]
            assert len(month_errors) == 2


class TestIssueM7SkipAllDuplicates:
    """Tests for ISSUE M7: Import with skip_duplicates when all entries exist."""

    def test_skip_all_duplicates_should_return_success(self, db_session, client):
        """Test importing CSV where ALL entries exist and skip_duplicates=True returns success.

        Should return success with imported_count=0 and skipped_count=N.
        """
        # First, create existing entries
        existing_dates = [date(2025, 12, 16), date(2025, 12, 17)]
        for work_date in existing_dates:
            entry = TimeEntry(
                user_id=1,
                work_date=work_date,
                start_time=None,
                end_time=None,
                break_minutes=0,
                absence_type="none",
                notes="Existing entry",
            )
            db_session.add(entry)
        db_session.commit()

        # CSV content with same dates
        csv_content = b"""work_date,start_time,end_time,break_minutes,absence_type,notes
2025-12-16,08:00,17:00,30,Keine,Duplicate entry
2025-12-17,08:00,17:00,30,Keine,Duplicate entry
"""

        # POST to import endpoint with skip_duplicates=True
        response = client.post(
            "/time-entries/import?user_id=1&skip_duplicates=true",
            files={"file": ("test.csv", csv_content, "text/csv")},
        )

        # Should return success (200 or 201, NOT 422)
        assert response.status_code in (200, 201)

        # Check response indicates 0 imported, 2 skipped
        json_response = response.json()
        assert json_response.get("success") is True
        assert json_response.get("imported_count") == 0
        assert json_response.get("skipped_count") == 2

    def test_skip_some_duplicates_should_return_success_with_mixed_counts(self, db_session, client):
        """Test importing CSV where SOME entries exist and skip_duplicates=True succeeds.

        Should return success with imported_count=N and skipped_count=M.
        """
        # First, create one existing entry
        existing_entry = TimeEntry(
            user_id=1,
            work_date=date(2025, 12, 16),
            start_time=None,
            end_time=None,
            break_minutes=0,
            absence_type="none",
            notes="Existing entry",
        )
        db_session.add(existing_entry)
        db_session.commit()

        # CSV content with one duplicate and one new entry
        csv_content = b"""work_date,start_time,end_time,break_minutes,absence_type,notes
2025-12-16,08:00,17:00,30,Keine,Duplicate entry
2025-12-17,08:00,17:00,30,Keine,New entry
"""

        # POST to import endpoint with skip_duplicates=True
        response = client.post(
            "/time-entries/import?user_id=1&skip_duplicates=true",
            files={"file": ("test.csv", csv_content, "text/csv")},
        )

        # Should return success
        assert response.status_code in (200, 201)

        # Check response indicates 1 imported, 1 skipped
        json_response = response.json()
        assert json_response.get("success") is True
        assert json_response.get("imported_count") == 1
        assert json_response.get("skipped_count") == 1

    def test_skip_duplicates_false_with_duplicates_should_return_error(self, db_session, client):
        """Test importing CSV with duplicates and skip_duplicates=False returns error."""
        # First, create existing entry
        existing_entry = TimeEntry(
            user_id=1,
            work_date=date(2025, 12, 16),
            start_time=None,
            end_time=None,
            break_minutes=0,
            absence_type="none",
            notes="Existing entry",
        )
        db_session.add(existing_entry)
        db_session.commit()

        # CSV content with duplicate date
        csv_content = b"""work_date,start_time,end_time,break_minutes,absence_type,notes
2025-12-16,08:00,17:00,30,Keine,Duplicate entry
"""

        # POST to import endpoint with skip_duplicates=False
        response = client.post(
            "/time-entries/import?user_id=1&skip_duplicates=false",
            files={"file": ("test.csv", csv_content, "text/csv")},
        )

        # Should return 422 with duplicate error
        assert response.status_code == 422

        json_response = response.json()
        assert "detail" in json_response
        errors = json_response["detail"].get("errors", [])
        assert len(errors) > 0
        assert any(e.get("code") == "duplicate_date" for e in errors)
