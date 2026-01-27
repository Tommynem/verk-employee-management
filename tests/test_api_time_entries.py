"""Test TimeEntry CRUD API routes.

Tests for TimeEntry routes following VaWW REST+HTMX patterns.
All tests should fail initially (TDD RED phase) until routes are implemented.

Routes tested:
- GET /time-entries -> HTML list
- GET /time-entries/new -> HTML form
- POST /time-entries -> Create entry, return detail HTML
- GET /time-entries/{id} -> HTML detail
- GET /time-entries/{id}/edit -> HTML edit form
- PATCH /time-entries/{id} -> Update entry, return detail HTML
- DELETE /time-entries/{id} -> 204 No Content
"""

from datetime import date, time

from source.database.enums import RecordStatus
from tests.factories import TimeEntryFactory


class TestTimeEntryList:
    """Test GET /time-entries list view."""

    def test_list_entries_empty(self, client, db_session):
        """GET /time-entries returns 200 with empty state HTML."""
        response = client.get("/time-entries")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Empty state message should be present
        assert "Keine Zeiteinträge" in response.text or "keine" in response.text.lower()

    def test_list_entries_with_data(self, client, db_session):
        """GET /time-entries returns entries in HTML table."""
        # Create test entries
        entry = TimeEntryFactory.build(
            user_id=1, work_date=date(2026, 1, 15), start_time=time(7, 0), end_time=time(15, 0)
        )
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Date should appear in response (either ISO or German format)
        assert "2026-01-15" in response.text or "15.01.2026" in response.text

    def test_list_filter_by_month_year(self, client, db_session):
        """GET /time-entries?month=1&year=2026 filters correctly."""
        # Create entries for different months
        january_entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        february_entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 2, 15))
        db_session.add_all([january_entry, february_entry])
        db_session.commit()

        response = client.get("/time-entries?month=1&year=2026")

        assert response.status_code == 200
        # January entry should be present
        assert "2026-01-15" in response.text or "15.01.2026" in response.text
        # February entry should NOT be present
        assert "2026-02-15" not in response.text and "15.02.2026" not in response.text


class TestTimeEntryForms:
    """Test GET /time-entries/new and /time-entries/{id}/edit form views."""

    def test_get_new_form(self, client, db_session):
        """GET /time-entries/new returns form HTML."""
        response = client.get("/time-entries/new")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Form should contain work_date input
        assert 'name="work_date"' in response.text or "work_date" in response.text
        # Form should have POST action
        assert 'hx-post="/time-entries"' in response.text or 'action="/time-entries"' in response.text

    def test_get_edit_form(self, client, db_session):
        """GET /time-entries/{id}/edit returns pre-filled form."""
        # Create entry to edit
        entry = TimeEntryFactory.build(
            user_id=1, work_date=date(2026, 1, 15), start_time=time(7, 0), end_time=time(15, 0), notes="Test notes"
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/edit")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Form should contain notes value
        assert "Test notes" in response.text
        # Form should have PATCH action
        assert (
            f'hx-patch="/time-entries/{entry.id}"' in response.text
            or f'action="/time-entries/{entry.id}"' in response.text
        )


class TestTimeEntryCreate:
    """Test POST /time-entries creation endpoint."""

    def test_create_entry_success(self, client, db_session):
        """POST /time-entries creates entry, returns 201 with detail HTML."""
        response = client.post(
            "/time-entries",
            data={
                "work_date": "2026-01-15",
                "start_time": "07:00",
                "end_time": "15:00",
                "break_minutes": "30",
                "absence_type": "none",
            },
        )

        assert response.status_code == 201
        assert "text/html" in response.headers["content-type"]
        # Response should contain entry details
        assert "2026-01-15" in response.text or "15.01.2026" in response.text

    def test_create_entry_duplicate_date(self, client, db_session):
        """POST with duplicate user_id+work_date returns 422."""
        # Create existing entry
        existing = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(existing)
        db_session.commit()

        # Attempt to create duplicate
        response = client.post(
            "/time-entries",
            data={
                "work_date": "2026-01-15",
                "start_time": "07:00",
                "end_time": "15:00",
                "break_minutes": "30",
                "absence_type": "none",
            },
        )

        assert response.status_code == 422
        # Error message should indicate duplicate
        assert "bereits vorhanden" in response.text.lower() or "duplicate" in response.text.lower()

    def test_create_entry_validation_error(self, client, db_session):
        """POST with break_minutes > 480 returns 422."""
        response = client.post(
            "/time-entries",
            data={
                "work_date": "2026-01-15",
                "start_time": "07:00",
                "end_time": "15:00",
                "break_minutes": "600",  # Invalid: > 480
                "absence_type": "none",
            },
        )

        assert response.status_code == 422

    def test_create_entry_hx_trigger(self, client, db_session):
        """POST sets HX-Trigger: timeEntryCreated header."""
        response = client.post(
            "/time-entries",
            data={
                "work_date": "2026-01-15",
                "start_time": "07:00",
                "end_time": "15:00",
                "break_minutes": "30",
                "absence_type": "none",
            },
        )

        assert response.status_code == 201
        assert "HX-Trigger" in response.headers
        assert response.headers["HX-Trigger"] == "timeEntryCreated"


class TestTimeEntryDetail:
    """Test GET /time-entries/{id} detail view."""

    def test_get_entry_success(self, client, db_session):
        """GET /time-entries/{id} returns 200 with detail HTML."""
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15), notes="Detail test")
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Detail test" in response.text

    def test_get_entry_not_found(self, client, db_session):
        """GET /time-entries/{id} for missing entry returns 404."""
        response = client.get("/time-entries/99999")

        assert response.status_code == 404


class TestTimeEntryUpdate:
    """Test PATCH /time-entries/{id} update endpoint."""

    def test_update_entry_success(self, client, db_session):
        """PATCH /time-entries/{id} updates and returns detail HTML."""
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15), notes="Original notes")
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.patch(
            f"/time-entries/{entry.id}",
            data={
                "notes": "Updated notes",
                "break_minutes": "45",
            },
        )

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Updated notes should appear in response
        assert "Updated notes" in response.text

    def test_update_submitted_entry_fails(self, client, db_session):
        """PATCH on SUBMITTED status entry returns 422."""
        # Create SUBMITTED entry
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15), status=RecordStatus.SUBMITTED)
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.patch(
            f"/time-entries/{entry.id}",
            data={
                "notes": "Attempt to update",
            },
        )

        assert response.status_code == 422
        # Error message should indicate submission lock
        assert "eingereicht" in response.text.lower() or "submitted" in response.text.lower()

    def test_update_entry_hx_trigger(self, client, db_session):
        """PATCH sets HX-Trigger: timeEntryUpdated header."""
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.patch(
            f"/time-entries/{entry.id}",
            data={
                "notes": "Updated",
            },
        )

        assert response.status_code == 200
        assert "HX-Trigger" in response.headers
        assert response.headers["HX-Trigger"] == "timeEntryUpdated"


class TestTimeEntryDelete:
    """Test DELETE /time-entries/{id} deletion endpoint."""

    def test_delete_entry_success(self, client, db_session):
        """DELETE /time-entries/{id} returns 204 No Content."""
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.delete(f"/time-entries/{entry.id}")

        assert response.status_code == 204

    def test_delete_entry_hx_trigger(self, client, db_session):
        """DELETE sets HX-Trigger: timeEntryDeleted header."""
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.delete(f"/time-entries/{entry.id}")

        assert response.status_code == 204
        assert "HX-Trigger" in response.headers
        assert response.headers["HX-Trigger"] == "timeEntryDeleted"
