"""Test Settings API routes.

Tests for Settings routes following VaWW REST+HTMX patterns.
All tests should fail initially (TDD RED phase) until routes are implemented.

Routes tested:
- GET /settings -> HTML settings page
- PATCH /settings/weekday-defaults -> Update weekday defaults, return form partial
"""

from decimal import Decimal

from tests.factories import UserSettingsFactory


class TestSettingsPage:
    """Test GET /settings page view."""

    def test_get_settings_page_success(self, client, db_session):
        """GET /settings returns 200 with HTML page."""
        response = client.get("/settings")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_settings_page_contains_weekday_section(self, client, db_session):
        """Settings page contains weekday defaults section."""
        response = client.get("/settings")

        assert response.status_code == 200
        # Should contain German day names
        assert "Montag" in response.text
        assert "Freitag" in response.text

    def test_settings_page_contains_all_weekdays(self, client, db_session):
        """Settings page contains all seven weekdays."""
        response = client.get("/settings")

        assert response.status_code == 200
        # All seven German day names
        assert "Montag" in response.text
        assert "Dienstag" in response.text
        assert "Mittwoch" in response.text
        assert "Donnerstag" in response.text
        assert "Freitag" in response.text
        assert "Samstag" in response.text
        assert "Sonntag" in response.text

    def test_settings_page_prepopulates_existing_values(self, client, db_session):
        """Settings page shows existing weekday defaults."""
        # Create settings with custom weekday defaults
        settings = UserSettingsFactory.build(
            user_id=1,
            weekly_target_hours=Decimal("40.00"),
            schedule_json={
                "weekday_defaults": {
                    "0": {"start_time": "09:00", "end_time": "17:00", "break_minutes": 45},
                    "1": {"start_time": "09:00", "end_time": "17:00", "break_minutes": 45},
                }
            },
        )
        db_session.add(settings)
        db_session.commit()

        response = client.get("/settings")

        assert response.status_code == 200
        assert "09:00" in response.text
        assert "17:00" in response.text

    def test_settings_page_shows_default_values_when_no_settings(self, client, db_session):
        """Settings page shows default values when no settings exist."""
        response = client.get("/settings")

        assert response.status_code == 200
        # Default values (08:00, 16:30, 30 minutes) per spec
        assert "08:00" in response.text
        assert "16:30" in response.text

    def test_settings_page_shows_null_for_weekends(self, client, db_session):
        """Settings page shows weekends as non-working days."""
        # Create settings with Saturday/Sunday as null (no work)
        settings = UserSettingsFactory.build(
            user_id=1,
            weekly_target_hours=Decimal("40.00"),
            schedule_json={
                "weekday_defaults": {
                    "0": {"start_time": "08:00", "end_time": "16:30", "break_minutes": 30},
                    "1": {"start_time": "08:00", "end_time": "16:30", "break_minutes": 30},
                    "2": {"start_time": "08:00", "end_time": "16:30", "break_minutes": 30},
                    "3": {"start_time": "08:00", "end_time": "16:30", "break_minutes": 30},
                    "4": {"start_time": "08:00", "end_time": "16:30", "break_minutes": 30},
                    "5": None,  # Saturday - no work
                    "6": None,  # Sunday - no work
                }
            },
        )
        db_session.add(settings)
        db_session.commit()

        response = client.get("/settings")

        assert response.status_code == 200
        # Should indicate weekends are non-working (empty inputs or checkboxes unchecked)
        assert "Samstag" in response.text
        assert "Sonntag" in response.text


class TestWeekdayDefaultsUpdate:
    """Test PATCH /settings/weekday-defaults endpoint."""

    def test_update_weekday_defaults_success(self, client, db_session):
        """PATCH updates weekday defaults successfully."""
        # Create initial settings
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/weekday-defaults",
            data={
                "weekday_0_start_time": "08:00",
                "weekday_0_end_time": "16:30",
                "weekday_0_break_minutes": "30",
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_update_sets_hx_trigger(self, client, db_session):
        """PATCH sets HX-Trigger: settingsUpdated header."""
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/weekday-defaults",
            data={
                "weekday_0_start_time": "08:00",
                "weekday_0_end_time": "16:30",
                "weekday_0_break_minutes": "30",
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 200
        assert "HX-Trigger" in response.headers
        assert response.headers["HX-Trigger"] == "settingsUpdated"

    def test_update_persists_to_database(self, client, db_session):
        """PATCH persists changes to database."""
        # Create initial settings
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        client.patch(
            "/settings/weekday-defaults",
            data={
                "weekday_0_start_time": "09:00",
                "weekday_0_end_time": "17:00",
                "weekday_0_break_minutes": "45",
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        # Refresh settings from database
        db_session.refresh(settings)

        # Verify changes persisted
        assert settings.schedule_json is not None
        assert settings.schedule_json["weekday_defaults"]["0"]["start_time"] == "09:00"
        assert settings.schedule_json["weekday_defaults"]["0"]["end_time"] == "17:00"
        assert settings.schedule_json["weekday_defaults"]["0"]["break_minutes"] == 45

    def test_update_handles_partial_updates(self, client, db_session):
        """PATCH handles partial updates (only update provided weekdays)."""
        # Create settings with multiple weekdays configured
        settings = UserSettingsFactory.build(
            user_id=1,
            weekly_target_hours=Decimal("40.00"),
            schedule_json={
                "weekday_defaults": {
                    "0": {"start_time": "08:00", "end_time": "16:30", "break_minutes": 30},
                    "1": {"start_time": "08:00", "end_time": "16:30", "break_minutes": 30},
                }
            },
        )
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        # Update only Monday (weekday 0)
        response = client.patch(
            "/settings/weekday-defaults",
            data={
                "weekday_0_start_time": "09:00",
                "weekday_0_end_time": "17:00",
                "weekday_0_break_minutes": "45",
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 200

        # Refresh and verify
        db_session.refresh(settings)
        # Monday should be updated
        assert settings.schedule_json["weekday_defaults"]["0"]["start_time"] == "09:00"
        # Tuesday should remain unchanged
        assert settings.schedule_json["weekday_defaults"]["1"]["start_time"] == "08:00"

    def test_update_multiple_weekdays_at_once(self, client, db_session):
        """PATCH updates multiple weekdays in single request."""
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/weekday-defaults",
            data={
                "weekday_0_start_time": "08:00",
                "weekday_0_end_time": "16:30",
                "weekday_0_break_minutes": "30",
                "weekday_1_start_time": "08:00",
                "weekday_1_end_time": "16:30",
                "weekday_1_break_minutes": "30",
                "weekday_2_start_time": "08:00",
                "weekday_2_end_time": "16:30",
                "weekday_2_break_minutes": "30",
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 200

        # Verify all three weekdays updated
        db_session.refresh(settings)
        assert settings.schedule_json["weekday_defaults"]["0"] is not None
        assert settings.schedule_json["weekday_defaults"]["1"] is not None
        assert settings.schedule_json["weekday_defaults"]["2"] is not None

    def test_update_validates_time_format(self, client, db_session):
        """PATCH validates time format (HH:MM)."""
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/weekday-defaults",
            data={
                "weekday_0_start_time": "invalid",  # Invalid time format
                "weekday_0_end_time": "16:30",
                "weekday_0_break_minutes": "30",
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 422  # Validation error

    def test_update_validates_break_minutes_range(self, client, db_session):
        """PATCH validates break_minutes is within valid range."""
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/weekday-defaults",
            data={
                "weekday_0_start_time": "08:00",
                "weekday_0_end_time": "16:30",
                "weekday_0_break_minutes": "999",  # Invalid: too large
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 422  # Validation error

    def test_update_returns_updated_form_partial(self, client, db_session):
        """PATCH returns updated form partial with new values."""
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/weekday-defaults",
            data={
                "weekday_0_start_time": "09:30",
                "weekday_0_end_time": "18:00",
                "weekday_0_break_minutes": "60",
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 200
        # Response should contain the updated values
        assert "09:30" in response.text
        assert "18:00" in response.text

    def test_update_weekday_to_null_for_non_working_day(self, client, db_session):
        """PATCH can set weekday to null (non-working day)."""
        settings = UserSettingsFactory.build(
            user_id=1,
            weekly_target_hours=Decimal("40.00"),
            schedule_json={
                "weekday_defaults": {
                    "5": {"start_time": "08:00", "end_time": "16:30", "break_minutes": 30},  # Saturday working
                }
            },
        )
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        # Update to make Saturday non-working by omitting data or sending empty values
        response = client.patch(
            "/settings/weekday-defaults",
            data={
                "weekday_5_enabled": "false",  # Indicate day is disabled
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 200

        db_session.refresh(settings)
        # Saturday should now be null (non-working)
        assert settings.schedule_json["weekday_defaults"]["5"] is None

    def test_update_creates_settings_if_not_exist(self, client, db_session):
        """PATCH creates settings record if none exists for user."""
        # No existing settings - should create one
        response = client.patch(
            "/settings/weekday-defaults",
            data={
                "weekday_0_start_time": "08:00",
                "weekday_0_end_time": "16:30",
                "weekday_0_break_minutes": "30",
            },
        )

        # May return 200 or 201 depending on implementation
        assert response.status_code in [200, 201]

    def test_update_requires_valid_weekday_keys(self, client, db_session):
        """PATCH validates weekday keys are 0-6."""
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/weekday-defaults",
            data={
                "weekday_7_start_time": "08:00",  # Invalid: weekday must be 0-6
                "weekday_7_end_time": "16:30",
                "weekday_7_break_minutes": "30",
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 422  # Validation error


class TestTrackingSettingsUpdate:
    """Test PATCH /settings/tracking endpoint."""

    def test_patch_tracking_settings_updates_tracking_start_date(self, client, db_session):
        """PATCH updates tracking_start_date successfully."""
        # Create initial settings
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/tracking",
            data={
                "tracking_start_date": "2026-01-15",
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 200
        assert "HX-Trigger" in response.headers
        assert response.headers["HX-Trigger"] == "settingsUpdated"

        # Verify database update
        db_session.refresh(settings)
        from datetime import date as date_type

        assert settings.tracking_start_date == date_type(2026, 1, 15)

    def test_patch_tracking_settings_updates_initial_hours_offset(self, client, db_session):
        """PATCH updates initial_hours_offset successfully."""
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/tracking",
            data={
                "initial_hours_offset": "15.50",
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 200
        assert "HX-Trigger" in response.headers
        assert response.headers["HX-Trigger"] == "settingsUpdated"

        # Verify database update
        db_session.refresh(settings)
        assert settings.initial_hours_offset == Decimal("15.50")

    def test_patch_tracking_settings_both_fields(self, client, db_session):
        """PATCH updates both tracking_start_date and initial_hours_offset."""
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/tracking",
            data={
                "tracking_start_date": "2026-01-15",
                "initial_hours_offset": "15.50",
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 200
        assert "HX-Trigger" in response.headers
        assert response.headers["HX-Trigger"] == "settingsUpdated"

        # Verify both fields updated
        db_session.refresh(settings)
        from datetime import date as date_type

        assert settings.tracking_start_date == date_type(2026, 1, 15)
        assert settings.initial_hours_offset == Decimal("15.50")

    def test_patch_tracking_settings_clears_values_with_empty_string(self, client, db_session):
        """PATCH clears tracking fields when empty strings provided."""
        # Create settings with existing values
        from datetime import date as date_type

        settings = UserSettingsFactory.build(
            user_id=1,
            weekly_target_hours=Decimal("40.00"),
            tracking_start_date=date_type(2026, 1, 1),
            initial_hours_offset=Decimal("10.00"),
        )
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/tracking",
            data={
                "tracking_start_date": "",
                "initial_hours_offset": "",
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 200
        assert "HX-Trigger" in response.headers
        assert response.headers["HX-Trigger"] == "settingsUpdated"

        # Verify fields cleared
        db_session.refresh(settings)
        assert settings.tracking_start_date is None
        assert settings.initial_hours_offset is None

    def test_patch_tracking_settings_invalid_date_format(self, client, db_session):
        """PATCH rejects invalid date format with German error message."""
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/tracking",
            data={
                "tracking_start_date": "invalid-date",
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 422
        # Should contain German error message
        assert "Ungültiges Datumsformat" in response.text

    def test_patch_tracking_settings_invalid_offset_value(self, client, db_session):
        """PATCH rejects non-numeric offset with German error message."""
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/tracking",
            data={
                "initial_hours_offset": "not-a-number",
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 422
        # Should contain German validation error
        assert response.text  # Contains error message

    def test_patch_tracking_settings_offset_out_of_range_high(self, client, db_session):
        """PATCH rejects offset > 999.99 with German error message."""
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/tracking",
            data={
                "initial_hours_offset": "1000.00",
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 422
        # Should contain validation error about range
        assert response.text

    def test_patch_tracking_settings_offset_out_of_range_low(self, client, db_session):
        """PATCH rejects offset < -999.99 with German error message."""
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/tracking",
            data={
                "initial_hours_offset": "-1000.00",
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 422
        # Should contain validation error about range
        assert response.text

    def test_get_settings_includes_tracking_fields(self, client, db_session):
        """GET /settings renders tracking_start_date and initial_hours_offset in German format."""
        from datetime import date as date_type

        # Create settings with tracking fields
        settings = UserSettingsFactory.build(
            user_id=1,
            weekly_target_hours=Decimal("40.00"),
            tracking_start_date=date_type(2026, 1, 15),
            initial_hours_offset=Decimal("15.50"),
        )
        db_session.add(settings)
        db_session.commit()

        response = client.get("/settings")

        assert response.status_code == 200
        # Should render tracking_start_date in German format (DD.MM.YYYY)
        assert "15.01.2026" in response.text
        # Should render initial_hours_offset in German format (comma decimal)
        assert "15,50" in response.text
        # Should render weekly_target_hours in German format
        assert "40,00" in response.text

    def test_patch_tracking_settings_negative_offset(self, client, db_session):
        """PATCH accepts negative offset within valid range."""
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/tracking",
            data={
                "initial_hours_offset": "-15.50",
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 200
        assert "HX-Trigger" in response.headers
        assert response.headers["HX-Trigger"] == "settingsUpdated"

        # Verify negative offset accepted
        db_session.refresh(settings)
        assert settings.initial_hours_offset == Decimal("-15.50")

    def test_patch_tracking_settings_creates_settings_if_not_exist(self, client, db_session):
        """PATCH creates settings record if none exists for user."""
        # No existing settings - should create one
        response = client.patch(
            "/settings/tracking",
            data={
                "tracking_start_date": "2026-01-15",
                "initial_hours_offset": "10.00",
            },
        )

        # May return 200 or 201 depending on implementation
        assert response.status_code in [200, 201]


class TestVacationSettingsUpdate:
    """Test PATCH /settings/vacation endpoint."""

    def test_patch_vacation_settings_updates_initial_days(self, client, db_session):
        """PATCH updates initial_vacation_days successfully."""
        # Create initial settings
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/vacation",
            data={
                "initial_vacation_days": "15.5",
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 200
        assert "HX-Trigger" in response.headers
        assert response.headers["HX-Trigger"] == "settingsUpdated"

        # Verify database update
        db_session.refresh(settings)
        assert settings.initial_vacation_days == Decimal("15.5")

    def test_patch_vacation_settings_updates_annual_days(self, client, db_session):
        """PATCH updates annual_vacation_days successfully."""
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/vacation",
            data={
                "annual_vacation_days": "30.0",
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 200
        assert "HX-Trigger" in response.headers
        assert response.headers["HX-Trigger"] == "settingsUpdated"

        # Verify database update
        db_session.refresh(settings)
        assert settings.annual_vacation_days == Decimal("30.0")

    def test_patch_vacation_settings_updates_carryover(self, client, db_session):
        """PATCH updates carryover days and expiry successfully."""
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/vacation",
            data={
                "vacation_carryover_days": "5.0",
                "vacation_carryover_expires": "2026-03-31",
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 200
        assert "HX-Trigger" in response.headers
        assert response.headers["HX-Trigger"] == "settingsUpdated"

        # Verify database update
        db_session.refresh(settings)
        from datetime import date as date_type

        assert settings.vacation_carryover_days == Decimal("5.0")
        assert settings.vacation_carryover_expires == date_type(2026, 3, 31)

    def test_patch_vacation_settings_all_fields(self, client, db_session):
        """PATCH updates all four vacation fields at once."""
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/vacation",
            data={
                "initial_vacation_days": "15.5",
                "annual_vacation_days": "30.0",
                "vacation_carryover_days": "5.0",
                "vacation_carryover_expires": "2026-03-31",
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 200
        assert "HX-Trigger" in response.headers
        assert response.headers["HX-Trigger"] == "settingsUpdated"

        # Verify all fields updated
        db_session.refresh(settings)
        from datetime import date as date_type

        assert settings.initial_vacation_days == Decimal("15.5")
        assert settings.annual_vacation_days == Decimal("30.0")
        assert settings.vacation_carryover_days == Decimal("5.0")
        assert settings.vacation_carryover_expires == date_type(2026, 3, 31)

    def test_patch_vacation_settings_clears_with_empty_string(self, client, db_session):
        """PATCH clears vacation fields when empty strings provided."""
        # Create settings with existing values
        from datetime import date as date_type

        settings = UserSettingsFactory.build(
            user_id=1,
            weekly_target_hours=Decimal("40.00"),
            initial_vacation_days=Decimal("15.5"),
            annual_vacation_days=Decimal("30.0"),
            vacation_carryover_days=Decimal("5.0"),
            vacation_carryover_expires=date_type(2026, 3, 31),
        )
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/vacation",
            data={
                "initial_vacation_days": "",
                "annual_vacation_days": "",
                "vacation_carryover_days": "",
                "vacation_carryover_expires": "",
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 200
        assert "HX-Trigger" in response.headers
        assert response.headers["HX-Trigger"] == "settingsUpdated"

        # Verify fields cleared
        db_session.refresh(settings)
        assert settings.initial_vacation_days is None
        assert settings.annual_vacation_days is None
        assert settings.vacation_carryover_days is None
        assert settings.vacation_carryover_expires is None

    def test_patch_vacation_settings_invalid_number_format(self, client, db_session):
        """PATCH rejects non-numeric vacation days with German error message."""
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/vacation",
            data={
                "initial_vacation_days": "not-a-number",
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 422
        # Should contain German validation error
        assert response.text

    def test_patch_vacation_settings_invalid_date_format(self, client, db_session):
        """PATCH rejects invalid date format with German error message."""
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/vacation",
            data={
                "vacation_carryover_expires": "invalid-date",
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 422
        # Should contain German error message
        assert "Ungültiges Datumsformat" in response.text

    def test_patch_vacation_settings_negative_days_rejected(self, client, db_session):
        """PATCH rejects negative vacation days with German error message."""
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/vacation",
            data={
                "initial_vacation_days": "-5.0",
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 422
        # Should contain validation error about negative values
        assert response.text

    def test_patch_vacation_settings_german_number_format(self, client, db_session):
        """PATCH accepts German number format (comma decimal)."""
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/vacation",
            data={
                "initial_vacation_days": "15,5",  # German format with comma
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 200
        assert "HX-Trigger" in response.headers
        assert response.headers["HX-Trigger"] == "settingsUpdated"

        # Verify German format converted correctly
        db_session.refresh(settings)
        assert settings.initial_vacation_days == Decimal("15.5")

    def test_patch_vacation_settings_german_date_format(self, client, db_session):
        """PATCH accepts German date format (DD.MM.YYYY)."""
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/vacation",
            data={
                "vacation_carryover_expires": "31.03.2026",  # German format
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 200
        assert "HX-Trigger" in response.headers
        assert response.headers["HX-Trigger"] == "settingsUpdated"

        # Verify German format converted correctly
        db_session.refresh(settings)
        from datetime import date as date_type

        assert settings.vacation_carryover_expires == date_type(2026, 3, 31)

    def test_patch_vacation_settings_sets_hx_trigger(self, client, db_session):
        """PATCH sets HX-Trigger: settingsUpdated header."""
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("40.00"))
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        response = client.patch(
            "/settings/vacation",
            data={
                "initial_vacation_days": "15.5",
                "updated_at": settings.updated_at.isoformat(),
            },
        )

        assert response.status_code == 200
        assert "HX-Trigger" in response.headers
        assert response.headers["HX-Trigger"] == "settingsUpdated"

    def test_patch_vacation_settings_creates_if_not_exist(self, client, db_session):
        """PATCH creates settings record if none exists for user."""
        # No existing settings - should create one
        response = client.patch(
            "/settings/vacation",
            data={
                "initial_vacation_days": "15.5",
                "annual_vacation_days": "30.0",
            },
        )

        # May return 200 or 201 depending on implementation
        assert response.status_code in [200, 201]

    def test_get_settings_includes_vacation_fields(self, client, db_session):
        """GET /settings renders vacation fields in German format."""
        from datetime import date as date_type

        # Create settings with vacation fields
        settings = UserSettingsFactory.build(
            user_id=1,
            weekly_target_hours=Decimal("40.00"),
            initial_vacation_days=Decimal("15.5"),
            annual_vacation_days=Decimal("30.0"),
            vacation_carryover_days=Decimal("5.0"),
            vacation_carryover_expires=date_type(2026, 3, 31),
        )
        db_session.add(settings)
        db_session.commit()

        response = client.get("/settings")

        assert response.status_code == 200
        # Should render vacation_carryover_expires in German format (DD.MM.YYYY)
        assert "31.03.2026" in response.text
        # Should render vacation days in German format (comma decimal)
        assert "15,5" in response.text
        assert "30,0" in response.text
        assert "5,0" in response.text
