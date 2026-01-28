"""CSV format handler for time entry import/export.

This module implements the FormatHandler interface for CSV files with
German Excel-compatible formatting (semicolon delimiter, UTF-8 with BOM).
"""

import csv
import io
from collections.abc import Iterator

from source.services.data_transfer.base import FormatHandler
from source.services.data_transfer.dataclasses import TimeEntryRow, ValidationError


class CSVFormatHandler(FormatHandler):
    """Format handler for CSV files with German Excel conventions.

    CSV format specifications:
    - Delimiter: semicolon (;)
    - Encoding: UTF-8 with BOM
    - Headers: German column names
    - Date format: YYYY-MM-DD
    - Time format: HH:MM
    - Absence types: German translations
    """

    # German column headers (used for export)
    HEADERS = ["Datum", "Startzeit", "Endzeit", "Pause (Min)", "Abwesenheit", "Notizen"]

    # Mapping from German headers to internal field names
    HEADER_MAP = {
        "Datum": "work_date",
        "Startzeit": "start_time",
        "Endzeit": "end_time",
        "Pause (Min)": "break_minutes",
        "Abwesenheit": "absence_type",
        "Notizen": "notes",
    }

    # Alternative English headers for import (API testing compatibility)
    ENGLISH_HEADER_MAP = {
        "work_date": "work_date",
        "start_time": "start_time",
        "end_time": "end_time",
        "break_minutes": "break_minutes",
        "absence_type": "absence_type",
        "notes": "notes",
    }

    # Absence type translations (internal -> German)
    ABSENCE_MAP = {
        "none": "Keine",
        "vacation": "Urlaub",
        "sick": "Krank",
        "holiday": "Feiertag",
        "flex_time": "Gleitzeit",
    }

    # Reverse mapping for import (German -> internal)
    REVERSE_ABSENCE_MAP = {v: k for k, v in ABSENCE_MAP.items()}

    def serialize(self, rows: list[TimeEntryRow]) -> bytes:
        """Convert rows to CSV bytes.

        Args:
            rows: List of TimeEntryRow objects to serialize

        Returns:
            CSV data as UTF-8 with BOM bytes
        """
        # UTF-8 BOM
        bom = b"\xef\xbb\xbf"

        # Create StringIO buffer for CSV writer (use Unix line endings)
        output = io.StringIO(newline="")
        writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL, lineterminator="\n")

        # Write header row
        writer.writerow(self.HEADERS)

        # Write data rows
        for row in rows:
            writer.writerow(
                [
                    row.work_date.isoformat(),  # YYYY-MM-DD format
                    row.start_time.strftime("%H:%M") if row.start_time else "",
                    row.end_time.strftime("%H:%M") if row.end_time else "",
                    str(row.break_minutes),
                    self.ABSENCE_MAP.get(row.absence_type, "Keine"),
                    row.notes or "",
                ]
            )

        # Convert to bytes with BOM
        return bom + output.getvalue().encode("utf-8")

    def deserialize(self, content: bytes) -> Iterator[tuple[int, dict]]:
        """Parse CSV bytes to (row_number, field_dict) tuples.

        Args:
            content: CSV data as bytes

        Yields:
            Tuples of (row_number, dict of field values)
        """
        # Strip BOM if present
        if content.startswith(b"\xef\xbb\xbf"):
            content = content[3:]

        # Decode to text
        text = content.decode("utf-8")

        # Detect delimiter (check first line for comma vs semicolon)
        delimiter = ";" if ";" in text.split("\n")[0] else ","

        # Parse CSV with DictReader
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)

        # Detect header format (German or English)
        if reader.fieldnames and "Datum" in reader.fieldnames:
            header_map = self.HEADER_MAP
        else:
            header_map = self.ENGLISH_HEADER_MAP

        # Yield rows with row numbers (data rows start at 2)
        for row_num, row in enumerate(reader, start=2):
            # Map headers to internal field names
            mapped_row = {}
            for header, internal_field in header_map.items():
                mapped_row[internal_field] = row.get(header, "")

            yield (row_num, mapped_row)

    def validate_structure(self, content: bytes) -> list[ValidationError]:
        """Validate CSV structure (headers, encoding, etc).

        Args:
            content: Raw CSV bytes to validate

        Returns:
            List of ValidationError objects (empty if valid)
        """
        errors = []

        # Check for empty content
        if not content or content == b"\xef\xbb\xbf":
            errors.append(
                ValidationError(
                    row_number=0,
                    field="file",
                    message="Datei ist leer",
                    code="empty_file",
                )
            )
            return errors

        # Try to decode (check encoding)
        try:
            if content.startswith(b"\xef\xbb\xbf"):
                text = content[3:].decode("utf-8")
            else:
                text = content.decode("utf-8")
        except UnicodeDecodeError:
            errors.append(
                ValidationError(
                    row_number=0,
                    field="encoding",
                    message="Ungültige Zeichenkodierung (UTF-8 erwartet)",
                    code="invalid_encoding",
                )
            )
            return errors

        # Detect delimiter (check first line for comma vs semicolon)
        delimiter = ";" if ";" in text.split("\n")[0] else ","

        # Parse header row
        reader = csv.reader(io.StringIO(text), delimiter=delimiter)
        try:
            headers = next(reader)
        except StopIteration:
            errors.append(
                ValidationError(
                    row_number=0,
                    field="file",
                    message="Datei ist leer",
                    code="empty_file",
                )
            )
            return errors

        # Check if German or English headers
        found = set(headers)
        german_headers = set(self.HEADERS)
        english_headers = set(self.ENGLISH_HEADER_MAP.keys())

        # Try German format first
        if found == german_headers or german_headers.issubset(found):
            # German format is valid
            return errors

        # Try English format
        if found == english_headers or english_headers.issubset(found):
            # English format is valid
            return errors

        # Neither format matches - report missing columns
        # Prefer German format for error messages
        missing = german_headers - found
        if missing:
            for col in sorted(missing):
                errors.append(
                    ValidationError(
                        row_number=1,
                        field="headers",
                        message=f"Fehlende Spalte: {col}",
                        code="missing_column",
                    )
                )

        return errors

    @property
    def content_type(self) -> str:
        """MIME type for CSV files.

        Returns:
            CSV MIME type with charset
        """
        return "text/csv; charset=utf-8"

    @property
    def file_extension(self) -> str:
        """File extension for CSV files.

        Returns:
            File extension without dot
        """
        return "csv"


__all__ = [
    "CSVFormatHandler",
]
