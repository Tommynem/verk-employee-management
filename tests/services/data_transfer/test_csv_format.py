"""Tests for CSV format handler.

This module tests the CSVFormatHandler implementation for German Excel-compatible
CSV files (semicolon delimiter, UTF-8 with BOM).
"""

from datetime import date, time

from source.services.data_transfer.csv_format import CSVFormatHandler
from source.services.data_transfer.dataclasses import TimeEntryRow


class TestCSVFormatHandlerProperties:
    """Tests for CSVFormatHandler properties."""

    def test_content_type_returns_csv_with_charset(self):
        """Test that content_type returns correct MIME type with charset."""
        handler = CSVFormatHandler()

        assert handler.content_type == "text/csv; charset=utf-8"

    def test_file_extension_returns_csv(self):
        """Test that file_extension returns csv without dot."""
        handler = CSVFormatHandler()

        assert handler.file_extension == "csv"


class TestCSVFormatHandlerSerialize:
    """Tests for CSVFormatHandler.serialize() method."""

    def test_serialize_empty_list_returns_headers_only(self):
        """Test serializing empty list returns only CSV headers with BOM."""
        handler = CSVFormatHandler()
        rows = []

        result = handler.serialize(rows)

        # Should contain UTF-8 BOM
        assert result.startswith(b"\xef\xbb\xbf")

        # Decode and check headers
        csv_text = result.decode("utf-8-sig")
        lines = csv_text.strip().split("\n")

        assert len(lines) == 1
        assert lines[0] == "Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen"

    def test_serialize_single_regular_work_entry(self):
        """Test serializing single work entry with times."""
        handler = CSVFormatHandler()
        rows = [
            TimeEntryRow(
                work_date=date(2026, 1, 15),
                start_time=time(7, 0),
                end_time=time(15, 30),
                break_minutes=30,
                absence_type="none",
                notes="Productive day",
            )
        ]

        result = handler.serialize(rows)

        # Decode and parse
        csv_text = result.decode("utf-8-sig")
        lines = csv_text.strip().split("\n")

        assert len(lines) == 2
        assert lines[0] == "Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen"
        assert lines[1] == "2026-01-15;07:00;15:30;30;Keine;Productive day"

    def test_serialize_absence_entry_with_empty_times(self):
        """Test serializing absence entry has empty time fields."""
        handler = CSVFormatHandler()
        rows = [
            TimeEntryRow(
                work_date=date(2026, 1, 16),
                start_time=None,
                end_time=None,
                break_minutes=0,
                absence_type="vacation",
                notes="",
            )
        ]

        result = handler.serialize(rows)

        csv_text = result.decode("utf-8-sig")
        lines = csv_text.strip().split("\n")

        assert len(lines) == 2
        assert lines[1] == "2026-01-16;;;0;Urlaub;"

    def test_serialize_multiple_entries(self):
        """Test serializing multiple time entries."""
        handler = CSVFormatHandler()
        rows = [
            TimeEntryRow(
                work_date=date(2026, 1, 15),
                start_time=time(7, 0),
                end_time=time(15, 0),
                break_minutes=30,
                absence_type="none",
                notes="Day 1",
            ),
            TimeEntryRow(
                work_date=date(2026, 1, 16),
                start_time=time(8, 0),
                end_time=time(16, 0),
                break_minutes=45,
                absence_type="none",
                notes="Day 2",
            ),
        ]

        result = handler.serialize(rows)

        csv_text = result.decode("utf-8-sig")
        lines = csv_text.strip().split("\n")

        assert len(lines) == 3
        assert lines[1] == "2026-01-15;07:00;15:00;30;Keine;Day 1"
        assert lines[2] == "2026-01-16;08:00;16:00;45;Keine;Day 2"

    def test_serialize_time_formatting_with_leading_zeros(self):
        """Test that times are formatted with leading zeros (HH:MM)."""
        handler = CSVFormatHandler()
        rows = [
            TimeEntryRow(
                work_date=date(2026, 1, 15),
                start_time=time(7, 0),
                end_time=time(15, 30),
                break_minutes=30,
                absence_type="none",
                notes="",
            )
        ]

        result = handler.serialize(rows)

        csv_text = result.decode("utf-8-sig")
        lines = csv_text.strip().split("\n")

        # Should have leading zeros: 07:00, not 7:00
        assert "07:00" in lines[1]
        assert "15:30" in lines[1]

    def test_serialize_notes_with_special_characters(self):
        """Test serializing notes containing commas, semicolons, and quotes."""
        handler = CSVFormatHandler()
        rows = [
            TimeEntryRow(
                work_date=date(2026, 1, 15),
                start_time=time(7, 0),
                end_time=time(15, 0),
                break_minutes=30,
                absence_type="none",
                notes='Meeting with "CEO"; discussed project, very productive',
            )
        ]

        result = handler.serialize(rows)

        csv_text = result.decode("utf-8-sig")

        # Notes with special chars should be quoted
        assert 'Meeting with "CEO"' in csv_text or 'Meeting with ""CEO""' in csv_text

    def test_serialize_all_absence_types(self):
        """Test serializing all supported absence types with German translations."""
        handler = CSVFormatHandler()
        rows = [
            TimeEntryRow(work_date=date(2026, 1, 15), absence_type="none"),
            TimeEntryRow(work_date=date(2026, 1, 16), absence_type="vacation"),
            TimeEntryRow(work_date=date(2026, 1, 17), absence_type="sick"),
            TimeEntryRow(work_date=date(2026, 1, 18), absence_type="holiday"),
            TimeEntryRow(work_date=date(2026, 1, 19), absence_type="flex_time"),
        ]

        result = handler.serialize(rows)

        csv_text = result.decode("utf-8-sig")
        lines = csv_text.strip().split("\n")

        assert "Keine" in lines[1]
        assert "Urlaub" in lines[2]
        assert "Krank" in lines[3]
        assert "Feiertag" in lines[4]
        assert "Gleitzeit" in lines[5]

    def test_serialize_utf8_with_bom_encoding(self):
        """Test that serialized CSV uses UTF-8 with BOM encoding."""
        handler = CSVFormatHandler()
        rows = [
            TimeEntryRow(
                work_date=date(2026, 1, 15),
                start_time=time(7, 0),
                end_time=time(15, 0),
                break_minutes=30,
                absence_type="none",
                notes="Ümlauts: äöü ÄÖÜ ß",
            )
        ]

        result = handler.serialize(rows)

        # Check BOM
        assert result.startswith(b"\xef\xbb\xbf")

        # Should decode correctly with utf-8-sig
        csv_text = result.decode("utf-8-sig")
        assert "Ümlauts: äöü ÄÖÜ ß" in csv_text


class TestCSVFormatHandlerDeserialize:
    """Tests for CSVFormatHandler.deserialize() method."""

    def test_deserialize_valid_csv_with_headers(self):
        """Test deserializing valid CSV returns correct field dicts."""
        handler = CSVFormatHandler()
        csv_content = (
            b"\xef\xbb\xbf"
            b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n"
            b"2026-01-15;07:00;15:30;30;Keine;Productive day\n"
        )

        results = list(handler.deserialize(csv_content))

        assert len(results) == 1
        row_num, fields = results[0]

        assert row_num == 2  # Header is row 1, data starts at row 2
        assert fields["work_date"] == "2026-01-15"
        assert fields["start_time"] == "07:00"
        assert fields["end_time"] == "15:30"
        assert fields["break_minutes"] == "30"
        assert fields["absence_type"] == "Keine"
        assert fields["notes"] == "Productive day"

    def test_deserialize_returns_row_number_and_dict_tuples(self):
        """Test deserialize yields (row_number, dict) tuples."""
        handler = CSVFormatHandler()
        csv_content = (
            b"\xef\xbb\xbf"
            b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n"
            b"2026-01-15;07:00;15:00;30;Keine;Day 1\n"
            b"2026-01-16;08:00;16:00;45;Keine;Day 2\n"
        )

        results = list(handler.deserialize(csv_content))

        assert len(results) == 2

        row_num_1, fields_1 = results[0]
        assert row_num_1 == 2
        assert isinstance(fields_1, dict)

        row_num_2, fields_2 = results[1]
        assert row_num_2 == 3
        assert isinstance(fields_2, dict)

    def test_deserialize_empty_time_fields_as_empty_strings(self):
        """Test that empty time fields are returned as empty strings."""
        handler = CSVFormatHandler()
        csv_content = (
            b"\xef\xbb\xbf" b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n" b"2026-01-16;;;0;Urlaub;\n"
        )

        results = list(handler.deserialize(csv_content))

        assert len(results) == 1
        row_num, fields = results[0]

        assert fields["start_time"] == ""
        assert fields["end_time"] == ""

    def test_deserialize_break_minutes_as_string(self):
        """Test that break_minutes is returned as string (not parsed)."""
        handler = CSVFormatHandler()
        csv_content = (
            b"\xef\xbb\xbf"
            b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n"
            b"2026-01-15;07:00;15:00;30;Keine;Test\n"
        )

        results = list(handler.deserialize(csv_content))

        assert len(results) == 1
        row_num, fields = results[0]

        # Should be string, not int (parsing happens in mapper layer)
        assert fields["break_minutes"] == "30"
        assert isinstance(fields["break_minutes"], str)

    def test_deserialize_absence_types_as_german_strings(self):
        """Test that absence types are returned as German strings."""
        handler = CSVFormatHandler()
        csv_content = (
            b"\xef\xbb\xbf"
            b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n"
            b"2026-01-15;;;0;Urlaub;\n"
            b"2026-01-16;;;0;Krank;\n"
        )

        results = list(handler.deserialize(csv_content))

        assert len(results) == 2
        assert results[0][1]["absence_type"] == "Urlaub"
        assert results[1][1]["absence_type"] == "Krank"

    def test_deserialize_multiple_rows_with_correct_row_numbers(self):
        """Test that row numbers start at 2 and increment correctly."""
        handler = CSVFormatHandler()
        csv_content = (
            b"\xef\xbb\xbf"
            b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n"
            b"2026-01-15;07:00;15:00;30;Keine;Day 1\n"
            b"2026-01-16;08:00;16:00;45;Keine;Day 2\n"
            b"2026-01-17;07:30;15:30;30;Keine;Day 3\n"
        )

        results = list(handler.deserialize(csv_content))

        assert len(results) == 3
        assert results[0][0] == 2
        assert results[1][0] == 3
        assert results[2][0] == 4

    def test_deserialize_handles_quoted_fields_with_special_characters(self):
        """Test deserializing quoted fields containing semicolons and commas."""
        handler = CSVFormatHandler()
        csv_content = (
            b"\xef\xbb\xbf"
            b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n"
            b'2026-01-15;07:00;15:00;30;Keine;"Meeting with CEO; discussed project, very productive"\n'
        )

        results = list(handler.deserialize(csv_content))

        assert len(results) == 1
        row_num, fields = results[0]

        # Should correctly parse quoted field
        assert "Meeting with CEO" in fields["notes"]
        assert "discussed project" in fields["notes"]

    def test_deserialize_handles_empty_notes_field(self):
        """Test deserializing entries with empty notes field."""
        handler = CSVFormatHandler()
        csv_content = (
            b"\xef\xbb\xbf"
            b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n"
            b"2026-01-15;07:00;15:00;30;Keine;\n"
        )

        results = list(handler.deserialize(csv_content))

        assert len(results) == 1
        row_num, fields = results[0]

        assert fields["notes"] == ""


class TestCSVFormatHandlerValidateStructure:
    """Tests for CSVFormatHandler.validate_structure() method."""

    def test_validate_structure_valid_csv_returns_empty_list(self):
        """Test that valid CSV returns empty error list."""
        handler = CSVFormatHandler()
        csv_content = (
            b"\xef\xbb\xbf"
            b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n"
            b"2026-01-15;07:00;15:00;30;Keine;Test\n"
        )

        errors = handler.validate_structure(csv_content)

        assert errors == []
        assert isinstance(errors, list)

    def test_validate_structure_missing_required_columns(self):
        """Test that missing required columns returns ValidationError."""
        handler = CSVFormatHandler()
        # Missing "Pause (Min)" and "Abwesenheit" columns
        csv_content = b"\xef\xbb\xbfDatum;Startzeit;Endzeit;Notizen\n"

        errors = handler.validate_structure(csv_content)

        assert len(errors) >= 1
        assert any(error.code == "missing_column" for error in errors)
        assert any("Pause (Min)" in error.message or "Abwesenheit" in error.message for error in errors)

    def test_validate_structure_extra_columns_ignored(self):
        """Test that extra columns are ignored (no error)."""
        handler = CSVFormatHandler()
        # Has all required columns plus extra "Extra" column
        csv_content = (
            b"\xef\xbb\xbf"
            b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen;Extra\n"
            b"2026-01-15;07:00;15:00;30;Keine;Test;Value\n"
        )

        errors = handler.validate_structure(csv_content)

        assert errors == []

    def test_validate_structure_invalid_encoding(self):
        """Test that non-UTF8 encoding returns ValidationError."""
        handler = CSVFormatHandler()
        # Latin-1 encoded content (not UTF-8)
        csv_content = b"Datum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n"
        csv_content += "2026-01-15;07:00;15:00;30;Keine;Ä".encode("latin-1")

        errors = handler.validate_structure(csv_content)

        # Should detect encoding issue
        assert len(errors) >= 1
        assert any(error.code == "invalid_encoding" for error in errors)

    def test_validate_structure_empty_file(self):
        """Test that empty file returns ValidationError."""
        handler = CSVFormatHandler()
        csv_content = b""

        errors = handler.validate_structure(csv_content)

        assert len(errors) >= 1
        assert any(error.code == "empty_file" for error in errors)

    def test_validate_structure_headers_only_is_valid(self):
        """Test that file with headers only (no data rows) is valid."""
        handler = CSVFormatHandler()
        csv_content = b"\xef\xbb\xbfDatum;Startzeit;Endzeit;Pause (Min);Abwesenheit;Notizen\n"

        errors = handler.validate_structure(csv_content)

        assert errors == []

    def test_validate_structure_missing_all_required_columns(self):
        """Test that missing all required columns returns multiple errors."""
        handler = CSVFormatHandler()
        csv_content = b"\xef\xbb\xbfColumn1;Column2\n"

        errors = handler.validate_structure(csv_content)

        assert len(errors) >= 1
        # Should report missing columns
        assert any(error.code == "missing_column" for error in errors)

    def test_validate_structure_case_sensitive_headers(self):
        """Test that header matching is case-sensitive."""
        handler = CSVFormatHandler()
        # Wrong case: "datum" instead of "Datum"
        csv_content = b"\xef\xbb\xbfdatum;startzeit;endzeit;pause (min);abwesenheit;notizen\n"

        errors = handler.validate_structure(csv_content)

        # Should fail because headers don't match exactly
        assert len(errors) >= 1
        assert any(error.code == "missing_column" for error in errors)


class TestCSVFormatHandlerAbsenceMappings:
    """Tests for absence type mapping constants."""

    def test_absence_map_contains_all_types(self):
        """Test that ABSENCE_MAP contains all expected absence types."""
        expected_types = ["none", "vacation", "sick", "holiday", "flex_time"]

        for absence_type in expected_types:
            assert absence_type in CSVFormatHandler.ABSENCE_MAP

    def test_absence_map_german_translations(self):
        """Test that ABSENCE_MAP has correct German translations."""
        handler = CSVFormatHandler()

        assert handler.ABSENCE_MAP["none"] == "Keine"
        assert handler.ABSENCE_MAP["vacation"] == "Urlaub"
        assert handler.ABSENCE_MAP["sick"] == "Krank"
        assert handler.ABSENCE_MAP["holiday"] == "Feiertag"
        assert handler.ABSENCE_MAP["flex_time"] == "Gleitzeit"

    def test_reverse_absence_map_inverts_absence_map(self):
        """Test that REVERSE_ABSENCE_MAP correctly inverts ABSENCE_MAP."""
        handler = CSVFormatHandler()

        assert handler.REVERSE_ABSENCE_MAP["Keine"] == "none"
        assert handler.REVERSE_ABSENCE_MAP["Urlaub"] == "vacation"
        assert handler.REVERSE_ABSENCE_MAP["Krank"] == "sick"
        assert handler.REVERSE_ABSENCE_MAP["Feiertag"] == "holiday"
        assert handler.REVERSE_ABSENCE_MAP["Gleitzeit"] == "flex_time"

    def test_absence_maps_are_bidirectional(self):
        """Test that both absence maps are complete inverses."""
        handler = CSVFormatHandler()

        for internal, german in handler.ABSENCE_MAP.items():
            assert handler.REVERSE_ABSENCE_MAP[german] == internal

        for german, internal in handler.REVERSE_ABSENCE_MAP.items():
            assert handler.ABSENCE_MAP[internal] == german


class TestCSVFormatHandlerHeaders:
    """Tests for CSV header constants."""

    def test_headers_constant_contains_all_columns(self):
        """Test that HEADERS constant contains all required columns."""
        expected_headers = ["Datum", "Startzeit", "Endzeit", "Pause (Min)", "Abwesenheit", "Notizen"]

        assert CSVFormatHandler.HEADERS == expected_headers

    def test_headers_in_correct_order(self):
        """Test that headers are in the correct order."""
        handler = CSVFormatHandler()

        assert handler.HEADERS[0] == "Datum"
        assert handler.HEADERS[1] == "Startzeit"
        assert handler.HEADERS[2] == "Endzeit"
        assert handler.HEADERS[3] == "Pause (Min)"
        assert handler.HEADERS[4] == "Abwesenheit"
        assert handler.HEADERS[5] == "Notizen"
