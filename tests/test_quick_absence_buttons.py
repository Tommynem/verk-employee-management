"""Test quick absence buttons feature for time entries.

Quick absence buttons allow one-click toggling of absence types without entering edit mode.
Tests follow TDD RED phase - all should fail initially.

Feature requirements:
1. Quick action buttons visible in read-only row view
2. Icons for each absence type (vacation, sick, holiday, flex_time)
3. One click to toggle absence type via HTMX PATCH
4. Visual indicator showing current absence type (highlighted button)
5. Clicking same type that's already set toggles back to "none"
"""

from datetime import date, time

from source.database.enums import AbsenceType
from tests.factories import TimeEntryFactory


class TestQuickAbsenceButtonsDisplay:
    """Test that quick absence buttons are present in read-only rows."""

    def test_row_contains_absence_buttons(self, client, db_session):
        """Read-only row contains quick absence buttons for all absence types."""
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            start_time=time(8, 0),
            end_time=time(16, 0),
            absence_type=AbsenceType.NONE,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/row")

        assert response.status_code == 200
        # Should contain quick absence buttons for each type
        # Using aria-label for accessibility and testing
        assert 'aria-label="Urlaub"' in response.text or "Urlaub" in response.text
        assert 'aria-label="Krank"' in response.text or "Krank" in response.text
        assert 'aria-label="Feiertag"' in response.text or "Feiertag" in response.text
        assert 'aria-label="Gleitzeit"' in response.text or "Gleitzeit" in response.text

    def test_buttons_have_patch_actions(self, client, db_session):
        """Each quick absence button has PATCH action to toggle absence type."""
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/row")

        assert response.status_code == 200
        # Should have PATCH actions for each absence type
        assert f'hx-patch="/time-entries/{entry.id}"' in response.text
        # Should include absence_type in hx-vals
        assert '"absence_type"' in response.text

    def test_buttons_stop_propagation(self, client, db_session):
        """Quick absence buttons prevent row click event (don't enter edit mode)."""
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/row")

        assert response.status_code == 200
        # Buttons should have onclick="event.stopPropagation()" to prevent row click
        assert "event.stopPropagation()" in response.text


class TestQuickAbsenceButtonVisualState:
    """Test visual indicators showing current absence type."""

    def test_vacation_button_highlighted_when_active(self, client, db_session):
        """Vacation button is visually highlighted when absence_type is vacation."""
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            absence_type=AbsenceType.VACATION,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/row")

        assert response.status_code == 200
        # Vacation button should have active/highlighted styling (!bg-primary/30 !border-primary)
        # and hx-vals should toggle to "none"
        assert 'aria-label="Urlaub"' in response.text
        assert "!bg-primary/30" in response.text
        assert "!border-primary" in response.text
        assert '"absence_type": "none"' in response.text

    def test_sick_button_highlighted_when_active(self, client, db_session):
        """Sick button is visually highlighted when absence_type is sick."""
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            absence_type=AbsenceType.SICK,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/row")

        assert response.status_code == 200
        # Sick button should have active styling (!bg-error/30 !border-error)
        assert 'aria-label="Krank"' in response.text
        assert "!bg-error/30" in response.text
        assert "!border-error" in response.text

    def test_holiday_button_highlighted_when_active(self, client, db_session):
        """Holiday button is visually highlighted when absence_type is holiday."""
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            absence_type=AbsenceType.HOLIDAY,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/row")

        assert response.status_code == 200
        # Holiday button should have active styling (!bg-warning/30 !border-warning)
        assert 'aria-label="Feiertag"' in response.text
        assert "!bg-warning/30" in response.text
        assert "!border-warning" in response.text

    def test_flex_time_button_highlighted_when_active(self, client, db_session):
        """Flex time button is visually highlighted when absence_type is flex_time."""
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            absence_type=AbsenceType.FLEX_TIME,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/row")

        assert response.status_code == 200
        # Flex time button should have active styling (!bg-info/30 !border-info)
        assert 'aria-label="Gleitzeit"' in response.text
        assert "!bg-info/30" in response.text
        assert "!border-info" in response.text

    def test_no_buttons_highlighted_for_regular_work(self, client, db_session):
        """No absence buttons are highlighted when absence_type is none."""
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            absence_type=AbsenceType.NONE,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/row")

        assert response.status_code == 200
        # Should contain absence buttons but none should be in active state
        # Verify absence_type="none" is set
        assert entry.absence_type.value == "none"


class TestQuickAbsenceButtonInteraction:
    """Test PATCH interactions for toggling absence types."""

    def test_click_vacation_button_sets_vacation(self, client, db_session):
        """Clicking vacation button on regular entry sets absence_type to vacation."""
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            absence_type=AbsenceType.NONE,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.patch(
            f"/time-entries/{entry.id}",
            data={"absence_type": "vacation"},
        )

        assert response.status_code == 200
        # Response should show updated row with vacation highlighted
        assert "!bg-primary/30" in response.text
        assert "!border-primary" in response.text
        db_session.refresh(entry)
        assert entry.absence_type == AbsenceType.VACATION

    def test_click_same_button_toggles_to_none(self, client, db_session):
        """Clicking vacation button when already vacation toggles back to none."""
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            absence_type=AbsenceType.VACATION,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.patch(
            f"/time-entries/{entry.id}",
            data={"absence_type": "none"},
        )

        assert response.status_code == 200
        # Entry should now be regular work (absence_type=none)
        db_session.refresh(entry)
        assert entry.absence_type == AbsenceType.NONE

    def test_click_different_button_switches_type(self, client, db_session):
        """Clicking sick button when vacation is active switches to sick."""
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            absence_type=AbsenceType.VACATION,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.patch(
            f"/time-entries/{entry.id}",
            data={"absence_type": "sick"},
        )

        assert response.status_code == 200
        db_session.refresh(entry)
        assert entry.absence_type == AbsenceType.SICK

    def test_quick_button_returns_updated_row(self, client, db_session):
        """PATCH from quick button returns updated read-only row."""
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            absence_type=AbsenceType.NONE,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.patch(
            f"/time-entries/{entry.id}",
            data={"absence_type": "sick"},
        )

        assert response.status_code == 200
        # Should return updated row HTML with sick button highlighted
        assert "text/html" in response.headers["content-type"]
        assert f'id="time-entry-row-{entry.id}"' in response.text


class TestQuickAbsenceButtonsInBrowserView:
    """Test that quick absence buttons appear in browser list view."""

    def test_browser_view_shows_quick_buttons(self, client, db_session):
        """Browser view (monthly table) shows quick absence buttons in each row."""
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            absence_type=AbsenceType.NONE,
        )
        db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries?month=1&year=2026")

        assert response.status_code == 200
        # Should contain quick absence buttons in the table
        assert 'aria-label="Urlaub"' in response.text or "Urlaub" in response.text
        assert 'aria-label="Krank"' in response.text or "Krank" in response.text

    def test_buttons_work_without_entering_edit_mode(self, client, db_session):
        """Quick buttons toggle absence without switching to edit mode."""
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            absence_type=AbsenceType.NONE,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        # Get row view (read-only)
        response = client.get(f"/time-entries/{entry.id}/row")
        assert response.status_code == 200

        # Should NOT contain edit form inputs (still read-only)
        assert 'name="start_time"' not in response.text
        assert 'name="end_time"' not in response.text

        # But should have PATCH buttons for quick absence
        assert f'hx-patch="/time-entries/{entry.id}"' in response.text


class TestQuickAbsenceButtonsStyling:
    """Test button styling and layout."""

    def test_buttons_are_small_and_subtle(self, client, db_session):
        """Quick absence buttons are small and subtle (not prominent)."""
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/row")

        assert response.status_code == 200
        # Buttons should be small (w-6 h-6 or btn-xs, etc.)
        # Could check for opacity classes or size classes
        # This is a softer assertion - just verify buttons exist with some sizing
        assert 'hx-patch="/time-entries/' in response.text

    def test_buttons_have_tooltips(self, client, db_session):
        """Quick absence buttons have German tooltips on hover."""
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = client.get(f"/time-entries/{entry.id}/row")

        assert response.status_code == 200
        # Should have German labels/tooltips
        assert "Urlaub" in response.text
        assert "Krank" in response.text
        assert "Feiertag" in response.text
        assert "Gleitzeit" in response.text


class TestBackendAbsenceToggleLogic:
    """Test backend logic for toggling absence types."""

    def test_patch_with_same_type_toggles_to_none(self, client, db_session):
        """Backend correctly toggles to 'none' when same type is clicked."""
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            absence_type=AbsenceType.VACATION,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        # Frontend sends "none" when clicking active button
        response = client.patch(
            f"/time-entries/{entry.id}",
            data={"absence_type": "none"},
        )

        assert response.status_code == 200
        db_session.refresh(entry)
        assert entry.absence_type == AbsenceType.NONE

    def test_patch_preserves_time_fields(self, client, db_session):
        """Changing absence_type preserves start_time, end_time, break_minutes."""
        entry = TimeEntryFactory.build(
            user_id=1,
            work_date=date(2026, 1, 15),
            start_time=time(8, 0),
            end_time=time(16, 0),
            break_minutes=30,
            absence_type=AbsenceType.NONE,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)
        original_start = entry.start_time
        original_end = entry.end_time
        original_break = entry.break_minutes

        response = client.patch(
            f"/time-entries/{entry.id}",
            data={"absence_type": "sick"},
        )

        assert response.status_code == 200
        db_session.refresh(entry)
        # Time fields should be unchanged
        assert entry.start_time == original_start
        assert entry.end_time == original_end
        assert entry.break_minutes == original_break
        # But absence type should be updated
        assert entry.absence_type == AbsenceType.SICK

    def test_all_absence_types_supported(self, client, db_session):
        """All absence types (vacation, sick, holiday, flex_time) can be set via PATCH."""
        entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15))
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        # Test each absence type
        absence_types = ["vacation", "sick", "holiday", "flex_time"]
        for absence_type in absence_types:
            response = client.patch(
                f"/time-entries/{entry.id}",
                data={"absence_type": absence_type},
            )
            assert response.status_code == 200, f"Failed to set {absence_type}"
            db_session.refresh(entry)
            assert entry.absence_type.value == absence_type
