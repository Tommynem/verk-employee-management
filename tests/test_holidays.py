"""Tests for German public holiday detection.

Tests the holiday service that calculates German public holidays including
movable holidays based on Easter date calculation.
"""

from datetime import date
from types import SimpleNamespace

import pytest

from source.core.holidays import (
    calculate_easter,
    get_german_holidays,
    get_german_holidays_for_settings,
    get_holiday_state_code,
    is_holiday,
    is_holiday_for_settings,
    is_non_vacation_consuming_closure_for_settings,
)


class TestEasterCalculation:
    """Test Easter date calculation using Meeus/Jones/Butcher algorithm."""

    @pytest.mark.unit
    def test_easter_2024(self):
        """Easter 2024 is March 31."""
        assert calculate_easter(2024) == date(2024, 3, 31)

    @pytest.mark.unit
    def test_easter_2025(self):
        """Easter 2025 is April 20."""
        assert calculate_easter(2025) == date(2025, 4, 20)

    @pytest.mark.unit
    def test_easter_2026(self):
        """Easter 2026 is April 5."""
        assert calculate_easter(2026) == date(2026, 4, 5)

    @pytest.mark.unit
    def test_easter_2027(self):
        """Easter 2027 is March 28."""
        assert calculate_easter(2027) == date(2027, 3, 28)

    @pytest.mark.unit
    def test_easter_2030(self):
        """Easter 2030 is April 21."""
        assert calculate_easter(2030) == date(2030, 4, 21)

    @pytest.mark.unit
    def test_easter_2035(self):
        """Easter 2035 is March 25."""
        assert calculate_easter(2035) == date(2035, 3, 25)


class TestGermanHolidays:
    """Test German nationwide public holiday detection."""

    @pytest.mark.unit
    def test_neujahr_2026(self):
        """New Year's Day 2026 is January 1."""
        holidays = get_german_holidays(2026)
        assert date(2026, 1, 1) in holidays
        assert holidays[date(2026, 1, 1)] == "Neujahr"

    @pytest.mark.unit
    def test_karfreitag_2026(self):
        """Good Friday 2026 is April 3 (Easter is April 5)."""
        holidays = get_german_holidays(2026)
        assert date(2026, 4, 3) in holidays
        assert holidays[date(2026, 4, 3)] == "Karfreitag"

    @pytest.mark.unit
    def test_ostermontag_2026(self):
        """Easter Monday 2026 is April 6 (Easter is April 5)."""
        holidays = get_german_holidays(2026)
        assert date(2026, 4, 6) in holidays
        assert holidays[date(2026, 4, 6)] == "Ostermontag"

    @pytest.mark.unit
    def test_tag_der_arbeit_2026(self):
        """Labour Day 2026 is May 1."""
        holidays = get_german_holidays(2026)
        assert date(2026, 5, 1) in holidays
        assert holidays[date(2026, 5, 1)] == "Tag der Arbeit"

    @pytest.mark.unit
    def test_christi_himmelfahrt_2026(self):
        """Ascension Day 2026 is May 14 (39 days after Easter April 5)."""
        holidays = get_german_holidays(2026)
        assert date(2026, 5, 14) in holidays
        assert holidays[date(2026, 5, 14)] == "Christi Himmelfahrt"

    @pytest.mark.unit
    def test_pfingstmontag_2026(self):
        """Whit Monday 2026 is May 25 (50 days after Easter April 5)."""
        holidays = get_german_holidays(2026)
        assert date(2026, 5, 25) in holidays
        assert holidays[date(2026, 5, 25)] == "Pfingstmontag"

    @pytest.mark.unit
    def test_tag_der_deutschen_einheit_2026(self):
        """German Unity Day 2026 is October 3."""
        holidays = get_german_holidays(2026)
        assert date(2026, 10, 3) in holidays
        assert holidays[date(2026, 10, 3)] == "Tag der Deutschen Einheit"

    @pytest.mark.unit
    def test_erster_weihnachtstag_2026(self):
        """Christmas Day 2026 is December 25."""
        holidays = get_german_holidays(2026)
        assert date(2026, 12, 25) in holidays
        assert holidays[date(2026, 12, 25)] == "1. Weihnachtstag"

    @pytest.mark.unit
    def test_zweiter_weihnachtstag_2026(self):
        """Boxing Day 2026 is December 26."""
        holidays = get_german_holidays(2026)
        assert date(2026, 12, 26) in holidays
        assert holidays[date(2026, 12, 26)] == "2. Weihnachtstag"

    @pytest.mark.unit
    def test_all_nine_holidays_present_2026(self):
        """Verify all 9 nationwide holidays are present for 2026."""
        holidays = get_german_holidays(2026)
        assert len(holidays) == 9

    @pytest.mark.unit
    def test_movable_holidays_2025(self):
        """Verify movable holidays for 2025 (Easter is April 20)."""
        holidays = get_german_holidays(2025)
        # Good Friday: 2 days before Easter
        assert date(2025, 4, 18) in holidays
        assert holidays[date(2025, 4, 18)] == "Karfreitag"
        # Easter Monday: 1 day after Easter
        assert date(2025, 4, 21) in holidays
        assert holidays[date(2025, 4, 21)] == "Ostermontag"
        # Ascension: 39 days after Easter
        assert date(2025, 5, 29) in holidays
        assert holidays[date(2025, 5, 29)] == "Christi Himmelfahrt"
        # Whit Monday: 50 days after Easter
        assert date(2025, 6, 9) in holidays
        assert holidays[date(2025, 6, 9)] == "Pfingstmontag"


class TestStateAwareGermanHolidays:
    """Test Bundesland-aware German public holiday detection."""

    @pytest.mark.unit
    def test_default_none_excludes_nrw_specific_fronleichnam(self):
        """Nationwide-only defaults do not include NRW-specific Fronleichnam."""
        holidays = get_german_holidays(2026)

        assert date(2026, 6, 4) not in holidays
        assert is_holiday(date(2026, 6, 4), state_code=None) is False

    @pytest.mark.unit
    def test_nw_includes_fronleichnam_2026(self):
        """NRW has Fronleichnam on June 4, 2026."""
        holidays = get_german_holidays(2026, state_code="NW")

        assert holidays[date(2026, 6, 4)] == "Fronleichnam"

    @pytest.mark.unit
    def test_nw_includes_allerheiligen_2026(self):
        """NRW has Allerheiligen on November 1."""
        holidays = get_german_holidays(2026, state_code="NW")

        assert holidays[date(2026, 11, 1)] == "Allerheiligen"

    @pytest.mark.unit
    def test_nw_keeps_nationwide_holidays(self):
        """State-specific holiday sets still include nationwide holidays."""
        holidays = get_german_holidays(2026, state_code="NW")

        assert holidays[date(2026, 10, 3)] == "Tag der Deutschen Einheit"
        assert holidays[date(2026, 12, 25)] == "1. Weihnachtstag"

    @pytest.mark.unit
    def test_is_holiday_with_nw_state_code(self):
        """is_holiday can include NRW-specific holidays."""
        assert is_holiday(date(2026, 6, 4), state_code="NW") is True
        assert is_holiday(date(2026, 6, 4), return_name=True, state_code="NW") == (True, "Fronleichnam")

    @pytest.mark.unit
    def test_get_holiday_state_code_from_settings_object(self):
        """Settings-like objects can provide the state code."""
        settings = SimpleNamespace(holiday_state_code="NW")

        assert get_holiday_state_code(settings) == "NW"

    @pytest.mark.unit
    def test_get_holiday_state_code_from_schedule_json(self):
        """Settings schedule_json can provide the state code."""
        settings = SimpleNamespace(schedule_json={"holidays": {"bundesland": "DE-NW"}})

        assert get_holiday_state_code(settings) == "NW"

    @pytest.mark.unit
    def test_settings_helpers_use_state_code(self):
        """Settings-aware helpers include NRW-specific holidays."""
        settings = SimpleNamespace(schedule_json={"holiday_state_code": "NW"})

        holidays = get_german_holidays_for_settings(2026, settings)

        assert holidays[date(2026, 6, 4)] == "Fronleichnam"
        assert is_holiday_for_settings(date(2026, 6, 4), settings, return_name=True) == (True, "Fronleichnam")

    @pytest.mark.unit
    def test_settings_helpers_default_to_nationwide_only(self):
        """Missing settings state keeps nationwide-only behavior."""
        settings = SimpleNamespace(schedule_json={})

        holidays = get_german_holidays_for_settings(2026, settings)

        assert date(2026, 6, 4) not in holidays
        assert is_holiday_for_settings(date(2026, 6, 4), settings) is False


class TestCompanyClosures:
    """Test settings-backed company closure detection."""

    @pytest.mark.unit
    def test_default_closures_apply_when_settings_exist(self):
        """Settings without explicit closure config use the default 24.12 closure."""
        settings = SimpleNamespace(schedule_json={})

        assert is_non_vacation_consuming_closure_for_settings(date(2025, 12, 24), settings, True) == (
            True,
            "Heiligabend",
        )

    @pytest.mark.unit
    def test_none_settings_preserves_legacy_no_closure_behavior(self):
        """Callers without settings do not get company closures implicitly."""
        assert is_non_vacation_consuming_closure_for_settings(date(2025, 12, 24), None) is False

    @pytest.mark.unit
    def test_disabled_default_closure_does_not_match(self):
        """Configured disabled closures override enabled defaults."""
        settings = SimpleNamespace(schedule_json={"company_closures": {"12-24": {"enabled": False}}})

        assert is_non_vacation_consuming_closure_for_settings(date(2025, 12, 24), settings) is False

    @pytest.mark.unit
    def test_list_style_closure_shape_is_supported(self):
        """Imported list-style closures can use the original consumes_vacation flag."""
        settings = SimpleNamespace(
            schedule_json={
                "company_closures": [
                    {
                        "month": 2,
                        "day": 3,
                        "name": "Betriebsschliessung",
                        "recurring": True,
                        "consumes_vacation": False,
                    }
                ]
            }
        )

        assert is_non_vacation_consuming_closure_for_settings(date(2026, 2, 3), settings, True) == (
            True,
            "Betriebsschliessung",
        )


class TestIsHoliday:
    """Test is_holiday convenience function."""

    @pytest.mark.unit
    def test_is_holiday_true_neujahr(self):
        """New Year's Day is a holiday."""
        assert is_holiday(date(2026, 1, 1)) is True

    @pytest.mark.unit
    def test_is_holiday_true_with_name(self):
        """is_holiday returns tuple with name when return_name=True."""
        result = is_holiday(date(2026, 1, 1), return_name=True)
        assert result == (True, "Neujahr")

    @pytest.mark.unit
    def test_is_holiday_false(self):
        """Regular work day is not a holiday."""
        assert is_holiday(date(2026, 1, 15)) is False

    @pytest.mark.unit
    def test_is_holiday_false_with_name(self):
        """is_holiday returns tuple with None when not a holiday."""
        result = is_holiday(date(2026, 1, 15), return_name=True)
        assert result == (False, None)

    @pytest.mark.unit
    def test_is_holiday_easter_monday(self):
        """Easter Monday 2026 is detected as holiday."""
        assert is_holiday(date(2026, 4, 6)) is True

    @pytest.mark.unit
    def test_is_holiday_weekend_not_holiday(self):
        """Weekend days are not automatically holidays (only explicit holidays count)."""
        # Saturday January 3, 2026
        assert is_holiday(date(2026, 1, 3)) is False
        # Sunday January 4, 2026
        assert is_holiday(date(2026, 1, 4)) is False
