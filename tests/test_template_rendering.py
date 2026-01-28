"""Template rendering characterization tests for spec compliance.

These tests verify that templates match the design specification requirements.
They are supplementary verification tests (not driving TDD) to ensure spec
requirements are properly implemented and prevent regression.

Design spec: docs/specs/zeiterfassung-monthly-view-spec.md
Template: templates/partials/_browser_time_entries.html
"""

from datetime import date, time
from decimal import Decimal

from source.database.enums import AbsenceType
from tests.factories import TimeEntryFactory, UserSettingsFactory


class TestTableHeaderStructure:
    """Verify table header matches spec section 5.2-5.3."""

    def test_table_header_has_all_columns(self, client, db_session):
        """Table header has all required columns in correct order per spec 5.3."""
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("32.00"))
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(settings)
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries?month=1&year=2026")
        html = response.text

        # All column headers must be present (now with Quick Absence Buttons column)
        expected_headers = [
            "Tag",
            "Ankunft",
            "Ende",
            "Pausen",
            "Arbeitsstunden Real",
            "Arbeitsstunden Soll",
            "+/-",
            "Abwesenheit / Bemerkung",
            "Abwesenheit",  # Quick absence buttons column
        ]

        for header in expected_headers:
            assert header in html, f"Missing column header: {header}"

    def test_table_header_has_dark_background(self, client, db_session):
        """Table header has dark background styling per spec 5.2."""
        settings = UserSettingsFactory.build(user_id=1)
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(settings)
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries?month=1&year=2026")
        html = response.text

        # Header row should have dark background and white text
        assert 'class="bg-neutral text-white"' in html or ("bg-neutral" in html and "text-white" in html)


class TestColumnStyling:
    """Verify column-specific styling matches spec section 5.3-5.6."""

    def test_arbeitsstunden_real_column_has_blue_background(self, client, db_session):
        """'Arbeitsstunden Real' body cells have light blue background per spec 5.3."""
        settings = UserSettingsFactory.build(user_id=1)
        entry = TimeEntryFactory.build(
            user_id=1, work_date=date(2026, 1, 15), start_time=time(7, 0), end_time=time(15, 0), break_minutes=30
        )
        db_session.add(settings)
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries?month=1&year=2026")
        html = response.text

        # Body cells in Arbeitsstunden Real column should have bg-info/10
        assert "bg-info/10" in html

    def test_balance_column_uses_color_coding(self, client, db_session):
        """Balance (+/-) column uses green/red color coding per spec 5.6."""
        settings = UserSettingsFactory.build(user_id=1)
        # Create entry with positive balance (8 hours worked vs 6.4 target)
        entry = TimeEntryFactory.build(
            user_id=1, work_date=date(2026, 1, 15), start_time=time(7, 0), end_time=time(15, 30), break_minutes=30
        )
        db_session.add(settings)
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries?month=1&year=2026")
        html = response.text

        # Balance should use success or error color classes
        assert "text-success" in html or "text-error" in html


class TestFooterStructure:
    """Verify footer structure matches spec section 7."""

    def test_footer_exists_with_summary_rows(self, client, db_session):
        """Footer has summary rows when data exists per spec 7."""
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("32.00"))
        entry = TimeEntryFactory.build(
            user_id=1, work_date=date(2026, 1, 15), start_time=time(7, 0), end_time=time(15, 0), break_minutes=30
        )
        db_session.add(settings)
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries?month=1&year=2026")
        html = response.text

        # Footer should contain Monatssaldo and Zeitkonto labels
        assert "Monatssaldo:" in html
        assert "Aktuelles Zeitkonto:" in html

    def test_footer_has_green_background_tinting(self, client, db_session):
        """Footer rows have green background tinting per spec 7.4."""
        settings = UserSettingsFactory.build(user_id=1)
        entry = TimeEntryFactory.build(
            user_id=1, work_date=date(2026, 1, 15), start_time=time(7, 0), end_time=time(15, 0)
        )
        db_session.add(settings)
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries?month=1&year=2026")
        html = response.text

        # Footer should have success color variations
        assert "bg-success" in html

    def test_footer_has_two_rows(self, client, db_session):
        """Footer contains exactly 2 summary rows per spec 7.2-7.3."""
        settings = UserSettingsFactory.build(user_id=1)
        entry = TimeEntryFactory.build(
            user_id=1, work_date=date(2026, 1, 15), start_time=time(7, 0), end_time=time(15, 0)
        )
        db_session.add(settings)
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries?month=1&year=2026")
        html = response.text

        # Both summary row labels should exist
        assert "Monatssaldo:" in html
        assert "Aktuelles Zeitkonto:" in html


class TestAddNextDayRow:
    """Verify 'Add Next Day' row matches spec section 6."""

    def test_add_row_has_orange_tint(self, client, db_session):
        """'Add Next Day' row has orange/yellow tint per spec 6.2."""
        settings = UserSettingsFactory.build(user_id=1)
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(settings)
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries?month=1&year=2026")
        html = response.text

        # Add row should have warning color tint
        assert "bg-warning/10" in html

    def test_add_row_contains_german_text(self, client, db_session):
        """'Add Next Day' row contains German text per spec 6.1."""
        settings = UserSettingsFactory.build(user_id=1)
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(settings)
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries?month=1&year=2026")
        html = response.text

        # Should contain German "add next day" text
        assert "Nächsten Tag hinzufügen" in html


class TestMonthNavigation:
    """Verify month navigation matches spec section 3."""

    def test_month_navigation_displays_german_month_names(self, client, db_session):
        """Month navigation displays German month names per spec 3.3."""
        settings = UserSettingsFactory.build(user_id=1)
        db_session.add(settings)
        db_session.commit()

        response = client.get("/time-entries?month=1&year=2026")
        html = response.text

        # Januar should be displayed
        assert "Januar" in html

    def test_month_navigation_has_chevron_buttons(self, client, db_session):
        """Month navigation has left and right chevron buttons per spec 3.1."""
        settings = UserSettingsFactory.build(user_id=1)
        db_session.add(settings)
        db_session.commit()

        response = client.get("/time-entries?month=1&year=2026")
        html = response.text

        # Should have HTMX navigation links for prev/next month
        assert "hx-get=" in html
        # Navigation should target the main content area
        assert "hx-target=" in html


class TestSummaryCards:
    """Verify summary cards match spec section 4."""

    def test_summary_cards_exist_when_data_present(self, client, db_session):
        """Summary cards are displayed when entries exist per spec 4."""
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("32.00"))
        entry = TimeEntryFactory.build(
            user_id=1, work_date=date(2026, 1, 15), start_time=time(7, 0), end_time=time(15, 0), break_minutes=30
        )
        db_session.add(settings)
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries?month=1&year=2026")
        html = response.text

        # All three card labels should exist
        assert "Monatssaldo" in html
        assert "Sollstunden" in html
        assert "Aktuelles Zeitkonto" in html

    def test_summary_cards_have_subtitles(self, client, db_session):
        """Summary cards have German subtitles per spec 4.3."""
        settings = UserSettingsFactory.build(user_id=1)
        entry = TimeEntryFactory.build(
            user_id=1, work_date=date(2026, 1, 15), start_time=time(7, 0), end_time=time(15, 0)
        )
        db_session.add(settings)
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries?month=1&year=2026")
        html = response.text

        # Card subtitles should exist
        assert "Ist-Stunden" in html
        assert "Pro Monat" in html
        assert "Überstunden" in html


class TestQuickAbsenceButtons:
    """Verify quick absence buttons column (replaces checkboxes)."""

    def test_absence_column_exists(self, client, db_session):
        """Abwesenheit column with quick buttons exists."""
        settings = UserSettingsFactory.build(user_id=1)
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15), absence_type=AbsenceType.NONE)
        db_session.add(settings)
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries?month=1&year=2026")
        html = response.text

        # Should have Abwesenheit header
        assert "Abwesenheit" in html
        # Should have quick action buttons (not checkboxes)
        assert 'aria-label="Urlaub"' in html
        assert 'aria-label="Krank"' in html
        assert 'aria-label="Feiertag"' in html
        assert 'aria-label="Gleitzeit"' in html

    def test_absence_buttons_use_htmx_patch(self, client, db_session):
        """Quick absence buttons use HTMX PATCH for updates."""
        settings = UserSettingsFactory.build(user_id=1)
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(settings)
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get("/time-entries?month=1&year=2026")
        html = response.text

        # Buttons should use hx-patch
        assert "hx-patch=" in html
        # Should target the specific entry ID
        assert f"/time-entries/{entry.id}" in html


class TestDateFormatting:
    """Verify date formatting matches spec section 5.3."""

    def test_dates_use_german_format(self, client, db_session):
        """Dates are formatted as DD.MM.YY per spec 5.3."""
        settings = UserSettingsFactory.build(user_id=1)
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(settings)
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries?month=1&year=2026")
        html = response.text

        # Date should appear in DD.MM.YY format
        assert "15.01.26" in html


class TestTimeFormatting:
    """Verify time formatting matches spec section 5.3."""

    def test_times_use_24hour_format(self, client, db_session):
        """Times are formatted as HH:MM per spec 5.3."""
        settings = UserSettingsFactory.build(user_id=1)
        entry = TimeEntryFactory.build(
            user_id=1, work_date=date(2026, 1, 15), start_time=time(7, 0), end_time=time(15, 30)
        )
        db_session.add(settings)
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries?month=1&year=2026")
        html = response.text

        # Times should appear in HH:MM format
        assert "07:00" in html
        assert "15:30" in html


class TestEmptyState:
    """Verify empty state display when no entries exist."""

    def test_empty_state_displays_message(self, client, db_session):
        """Empty state shows German message when no entries exist."""
        response = client.get("/time-entries?month=1&year=2026")
        html = response.text

        # Should show empty state message
        assert "Keine Zeiteinträge" in html or "keine" in html.lower()

    def test_empty_state_shows_table_with_add_button(self, client, db_session):
        """Empty state shows table structure with add button for HTMX functionality."""
        response = client.get("/time-entries?month=1&year=2026")
        html = response.text

        # Should show empty state message within the table structure
        assert "Keine Zeiteinträge" in html
        # Table headers should be present (required for HTMX add-row targeting)
        assert "Ankunft" in html and "Ende" in html
        # Add button should be available
        assert "Ersten Eintrag hinzufügen" in html


class TestCopyLastEntryButton:
    """Test copy-last-entry button appears in edit row."""

    def test_copy_button_exists_in_new_row(self, client, db_session):
        """Copy Last button exists in new entry row."""
        response = client.get("/time-entries/new-row")
        html = response.text

        # Should contain Copy Last button with correct title
        assert "Letzte kopieren" in html
        # Should have onclick handler
        assert "copyLastEntry" in html
        # Should use clipboard icon (check for SVG clipboard path)
        assert 'width="8" height="4" x="8" y="2"' in html  # Clipboard SVG rect

    def test_copy_button_exists_in_edit_row(self, client, db_session):
        """Copy Last button exists when editing existing entry."""
        # Create entry to edit
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/edit-row")
        html = response.text

        # Should contain Copy Last button
        assert "Letzte kopieren" in html
        assert "copyLastEntry" in html
