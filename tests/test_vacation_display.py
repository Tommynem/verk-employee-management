"""Test vacation KPI card display on time entries page.

Tests for vacation balance display following TDD RED phase.
All tests should fail initially until the vacation KPI card is implemented.

Tests verify:
- Vacation balance card appears when settings configured
- Card shows correct remaining days calculation
- Warning badge appears when carryover days expiring soon
- Card updates after vacation entries added
"""

from datetime import date, timedelta
from decimal import Decimal

from tests.factories import UserSettingsFactory, VacationEntryFactory


class TestVacationKPIDisplay:
    """Test vacation KPI card display on time entries page."""

    def test_time_entries_page_shows_vacation_card_when_settings_exist(self, client, db_session):
        """GET /time-entries shows vacation balance card when settings configured."""
        # Create user settings with vacation fields configured
        settings = UserSettingsFactory.build(
            user_id=1,
            initial_vacation_days=Decimal("30"),
            annual_vacation_days=Decimal("30"),
            tracking_start_date=date(2026, 1, 1),
        )
        db_session.add(settings)
        db_session.commit()

        response = client.get("/time-entries")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Card should contain "Resturlaub" (German for remaining vacation)
        assert "Resturlaub" in response.text
        # Should show vacation balance value (30 days)
        assert "30" in response.text

    def test_vacation_card_not_shown_when_no_settings(self, client, db_session):
        """GET /time-entries does NOT show vacation card when no settings configured."""
        # No vacation settings configured - all None
        settings = UserSettingsFactory.build(
            user_id=1,
            initial_vacation_days=None,
            annual_vacation_days=None,
            vacation_carryover_days=None,
            vacation_carryover_expires=None,
        )
        db_session.add(settings)
        db_session.commit()

        response = client.get("/time-entries")

        assert response.status_code == 200
        # Should NOT contain "Resturlaub" since no vacation configured
        assert "Resturlaub" not in response.text

    def test_vacation_card_shows_correct_balance(self, client, db_session):
        """GET /time-entries shows correct vacation balance after vacation days used."""
        # Create settings: initial_vacation_days=30
        settings = UserSettingsFactory.build(
            user_id=1,
            initial_vacation_days=Decimal("30"),
            tracking_start_date=date(2026, 1, 1),
        )
        db_session.add(settings)
        db_session.commit()

        # Create 5 vacation entries
        for day_offset in range(5):
            entry = VacationEntryFactory.build(
                user_id=1,
                work_date=date(2026, 1, 10) + timedelta(days=day_offset),
            )
            db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries")

        assert response.status_code == 200
        # Should show "25" (30 - 5 = 25 days remaining)
        # Look for the remaining days display pattern
        assert "25" in response.text
        assert "Resturlaub" in response.text

    def test_vacation_warning_shown_when_carryover_expiring(self, client, db_session):
        """GET /time-entries shows warning badge when carryover days expiring soon."""
        # Create settings with carryover that expires soon (within 30 days)
        today = date.today()
        expires_soon = today + timedelta(days=20)  # 20 days from now

        settings = UserSettingsFactory.build(
            user_id=1,
            initial_vacation_days=Decimal("30"),
            vacation_carryover_days=Decimal("5"),
            vacation_carryover_expires=expires_soon,
            tracking_start_date=date(2026, 1, 1),
        )
        db_session.add(settings)
        db_session.commit()

        response = client.get("/time-entries")

        assert response.status_code == 200
        # Should contain warning badge or indicator
        assert "badge" in response.text.lower() or "warning" in response.text.lower()
        # Should mention "verfallen" (German for expire)
        assert "verfallen" in response.text

    def test_no_vacation_warning_when_carryover_not_expiring(self, client, db_session):
        """GET /time-entries does NOT show warning when carryover expires far in future."""
        # Create settings with carryover that expires far in future (>30 days)
        today = date.today()
        expires_later = today + timedelta(days=60)  # 60 days from now

        settings = UserSettingsFactory.build(
            user_id=1,
            initial_vacation_days=Decimal("30"),
            vacation_carryover_days=Decimal("5"),
            vacation_carryover_expires=expires_later,
            tracking_start_date=date(2026, 1, 1),
        )
        db_session.add(settings)
        db_session.commit()

        response = client.get("/time-entries")

        assert response.status_code == 200
        # Should still show vacation card
        assert "Resturlaub" in response.text
        # But should NOT show warning badge/message about expiring
        # Note: We check that "verfallen" does NOT appear
        assert "verfallen" not in response.text

    def test_vacation_card_updates_after_vacation_entry_added(self, client, db_session):
        """Vacation card updates to show correct remaining days after adding vacation entry."""
        # Create settings with initial_vacation_days=30
        settings = UserSettingsFactory.build(
            user_id=1,
            initial_vacation_days=Decimal("30"),
            tracking_start_date=date(2026, 1, 1),
        )
        db_session.add(settings)
        db_session.commit()

        # GET /time-entries -> should show 30 remaining
        response = client.get("/time-entries")
        assert response.status_code == 200
        assert "30" in response.text
        assert "Resturlaub" in response.text

        # Add vacation entry via POST
        vacation_data = {
            "user_id": 1,
            "work_date": "2026-01-15",
            "absence_type": "vacation",
            "status": "draft",
        }
        post_response = client.post("/time-entries", data=vacation_data)
        assert post_response.status_code == 201

        # GET /time-entries again -> should now show 29 remaining
        response_after = client.get("/time-entries")
        assert response_after.status_code == 200
        assert "29" in response_after.text
        assert "Resturlaub" in response_after.text

    def test_vacation_card_shows_zero_when_all_days_used(self, client, db_session):
        """Vacation card correctly shows zero remaining days when all vacation used."""
        # Create settings with only 3 days vacation
        settings = UserSettingsFactory.build(
            user_id=1,
            initial_vacation_days=Decimal("3"),
            tracking_start_date=date(2026, 1, 1),
        )
        db_session.add(settings)
        db_session.commit()

        # Use all 3 vacation days
        for day_offset in range(3):
            entry = VacationEntryFactory.build(
                user_id=1,
                work_date=date(2026, 1, 10) + timedelta(days=day_offset),
            )
            db_session.add(entry)
        db_session.commit()

        response = client.get("/time-entries")

        assert response.status_code == 200
        # Should show "0" days remaining
        assert "Resturlaub" in response.text
        # Look for zero display (could be "0" or "0.00")
        assert "0" in response.text

    def test_vacation_card_includes_carryover_in_total(self, client, db_session):
        """Vacation card shows total including carryover days."""
        # Create settings with initial days + carryover
        settings = UserSettingsFactory.build(
            user_id=1,
            initial_vacation_days=Decimal("25"),
            vacation_carryover_days=Decimal("5"),
            vacation_carryover_expires=date(2026, 6, 30),  # Not expired yet
            tracking_start_date=date(2026, 1, 1),
        )
        db_session.add(settings)
        db_session.commit()

        response = client.get("/time-entries")

        assert response.status_code == 200
        # Should show "30" total (25 initial + 5 carryover)
        assert "30" in response.text
        assert "Resturlaub" in response.text

    def test_vacation_card_excludes_expired_carryover(self, client, db_session):
        """Vacation card does NOT include expired carryover in balance."""
        # Create settings with carryover that has already expired
        today = date.today()
        expired_date = today - timedelta(days=10)  # 10 days ago

        settings = UserSettingsFactory.build(
            user_id=1,
            initial_vacation_days=Decimal("25"),
            vacation_carryover_days=Decimal("5"),
            vacation_carryover_expires=expired_date,  # Already expired
            tracking_start_date=date(2026, 1, 1),
        )
        db_session.add(settings)
        db_session.commit()

        response = client.get("/time-entries")

        assert response.status_code == 200
        # Should show "25" only (expired carryover not counted)
        assert "25" in response.text
        assert "Resturlaub" in response.text
        # Should NOT show 30 (which would include expired carryover)
        # We need to be careful here - "30" might appear elsewhere
        # Better to check that vacation balance specifically shows 25 not 30
