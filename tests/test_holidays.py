"""Tests for German public holiday detection.

Tests the holiday service that calculates German public holidays including
movable holidays based on Easter date calculation.
"""

from datetime import date

import pytest

from source.core.holidays import calculate_easter, get_german_holidays, is_holiday


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
