"""Tests for Jinja2 template filters."""

from decimal import Decimal

from source.api.context import format_balance, format_duration, format_hours


class TestFormatHoursFilter:
    """Tests for format_hours filter.

    Converts Decimal hours to "HHH:MMh" format.
    Input is Decimal representing hours, output shows hours:minutes with 'h' suffix.
    """

    def test_format_hours_large_value(self):
        """Large hour values format correctly."""
        # 149 hours and 38 minutes = 149 + 38/60 = 149.6333...
        assert format_hours(Decimal("149.6333")) == "149:38h"

    def test_format_hours_small_value(self):
        """Small hour values format correctly."""
        # 6 hours and 24 minutes = 6.4
        assert format_hours(Decimal("6.4")) == "6:24h"

    def test_format_hours_zero(self):
        """Zero hours formats correctly."""
        assert format_hours(Decimal("0")) == "0:00h"

    def test_format_hours_half_hour(self):
        """Half hour formats correctly."""
        assert format_hours(Decimal("8.5")) == "8:30h"

    def test_format_hours_quarter_hour(self):
        """Quarter hour formats correctly."""
        assert format_hours(Decimal("0.25")) == "0:15h"

    def test_format_hours_three_quarter_hour(self):
        """Three quarter hour formats correctly."""
        assert format_hours(Decimal("0.75")) == "0:45h"

    def test_format_hours_none(self):
        """None returns dash placeholder."""
        assert format_hours(None) == "-"

    def test_format_hours_negative_value(self):
        """Negative hours format correctly (edge case)."""
        # Should handle negative values without sign in display
        assert format_hours(Decimal("-1.5")) == "-1:30h"


class TestFormatDurationFilter:
    """Tests for format_duration filter.

    Converts integer minutes to "H:MMh" format.
    Input is integer minutes, output shows hours:minutes with 'h' suffix.
    """

    def test_format_duration_thirty_minutes(self):
        """Thirty minutes formats correctly."""
        assert format_duration(30) == "0:30h"

    def test_format_duration_ninety_minutes(self):
        """Ninety minutes formats correctly."""
        assert format_duration(90) == "1:30h"

    def test_format_duration_zero(self):
        """Zero minutes formats correctly."""
        assert format_duration(0) == "0:00h"

    def test_format_duration_forty_five_minutes(self):
        """Forty-five minutes formats correctly."""
        assert format_duration(45) == "0:45h"

    def test_format_duration_exact_hours(self):
        """Exact hours format correctly."""
        assert format_duration(120) == "2:00h"

    def test_format_duration_large_value(self):
        """Large minute values format correctly."""
        assert format_duration(500) == "8:20h"

    def test_format_duration_one_minute(self):
        """Single minute formats correctly."""
        assert format_duration(1) == "0:01h"

    def test_format_duration_none(self):
        """None returns dash placeholder."""
        assert format_duration(None) == "-"

    def test_format_duration_negative_value(self):
        """Negative minutes format correctly (edge case)."""
        assert format_duration(-30) == "-0:30h"


class TestFormatBalanceFilter:
    """Tests for format_balance filter.

    Converts Decimal hours to signed "+H:MM" or "-H:MM" format.
    Input is Decimal representing hours, output shows hours:minutes with +/- sign, no 'h' suffix.
    """

    def test_format_balance_positive_small(self):
        """Small positive balance formats correctly."""
        assert format_balance(Decimal("1.5")) == "+1:30"

    def test_format_balance_negative_small(self):
        """Small negative balance formats correctly."""
        assert format_balance(Decimal("-0.75")) == "-0:45"

    def test_format_balance_zero(self):
        """Zero balance formats with positive sign."""
        assert format_balance(Decimal("0")) == "+0:00"

    def test_format_balance_positive_large(self):
        """Large positive balance formats correctly."""
        assert format_balance(Decimal("19.5")) == "+19:30"

    def test_format_balance_negative_large(self):
        """Large negative balance formats correctly."""
        assert format_balance(Decimal("-2.25")) == "-2:15"

    def test_format_balance_positive_quarter_hour(self):
        """Positive quarter hour balance formats correctly."""
        assert format_balance(Decimal("0.25")) == "+0:15"

    def test_format_balance_negative_quarter_hour(self):
        """Negative quarter hour balance formats correctly."""
        assert format_balance(Decimal("-0.25")) == "-0:15"

    def test_format_balance_positive_three_quarter_hour(self):
        """Positive three quarter hour balance formats correctly."""
        assert format_balance(Decimal("0.75")) == "+0:45"

    def test_format_balance_none(self):
        """None returns dash placeholder."""
        assert format_balance(None) == "-"

    def test_format_balance_very_large_positive(self):
        """Very large positive balance formats correctly."""
        assert format_balance(Decimal("100.5")) == "+100:30"

    def test_format_balance_very_large_negative(self):
        """Very large negative balance formats correctly."""
        assert format_balance(Decimal("-100.5")) == "-100:30"
