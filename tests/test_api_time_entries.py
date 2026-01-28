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
from decimal import Decimal

from source.database.enums import RecordStatus
from tests.factories import TimeEntryFactory, UserSettingsFactory


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
        # Date should appear in response (DD.MM.YY format per spec)
        assert "15.01.26" in response.text

    def test_list_filter_by_month_year(self, client, db_session):
        """GET /time-entries?month=1&year=2026 filters correctly."""
        # Create entries for different months
        january_entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        february_entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 2, 15))
        db_session.add_all([january_entry, february_entry])
        db_session.commit()

        response = client.get("/time-entries?month=1&year=2026")

        assert response.status_code == 200
        # January entry should be present (DD.MM.YY format per spec)
        assert "15.01.26" in response.text
        # February entry should NOT be present
        assert "15.02.26" not in response.text


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
        # Response should contain entry details (date in DD.MM.YY format per template)
        assert "15.01.26" in response.text

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


class TestMonthlyViewContext:
    """Test GET /time-entries?month=X&year=Y monthly view context.

    Monthly view requires additional context for templates:
    - summary: MonthlySummary with calculations
    - month/year: Month and year being displayed
    - month_name: German month name
    - prev_month/prev_year: Navigation to previous month
    - next_month/next_year: Navigation to next month
    - next_date: Date for "Add Next Day" button
    """

    # German month names for reference
    GERMAN_MONTHS = {
        1: "Januar",
        2: "Februar",
        3: "März",
        4: "April",
        5: "Mai",
        6: "Juni",
        7: "Juli",
        8: "August",
        9: "September",
        10: "Oktober",
        11: "November",
        12: "Dezember",
    }

    def test_context_includes_summary(self, client, db_session):
        """Response context includes MonthlySummary with total_actual, total_target, period_balance."""
        # Create user settings with target hours
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("32.00"))
        db_session.add(settings)

        # Create time entry with 8 hours worked
        entry = TimeEntryFactory.build(
            user_id=1, work_date=date(2026, 1, 15), start_time=time(7, 0), end_time=time(15, 30), break_minutes=30
        )
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries?month=1&year=2026")

        assert response.status_code == 200
        # Check for summary section with labels and values per design spec
        # Should have labels like "Ist-Stunden", "Pro Monat", "Überstunden"
        assert "Ist-Stunden" in response.text
        assert "Pro Monat" in response.text or "Soll" in response.text
        assert "Überstunden" in response.text or "Monatssaldo" in response.text

    def test_context_includes_month_year(self, client, db_session):
        """Response includes month and year integers."""
        response = client.get("/time-entries?month=3&year=2026")

        assert response.status_code == 200
        # Month and year should appear in the response
        assert "2026" in response.text
        # Month 3 should be displayed (either as number or German name "März")
        assert "3" in response.text or "März" in response.text

    def test_context_includes_german_month_name(self, client, db_session):
        """month_name is German (e.g., 'Januar' for month=1)."""
        response = client.get("/time-entries?month=1&year=2026")

        assert response.status_code == 200
        # German month name should appear
        assert "Januar" in response.text

    def test_navigation_includes_prev_next_month(self, client, db_session):
        """Response includes prev_month, prev_year, next_month, next_year."""
        response = client.get("/time-entries?month=5&year=2026")

        assert response.status_code == 200
        # Should have navigation to previous month (April) and next month (June)
        # Navigation links should contain month and year parameters
        assert "month=4" in response.text  # prev_month
        assert "month=6" in response.text  # next_month
        assert "year=2026" in response.text

    def test_navigation_wraps_year_boundary(self, client, db_session):
        """December → January wraps year correctly (month=12 → next_month=1, next_year+1)."""
        response = client.get("/time-entries?month=12&year=2025")

        assert response.status_code == 200
        # Next month should be January 2026
        assert "month=1" in response.text
        assert "year=2026" in response.text
        # Previous month should be November 2025
        assert "month=11" in response.text
        assert "year=2025" in response.text

    def test_navigation_wraps_year_boundary_backward(self, client, db_session):
        """January → December wraps year correctly (month=1 → prev_month=12, prev_year-1)."""
        response = client.get("/time-entries?month=1&year=2026")

        assert response.status_code == 200
        # Previous month should be December 2025
        assert "month=12" in response.text
        assert "year=2025" in response.text
        # Next month should be February 2026
        assert "month=2" in response.text
        assert "year=2026" in response.text

    def test_context_includes_next_date(self, client, db_session):
        """Response includes next_date for 'Add Next Day' button."""
        # Create entry on January 15
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries?month=1&year=2026")

        assert response.status_code == 200
        # Should have a "next day" date in response
        # This could be a link or button with the next date
        assert "time-entries/new" in response.text

    def test_next_date_after_last_entry(self, client, db_session):
        """next_date is day after the last entry's work_date."""
        # Create entries on different dates
        entry1 = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 10))
        entry2 = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 18))  # Latest
        entry3 = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 5))
        db_session.add_all([entry1, entry2, entry3])
        db_session.commit()

        response = client.get("/time-entries?month=1&year=2026")

        assert response.status_code == 200
        # Next date should be January 19 (day after latest entry on Jan 18)
        assert "2026-01-19" in response.text or "19.01.2026" in response.text

    def test_next_date_first_of_month_when_no_entries(self, client, db_session):
        """next_date is first of month when no entries exist."""
        response = client.get("/time-entries?month=1&year=2026")

        assert response.status_code == 200
        # Next date should be first of month when no entries
        assert "2026-01-01" in response.text or "01.01.2026" in response.text


class TestHTMXResponseDetection:
    """Test HTMX request detection and appropriate template rendering."""

    def test_direct_browser_access_returns_full_page(self, client, db_session):
        """Direct browser access returns full page with base.html wrapper."""
        # Create test entry for monthly view
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries?month=1&year=2026")

        assert response.status_code == 200
        # Should contain base.html elements (nav, DOCTYPE, etc.)
        assert "<!DOCTYPE html>" in response.text
        assert "<nav" in response.text or "navbar" in response.text
        # Should contain the time-entries-content wrapper
        assert 'id="time-entries-content"' in response.text

    def test_htmx_request_returns_partial_only(self, client, db_session):
        """HTMX request returns partial template without base.html wrapper."""
        # Create test entry for monthly view
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(entry)
        db_session.commit()

        # Simulate HTMX request with HX-Request header
        response = client.get("/time-entries?month=1&year=2026", headers={"HX-Request": "true"})

        assert response.status_code == 200
        # Should NOT contain base.html elements
        assert "<!DOCTYPE html>" not in response.text
        assert "<nav" not in response.text
        # Should contain the browser partial content (month navigation, table)
        assert "Januar" in response.text
        assert "15.01.26" in response.text

    def test_htmx_navigation_targets_correct_container(self, client, db_session):
        """Month navigation buttons target #time-entries-content."""
        # Create test entry for monthly view
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries?month=1&year=2026")

        assert response.status_code == 200
        # Navigation buttons should target #time-entries-content
        assert 'hx-target="#time-entries-content"' in response.text


class TestInlineEditingRoutes:
    """Test inline editing row routes for table-based editing.

    These routes enable inline editing of time entries directly in the monthly view table:
    - GET /time-entries/{id}/edit-row: Returns editable row HTML for existing entry
    - GET /time-entries/{id}/row: Returns read-only row HTML (for cancel action)
    - GET /time-entries/new-row: Returns editable row HTML for new entry

    TDD RED phase: All tests should fail because routes don't exist yet.
    """

    def test_get_edit_row_success(self, client, db_session):
        """GET /time-entries/{id}/edit-row returns 200 with editable row HTML."""
        # Create existing entry to edit
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            start_time=time(7, 0),
            end_time=time(15, 0),
            break_minutes=30,
            notes="Test notes",
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/edit-row")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Should contain the entry date
        assert "15.01.26" in response.text or "2026-01-15" in response.text

    def test_get_edit_row_contains_form_inputs(self, client, db_session):
        """Editable row contains form inputs for start_time, end_time, break_minutes, notes."""
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            start_time=time(7, 0),
            end_time=time(15, 0),
            break_minutes=30,
            notes="Test notes",
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/edit-row")

        assert response.status_code == 200
        # Should contain input fields for editable columns
        assert 'name="start_time"' in response.text
        assert 'name="end_time"' in response.text
        assert 'name="break_minutes"' in response.text
        assert 'name="notes"' in response.text

    def test_get_edit_row_prepopulates_values(self, client, db_session):
        """Editable row pre-populates inputs with existing entry values."""
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            start_time=time(7, 30),
            end_time=time(16, 15),
            break_minutes=45,
            notes="Important meeting",
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/edit-row")

        assert response.status_code == 200
        # Should pre-populate with existing values
        assert "07:30" in response.text
        assert "16:15" in response.text
        assert "45" in response.text
        assert "Important meeting" in response.text

    def test_get_edit_row_contains_save_button(self, client, db_session):
        """Editable row contains Save button with PATCH action."""
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/edit-row")

        assert response.status_code == 200
        # Should contain Save button with PATCH action
        assert "Speichern" in response.text or "Save" in response.text
        assert (
            f'hx-patch="/time-entries/{entry.id}"' in response.text
            or f'hx-patch="/time-entries/{entry.id}"' in response.text
        )

    def test_get_edit_row_contains_cancel_button(self, client, db_session):
        """Editable row contains Cancel button to restore read-only row."""
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/edit-row")

        assert response.status_code == 200
        # Should contain Cancel button that loads read-only row
        assert "Abbrechen" in response.text or "Cancel" in response.text
        assert f'hx-get="/time-entries/{entry.id}/row"' in response.text

    def test_get_edit_row_not_found(self, client, db_session):
        """GET /time-entries/{id}/edit-row returns 404 for non-existent entry."""
        response = client.get("/time-entries/99999/edit-row")

        assert response.status_code == 404

    def test_get_row_success(self, client, db_session):
        """GET /time-entries/{id}/row returns 200 with read-only row HTML."""
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            start_time=time(7, 0),
            end_time=time(15, 0),
            break_minutes=30,
            notes="Test notes",
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/row")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Should contain entry data
        assert "15.01.26" in response.text or "2026-01-15" in response.text

    def test_get_row_contains_readonly_display(self, client, db_session):
        """Read-only row displays data without form inputs."""
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            start_time=time(7, 0),
            end_time=time(15, 0),
            break_minutes=30,
            notes="Read-only test",
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/row")

        assert response.status_code == 200
        # Should NOT contain form inputs (read-only)
        assert 'name="start_time"' not in response.text
        assert 'name="end_time"' not in response.text
        # Should display the values as text
        assert "07:00" in response.text
        assert "15:00" in response.text
        assert "Read-only test" in response.text

    def test_get_row_clickable_for_editing(self, client, db_session):
        """Read-only row is clickable to switch to edit mode."""
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/row")

        assert response.status_code == 200
        # Row should have hx-get pointing to edit-row endpoint
        assert f'hx-get="/time-entries/{entry.id}/edit-row"' in response.text

    def test_get_row_not_found(self, client, db_session):
        """GET /time-entries/{id}/row returns 404 for non-existent entry."""
        response = client.get("/time-entries/99999/row")

        assert response.status_code == 404

    def test_get_new_row_success(self, client, db_session):
        """GET /time-entries/new-row returns 200 with editable row HTML."""
        response = client.get("/time-entries/new-row")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_get_new_row_contains_form_inputs(self, client, db_session):
        """New row contains form inputs for all editable fields."""
        response = client.get("/time-entries/new-row")

        assert response.status_code == 200
        # Should contain inputs for all editable fields
        assert 'name="work_date"' in response.text
        assert 'name="start_time"' in response.text
        assert 'name="end_time"' in response.text
        assert 'name="break_minutes"' in response.text
        assert 'name="notes"' in response.text

    def test_get_new_row_contains_save_button(self, client, db_session):
        """New row contains Save button with POST action."""
        response = client.get("/time-entries/new-row")

        assert response.status_code == 200
        # Should contain Save button with POST action
        assert "Speichern" in response.text or "Save" in response.text
        assert 'hx-post="/time-entries"' in response.text

    def test_get_new_row_contains_cancel_button(self, client, db_session):
        """New row contains Cancel button to remove the row."""
        response = client.get("/time-entries/new-row")

        assert response.status_code == 200
        # Should contain Cancel button (likely removes the row or swaps it out)
        assert "Abbrechen" in response.text or "Cancel" in response.text

    def test_get_new_row_accepts_date_param(self, client, db_session):
        """GET /time-entries/new-row?date=2026-01-20 accepts date query parameter."""
        response = client.get("/time-entries/new-row?date=2026-01-20")

        assert response.status_code == 200
        # Should accept date parameter without error
        assert "text/html" in response.headers["content-type"]

    def test_get_new_row_prepopulates_date_from_param(self, client, db_session):
        """New row pre-populates work_date from query parameter."""
        response = client.get("/time-entries/new-row?date=2026-01-20")

        assert response.status_code == 200
        # Should pre-populate date field with provided date
        assert "2026-01-20" in response.text or "20.01.2026" in response.text or "20.01.26" in response.text

    def test_get_new_row_without_date_param(self, client, db_session):
        """GET /time-entries/new-row without date parameter still works."""
        response = client.get("/time-entries/new-row")

        assert response.status_code == 200
        # Should work without date parameter (may use today's date or leave blank)
        assert "text/html" in response.headers["content-type"]

    def test_inline_edit_preserves_row_id(self, client, db_session):
        """Edit row preserves the row's id attribute for HTMX swapping."""
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/edit-row")

        assert response.status_code == 200
        # Should have row id for proper HTMX swap targeting
        assert f'id="time-entry-row-{entry.id}"' in response.text or f"id='time-entry-row-{entry.id}'" in response.text

    def test_readonly_row_preserves_row_id(self, client, db_session):
        """Read-only row preserves the row's id attribute for HTMX swapping."""
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/row")

        assert response.status_code == 200
        # Should have row id for proper HTMX swap targeting
        assert f'id="time-entry-row-{entry.id}"' in response.text or f"id='time-entry-row-{entry.id}'" in response.text


class TestNewRowWeekdayDefaults:
    """Test GET /time-entries/new-row with weekday defaults."""

    def test_new_row_uses_weekday_defaults(self, client, db_session):
        """New row pre-populates with weekday defaults from settings."""
        # Create settings with custom Monday defaults
        settings = UserSettingsFactory.build(
            user_id=1,
            weekly_target_hours=Decimal("40.00"),
            schedule_json={
                "weekday_defaults": {
                    "0": {"start_time": "09:00", "end_time": "17:30", "break_minutes": 45},
                }
            },
        )
        db_session.add(settings)
        db_session.commit()

        # Request new row for a Monday (2026-01-19 is a Monday)
        response = client.get("/time-entries/new-row?date=2026-01-19")

        assert response.status_code == 200
        # Should contain the custom default values
        assert "09:00" in response.text  # start_time
        assert "17:30" in response.text  # end_time
        assert "45" in response.text  # break_minutes
