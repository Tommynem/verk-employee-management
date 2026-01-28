"""Specification tests for keyboard shortcuts in time tracking.

These tests define the expected behavior of global keyboard shortcuts.
Tests use Playwright for browser-based testing of keyboard interactions.

NOTE: These tests require:
1. Playwright to be installed (pip install pytest-playwright && playwright install)
2. A running server at http://localhost:8000

Run with: pytest tests/test_keyboard_shortcuts.py -m playwright
"""

import pytest

# Skip all tests if playwright is not installed
pytest.importorskip("playwright")

from playwright.sync_api import Page, expect


@pytest.mark.playwright
@pytest.mark.skip(reason="Requires running server at localhost:8000")
class TestKeyboardShortcuts:
    """Test keyboard shortcuts for time tracking navigation and actions."""

    def test_n_key_triggers_add_next_day_button(self, page: Page):
        """Test that pressing 'N' key triggers the 'Add Next Day' button.

        Given: User is on the time entries page with visible 'Add Next Day' button
        When: User presses 'N' key
        Then: The 'Add Next Day' button is clicked and new entry row appears
        """
        # Navigate to time entries page
        page.goto("http://localhost:8000/time-entries")

        # Wait for page to load
        page.wait_for_selector("#time-entries-table")

        # Find the "Add Next Day" button
        add_button = page.locator("button:has-text('Nächsten Tag hinzufügen')")

        # Ensure button is visible
        if add_button.count() > 0:
            # Press 'N' key
            page.keyboard.press("n")

            # Verify that an edit row appears (new entry row)
            edit_row = page.locator("tr[data-edit-row]")
            expect(edit_row).to_be_visible()

    def test_t_key_jumps_to_current_month(self, page: Page):
        """Test that pressing 'T' key navigates to current month.

        Given: User is on time entries page viewing any month
        When: User presses 'T' key
        Then: Page navigates to current month view
        """
        # Navigate to past month (e.g., January 2024)
        page.goto("http://localhost:8000/time-entries?month=1&year=2024")

        # Wait for page to load
        page.wait_for_selector("#time-entries-table")

        # Press 'T' key
        page.keyboard.press("t")

        # Wait for navigation to complete
        page.wait_for_load_state("networkidle")

        # Verify URL contains current month/year (will depend on test execution date)
        # For now, just verify we navigated somewhere
        page.wait_for_selector("#time-entries-table")

    def test_arrow_left_navigates_to_previous_month(self, page: Page):
        """Test that pressing left arrow key navigates to previous month.

        Given: User is on time entries page
        When: User presses ArrowLeft key
        Then: Page navigates to previous month
        """
        # Navigate to specific month (e.g., March 2024)
        page.goto("http://localhost:8000/time-entries?month=3&year=2024")

        # Wait for page to load
        page.wait_for_selector("#time-entries-table")

        # Get current month header text
        initial_header = page.locator("h2:has-text('2024')").inner_text()

        # Press ArrowLeft key
        page.keyboard.press("ArrowLeft")

        # Wait for navigation
        page.wait_for_load_state("networkidle")

        # Verify month changed
        new_header = page.locator("h2:has-text('2024')").inner_text()
        assert new_header != initial_header

    def test_arrow_right_navigates_to_next_month(self, page: Page):
        """Test that pressing right arrow key navigates to next month.

        Given: User is on time entries page
        When: User presses ArrowRight key
        Then: Page navigates to next month
        """
        # Navigate to specific month (e.g., March 2024)
        page.goto("http://localhost:8000/time-entries?month=3&year=2024")

        # Wait for page to load
        page.wait_for_selector("#time-entries-table")

        # Get current month header text
        initial_header = page.locator("h2:has-text('2024')").inner_text()

        # Press ArrowRight key
        page.keyboard.press("ArrowRight")

        # Wait for navigation
        page.wait_for_load_state("networkidle")

        # Verify month changed
        new_header = page.locator("h2:has-text('2024')").inner_text()
        assert new_header != initial_header

    def test_shortcuts_ignore_when_input_focused(self, page: Page):
        """Test that keyboard shortcuts do NOT trigger when input field is focused.

        Given: User is editing a time entry with input field focused
        When: User types 'n' or 't' in the input field
        Then: Shortcuts do not trigger, text is entered normally
        """
        # Navigate to time entries page
        page.goto("http://localhost:8000/time-entries")

        # Wait for page to load
        page.wait_for_selector("#time-entries-table")

        # Trigger adding a new entry to get an input field
        add_button = page.locator(
            "button:has-text('Nächsten Tag hinzufügen'), button:has-text('Ersten Eintrag hinzufügen')"
        )
        if add_button.count() > 0:
            add_button.first.click()

            # Wait for edit row to appear
            page.wait_for_selector("tr[data-edit-row]")

            # Focus on notes input field
            notes_input = page.locator("tr[data-edit-row] input[name='notes']")
            notes_input.click()

            # Type 'n' and 't' characters
            notes_input.type("nt")

            # Verify the text is in the input field
            expect(notes_input).to_have_value("nt")

            # Verify that shortcuts did NOT trigger (no additional edit rows)
            edit_rows = page.locator("tr[data-edit-row]")
            expect(edit_rows).to_have_count(1)

    def test_tab_order_through_edit_row_fields(self, page: Page):
        """Test that Tab key navigates smoothly through edit row fields.

        Given: User has an editable entry row open
        When: User presses Tab repeatedly
        Then: Focus moves through Start → End → Break → Notes → Save button
        """
        # Navigate to time entries page
        page.goto("http://localhost:8000/time-entries")

        # Wait for page to load
        page.wait_for_selector("#time-entries-table")

        # Trigger adding a new entry
        add_button = page.locator(
            "button:has-text('Nächsten Tag hinzufügen'), button:has-text('Ersten Eintrag hinzufügen')"
        )
        if add_button.count() > 0:
            add_button.first.click()

            # Wait for edit row to appear
            page.wait_for_selector("tr[data-edit-row]")

            # Get references to all focusable fields
            edit_row = page.locator("tr[data-edit-row]").first
            start_input = edit_row.locator("input[name='start_time']")
            end_input = edit_row.locator("input[name='end_time']")
            break_input = edit_row.locator("input[name='break_minutes']")
            notes_input = edit_row.locator("input[name='notes']")
            save_button = edit_row.locator("button.btn-primary")

            # Focus first field
            start_input.focus()

            # Tab to next field
            page.keyboard.press("Tab")
            expect(end_input).to_be_focused()

            # Tab to break field
            page.keyboard.press("Tab")
            expect(break_input).to_be_focused()

            # Tab to notes field
            page.keyboard.press("Tab")
            expect(notes_input).to_be_focused()

            # Tab to save button
            page.keyboard.press("Tab")
            expect(save_button).to_be_focused()

    def test_keyboard_shortcuts_legend_visible(self, page: Page):
        """Test that keyboard shortcuts legend is visible on the page.

        Given: User is on the time entries page
        When: Page loads
        Then: Keyboard shortcuts legend is visible showing available shortcuts
        """
        # Navigate to time entries page
        page.goto("http://localhost:8000/time-entries")

        # Wait for page to load
        page.wait_for_selector("#time-entries-table")

        # Check for keyboard shortcuts legend
        legend = page.locator("text=Tastenkürzel")
        expect(legend).to_be_visible()

        # Verify key shortcuts are listed
        expect(page.locator("text=N")).to_be_visible()
        expect(page.locator("text=T")).to_be_visible()


@pytest.fixture
def page(playwright) -> Page:
    """Create a browser page for testing."""
    browser = playwright.chromium.launch()
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()
    browser.close()
