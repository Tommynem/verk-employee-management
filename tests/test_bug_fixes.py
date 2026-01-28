"""Tests for bug fixes found during Playwright testing.

This module contains TDD tests that verify fixes for bugs identified during
manual Playwright testing.

NOTE: These tests require:
1. Playwright to be installed (pip install pytest-playwright && playwright install)
2. A running server at http://localhost:8000

Run with: pytest tests/test_bug_fixes.py -m playwright
"""

import pytest

# Skip all tests if playwright is not installed
pytest.importorskip("playwright")

from playwright.sync_api import Page, expect


@pytest.mark.playwright
@pytest.mark.skip(reason="Requires running server at localhost:8000")
class TestBug1And2InvalidTimeInput:
    """Test that invalid time inputs are rejected and cleared.

    BUG #1-2: Invalid time input accepted - "25" and "abc" are accepted
    in time fields without validation. The formatTimeInput function should
    clear invalid inputs instead of returning the original value.
    """

    def test_invalid_hour_25_is_cleared_on_blur(self, page: Page):
        """Test that entering hour '25' clears the field on blur.

        Given: User is editing a time entry row
        When: User enters '25' in start_time field and blurs
        Then: Field should be empty (invalid hour >= 24)
        """
        page.goto("http://localhost:8000/time-entries")
        page.wait_for_selector("#time-entries-table")

        # Click "Add Next Day" to get edit row
        add_button = page.locator("button:has-text('Nächsten Tag hinzufügen')")
        if add_button.count() > 0:
            add_button.click()

        # Wait for edit row
        edit_row = page.locator("tr[data-edit-row]")
        expect(edit_row).to_be_visible()

        # Find start_time input
        start_time_input = edit_row.locator('input[name="start_time"]')

        # Type "25" (invalid hour)
        start_time_input.fill("25")

        # Blur the field (click somewhere else)
        page.locator("body").click()

        # Wait a moment for blur event to process
        page.wait_for_timeout(100)

        # Verify field is empty (not "25" or "25:00")
        value = start_time_input.input_value()
        assert value == "", f"Expected empty string for invalid input '25', got '{value}'"

    def test_invalid_text_abc_is_cleared_on_blur(self, page: Page):
        """Test that entering 'abc' (non-numeric) clears the field on blur.

        Given: User is editing a time entry row
        When: User enters 'abc' in start_time field and blurs
        Then: Field should be empty (invalid non-numeric input)
        """
        page.goto("http://localhost:8000/time-entries")
        page.wait_for_selector("#time-entries-table")

        # Click "Add Next Day" to get edit row
        add_button = page.locator("button:has-text('Nächsten Tag hinzufügen')")
        if add_button.count() > 0:
            add_button.click()

        # Wait for edit row
        edit_row = page.locator("tr[data-edit-row]")
        expect(edit_row).to_be_visible()

        # Find start_time input
        start_time_input = edit_row.locator('input[name="start_time"]')

        # Type "abc" (invalid text)
        start_time_input.fill("abc")

        # Blur the field
        page.locator("body").click()

        # Wait a moment for blur event
        page.wait_for_timeout(100)

        # Verify field is empty
        value = start_time_input.input_value()
        assert value == "", f"Expected empty string for invalid input 'abc', got '{value}'"

    def test_invalid_minute_12_60_is_cleared_on_blur(self, page: Page):
        """Test that entering '12:60' (invalid minute) clears the field on blur.

        Given: User is editing a time entry row
        When: User enters '12:60' in start_time field and blurs
        Then: Field should be empty (minute >= 60 is invalid)
        """
        page.goto("http://localhost:8000/time-entries")
        page.wait_for_selector("#time-entries-table")

        # Click "Add Next Day" to get edit row
        add_button = page.locator("button:has-text('Nächsten Tag hinzufügen')")
        if add_button.count() > 0:
            add_button.click()

        # Wait for edit row
        edit_row = page.locator("tr[data-edit-row]")
        expect(edit_row).to_be_visible()

        # Find start_time input
        start_time_input = edit_row.locator('input[name="start_time"]')

        # Type "12:60" (invalid minute)
        start_time_input.fill("12:60")

        # Blur the field
        page.locator("body").click()

        # Wait a moment
        page.wait_for_timeout(100)

        # Verify field is empty
        value = start_time_input.input_value()
        assert value == "", f"Expected empty string for invalid input '12:60', got '{value}'"


@pytest.mark.playwright
class TestBug3DateFieldCorruption:
    """Test that date field displays correctly when adding new entry.

    BUG #3: Date field corruption showing "ID-150/2526" - When adding new entry,
    date sometimes shows corrupted value that looks like part of a row ID got mixed in.
    """

    def test_new_entry_date_field_has_valid_date_format(self, page: Page):
        """Test that new entry date field shows valid YYYY-MM-DD format.

        Given: User is on time entries page
        When: User clicks "Add Next Day" button
        Then: Date input field should contain valid YYYY-MM-DD format (not corrupted)
        """
        page.goto("http://localhost:8000/time-entries")
        page.wait_for_selector("#time-entries-table")

        # Click "Add Next Day"
        add_button = page.locator("button:has-text('Nächsten Tag hinzufügen')")
        if add_button.count() > 0:
            add_button.click()

        # Wait for edit row
        edit_row = page.locator("tr[data-edit-row]")
        expect(edit_row).to_be_visible()

        # Find date input (for new entries)
        date_input = edit_row.locator('input[name="work_date"][type="date"]')

        # Verify date input exists
        expect(date_input).to_be_visible()

        # Get the value
        date_value = date_input.input_value()

        # Verify it's a valid date format (YYYY-MM-DD) or empty
        if date_value:
            # Should match YYYY-MM-DD format
            import re

            assert re.match(
                r"^\d{4}-\d{2}-\d{2}$", date_value
            ), f"Expected valid date format YYYY-MM-DD, got '{date_value}'"
            # Should NOT contain "ID-" or other corruption
            assert "ID-" not in date_value, f"Date value corrupted with row ID: '{date_value}'"

    def test_new_entry_date_field_not_corrupted_with_row_id(self, page: Page):
        """Test that date field doesn't contain row ID fragments.

        Given: User adds multiple new entries
        When: Each new entry is created
        Then: Date field should never contain fragments like "ID-150"
        """
        page.goto("http://localhost:8000/time-entries")
        page.wait_for_selector("#time-entries-table")

        # Add new entry multiple times to test consistency
        for i in range(3):
            # Click "Add Next Day"
            add_button = page.locator("button:has-text('Nächsten Tag hinzufügen')")
            if add_button.count() > 0:
                add_button.click()

            # Wait for edit row
            edit_row = page.locator("tr[data-edit-row]")
            expect(edit_row).to_be_visible()

            # Find date input
            date_input = edit_row.locator('input[name="work_date"][type="date"]')

            # Get the value
            date_value = date_input.input_value()

            # Verify no corruption
            assert "ID-" not in str(date_value), f"Iteration {i+1}: Date value corrupted: '{date_value}'"
            assert "time-entry-row-" not in str(
                date_value
            ), f"Iteration {i+1}: Date value contains row ID: '{date_value}'"

            # Cancel to clean up
            cancel_button = edit_row.locator('button[title="Abbrechen"]')
            if cancel_button.count() > 0:
                cancel_button.click()
                page.wait_for_timeout(100)


@pytest.mark.playwright
class TestBug4MissingVisualFeedbackAbsenceButtons:
    """Test that absence buttons show visual feedback when clicked.

    BUG #4: Missing visual feedback for active absence buttons - Clicking absence
    button doesn't show visual change. The styling exists but daisyUI btn-ghost
    might be overriding the custom classes.
    """

    def test_vacation_button_shows_active_state_after_click(self, page: Page):
        """Test that vacation button shows active styling after click.

        Given: User has a time entry row visible
        When: User clicks the vacation (Urlaub) button
        Then: Button should have visible active styling (bg-primary/20 or similar)
        """
        page.goto("http://localhost:8000/time-entries")
        page.wait_for_selector("#time-entries-table")

        # Find first time entry row (not edit row)
        entry_row = page.locator("tr[id^='time-entry-row-']:not([data-edit-row])").first

        if entry_row.count() > 0:
            # Find vacation button (tree-palm icon)
            vacation_button = entry_row.locator('button[title="Urlaub"]')

            # Get initial class list
            initial_classes = vacation_button.get_attribute("class")

            # Click the button
            vacation_button.click()

            # Wait for HTMX to swap the row
            page.wait_for_timeout(500)

            # Find the button again (row was swapped)
            vacation_button = entry_row.locator('button[title="Urlaub"]')

            # Get updated class list
            updated_classes = vacation_button.get_attribute("class")

            # Verify button has active state styling
            # Should have "bg-primary/20" or "border-primary"
            assert (
                "bg-primary" in updated_classes or "border-primary" in updated_classes
            ), f"Expected active state styling, got classes: {updated_classes}"

            # Verify button looks different from initial state
            assert initial_classes != updated_classes, "Button classes should change after activation"

    def test_sick_button_shows_active_state_after_click(self, page: Page):
        """Test that sick button shows active styling after click.

        Given: User has a time entry row visible
        When: User clicks the sick (Krank) button
        Then: Button should have visible active styling (bg-error/20 or similar)
        """
        page.goto("http://localhost:8000/time-entries")
        page.wait_for_selector("#time-entries-table")

        # Find first time entry row
        entry_row = page.locator("tr[id^='time-entry-row-']:not([data-edit-row])").first

        if entry_row.count() > 0:
            # Find sick button (thermometer icon)
            sick_button = entry_row.locator('button[title="Krank"]')

            # Click the button
            sick_button.click()

            # Wait for HTMX swap
            page.wait_for_timeout(500)

            # Find the button again
            sick_button = entry_row.locator('button[title="Krank"]')

            # Get class list
            classes = sick_button.get_attribute("class")

            # Verify active state
            assert (
                "bg-error" in classes or "border-error" in classes
            ), f"Expected sick button active styling, got: {classes}"


@pytest.mark.playwright
class TestBug5EscapeKeyNotWorkingToCancel:
    """Test that Escape key cancels edit mode.

    BUG #5: Escape key not working to cancel edit - The handler exists but the
    .btn-ghost selector might not be specific enough, or there are multiple
    .btn-ghost buttons confusing the selector.
    """

    def test_escape_key_cancels_edit_mode_on_existing_entry(self, page: Page):
        """Test that pressing Escape cancels edit mode on existing entry.

        Given: User is editing an existing time entry
        When: User presses Escape key
        Then: Edit mode should be cancelled and row returns to read-only view
        """
        page.goto("http://localhost:8000/time-entries")
        page.wait_for_selector("#time-entries-table")

        # Find first time entry row and click to enter edit mode
        entry_row = page.locator("tr[id^='time-entry-row-']:not([data-edit-row])").first

        if entry_row.count() > 0:
            entry_row.click()

            # Wait for edit row to appear
            edit_row = page.locator("tr[data-edit-row]")
            expect(edit_row).to_be_visible()

            # Verify we're in edit mode (input fields visible)
            start_time_input = edit_row.locator('input[name="start_time"]')
            expect(start_time_input).to_be_visible()

            # Press Escape key
            page.keyboard.press("Escape")

            # Wait a moment for event processing
            page.wait_for_timeout(200)

            # Verify we're back in read-only mode (edit row gone)
            # The edit row should be replaced with read-only row
            expect(edit_row).not_to_be_attached()

    def test_escape_key_cancels_new_entry(self, page: Page):
        """Test that pressing Escape cancels new entry creation.

        Given: User is creating a new time entry
        When: User presses Escape key
        Then: New entry row should be removed
        """
        page.goto("http://localhost:8000/time-entries")
        page.wait_for_selector("#time-entries-table")

        # Click "Add Next Day"
        add_button = page.locator("button:has-text('Nächsten Tag hinzufügen')")
        if add_button.count() > 0:
            add_button.click()

        # Wait for edit row
        edit_row = page.locator("tr[data-edit-row]")
        expect(edit_row).to_be_visible()

        # Verify we're in edit mode
        start_time_input = edit_row.locator('input[name="start_time"]')
        expect(start_time_input).to_be_visible()

        # Press Escape key
        page.keyboard.press("Escape")

        # Wait for event processing
        page.wait_for_timeout(200)

        # Verify edit row is gone
        expect(edit_row).not_to_be_attached()

    def test_escape_key_works_when_focus_on_input_field(self, page: Page):
        """Test that Escape works even when focus is on an input field.

        Given: User is editing an entry and focus is on a text input
        When: User presses Escape key
        Then: Edit mode should be cancelled regardless of focus
        """
        page.goto("http://localhost:8000/time-entries")
        page.wait_for_selector("#time-entries-table")

        # Find and click first entry to edit
        entry_row = page.locator("tr[id^='time-entry-row-']:not([data-edit-row])").first

        if entry_row.count() > 0:
            entry_row.click()

            # Wait for edit row
            edit_row = page.locator("tr[data-edit-row]")
            expect(edit_row).to_be_visible()

            # Focus on start_time input
            start_time_input = edit_row.locator('input[name="start_time"]')
            start_time_input.click()
            expect(start_time_input).to_be_focused()

            # Press Escape while input is focused
            page.keyboard.press("Escape")

            # Wait for processing
            page.wait_for_timeout(200)

            # Verify edit cancelled
            expect(edit_row).not_to_be_attached()
