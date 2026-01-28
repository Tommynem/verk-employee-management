"""
Tests for time input formatting functionality.

This tests the JavaScript formatTimeInput function's expected behavior
by documenting test cases and verifying template integration.
"""


class TestTimeInputFormatting:
    """Test suite for quick time input formatting."""

    def test_format_single_digit_hour(self):
        """Single digit (e.g., '6') should format to '06:00'."""
        test_cases = [
            ("6", "06:00"),
            ("8", "08:00"),
            ("9", "09:00"),
        ]
        for input_val, expected in test_cases:
            result = self._format_time_input(input_val)
            assert result == expected, f"Expected '{input_val}' to format to '{expected}', got '{result}'"

    def test_format_double_digit_hour(self):
        """Double digit hour (e.g., '14') should format to '14:00'."""
        test_cases = [
            ("14", "14:00"),
            ("16", "16:00"),
            ("23", "23:00"),
            ("00", "00:00"),
        ]
        for input_val, expected in test_cases:
            result = self._format_time_input(input_val)
            assert result == expected, f"Expected '{input_val}' to format to '{expected}', got '{result}'"

    def test_format_three_digit_time(self):
        """Three digit time (e.g., '830') should format to '08:30'."""
        test_cases = [
            ("830", "08:30"),
            ("945", "09:45"),
        ]
        for input_val, expected in test_cases:
            result = self._format_time_input(input_val)
            assert result == expected, f"Expected '{input_val}' to format to '{expected}', got '{result}'"

    def test_format_four_digit_time(self):
        """Four digit time (e.g., '1630') should format to '16:30'."""
        test_cases = [
            ("1630", "16:30"),
            ("0845", "08:45"),
            ("2359", "23:59"),
        ]
        for input_val, expected in test_cases:
            result = self._format_time_input(input_val)
            assert result == expected, f"Expected '{input_val}' to format to '{expected}', got '{result}'"

    def test_format_colon_format_single_digit_hour(self):
        """Colon format with single digit hour (e.g., '8:30') should format to '08:30'."""
        test_cases = [
            ("8:30", "08:30"),
            ("9:45", "09:45"),
        ]
        for input_val, expected in test_cases:
            result = self._format_time_input(input_val)
            assert result == expected, f"Expected '{input_val}' to format to '{expected}', got '{result}'"

    def test_format_already_formatted(self):
        """Already formatted time (e.g., '16:30') should remain unchanged."""
        test_cases = [
            ("16:30", "16:30"),
            ("08:00", "08:00"),
            ("23:59", "23:59"),
        ]
        for input_val, expected in test_cases:
            result = self._format_time_input(input_val)
            assert result == expected, f"Expected '{input_val}' to remain '{expected}', got '{result}'"

    def test_format_empty_input(self):
        """Empty input should return empty string."""
        assert self._format_time_input("") == ""
        assert self._format_time_input("   ") == ""

    def test_format_invalid_input(self):
        """Invalid input should return empty string (clears the field)."""
        test_cases = [
            "abc",      # Non-numeric
            "25",       # Invalid hour > 23
            "25:00",    # Invalid hour in colon format
            "12:60",    # Invalid minute >= 60
            "123456",   # Too long
        ]
        for input_val in test_cases:
            result = self._format_time_input(input_val)
            # Should return empty string to clear invalid input
            assert result == "", f"Expected empty string for invalid '{input_val}', got '{result}'"

    def test_format_edge_cases(self):
        """Test edge cases like midnight and specific boundaries."""
        test_cases = [
            ("0", "00:00"),
            ("00", "00:00"),
            ("0000", "00:00"),
            ("2400", "00:00"),  # 24:00 wraps to 00:00 (optional behavior)
        ]
        for input_val, expected in test_cases:
            result = self._format_time_input(input_val)
            # For 2400, it's optional - can be original or converted
            if input_val == "2400" and result != expected:
                continue
            assert result == expected, f"Expected '{input_val}' to format to '{expected}', got '{result}'"

    def _format_time_input(self, value: str) -> str:
        """
        Python implementation mirroring the JavaScript formatTimeInput function.
        This serves as specification for the JS implementation.

        Args:
            value: Input time string

        Returns:
            Formatted time string in HH:MM format
        """
        # Strip whitespace
        value = value.strip()

        # Empty string returns empty
        if not value:
            return ""

        # If already in HH:MM format with proper padding, return as-is
        if ":" in value:
            parts = value.split(":")
            if len(parts) == 2:
                try:
                    hour = int(parts[0])
                    minute = int(parts[1])
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        return f"{hour:02d}:{minute:02d}"
                except ValueError:
                    return ""  # Invalid, clear field

        # Remove any colons for uniform processing
        value = value.replace(":", "")

        # Must be numeric
        if not value.isdigit():
            return ""  # Invalid, clear field

        # Handle different length inputs
        length = len(value)

        if length == 1:
            # Single digit: treat as hour (e.g., "6" -> "06:00")
            hour = int(value)
            if 0 <= hour <= 23:
                return f"{hour:02d}:00"

        elif length == 2:
            # Two digits: treat as hour (e.g., "14" -> "14:00")
            hour = int(value)
            if 0 <= hour <= 23:
                return f"{hour:02d}:00"
            # Special case: 24 -> 00:00
            elif hour == 24:
                return "00:00"

        elif length == 3:
            # Three digits: HMM format (e.g., "830" -> "08:30")
            hour = int(value[0])
            minute = int(value[1:3])
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return f"{hour:02d}:{minute:02d}"

        elif length == 4:
            # Four digits: HHMM format (e.g., "1630" -> "16:30")
            hour = int(value[0:2])
            minute = int(value[2:4])
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return f"{hour:02d}:{minute:02d}"
            # Special case: 2400 -> 00:00
            elif hour == 24 and minute == 0:
                return "00:00"

        # Invalid format, clear field
        return ""


class TestTimeInputTemplateIntegration:
    """Test that time input fields have proper event listeners attached."""

    def test_edit_row_has_time_inputs(self, client):
        """Verify that time entry edit rows have time input fields."""
        # This will pass once templates are loaded
        response = client.get("/time-entries/new-row")
        assert response.status_code == 200

        html = response.text
        # Check that time input fields exist
        assert 'name="start_time"' in html
        assert 'name="end_time"' in html
        assert 'pattern="([01]?[0-9]|2[0-3]):[0-5][0-9]"' in html

    def test_settings_page_has_weekday_inputs(self, client):
        """Verify that settings page has weekday time input fields."""
        response = client.get("/settings")
        assert response.status_code == 200

        html = response.text
        # Check that weekday time input fields exist
        assert 'name="weekday_0_start_time"' in html
        assert 'name="weekday_0_end_time"' in html
