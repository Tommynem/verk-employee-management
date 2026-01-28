"""Export service for time entry data.

This module provides the ExportService class that orchestrates exporting
time entries to various formats using format handlers.
"""

from source.database.models import TimeEntry
from source.services.data_transfer.base import FormatHandler
from source.services.data_transfer.csv_format import CSVFormatHandler
from source.services.data_transfer.dataclasses import ExportResult, TimeEntryRow


class ExportService:
    """Service for exporting time entries to various formats.

    This service coordinates the export process by:
    - Converting TimeEntry ORM objects to TimeEntryRow DTOs
    - Delegating serialization to the configured format handler
    - Generating appropriate filenames and metadata
    """

    def __init__(self, handler: FormatHandler | None = None):
        """Initialize with a format handler.

        Args:
            handler: Format handler for serialization. Defaults to CSVFormatHandler.
        """
        self._handler = handler or CSVFormatHandler()

    @property
    def handler(self) -> FormatHandler:
        """Get the format handler.

        Returns:
            The configured format handler
        """
        return self._handler

    def export_entries(
        self,
        entries: list[TimeEntry],
        user_id: int,
        year: int,
        month: int,
    ) -> ExportResult:
        """Export time entries to the configured format.

        Args:
            entries: List of TimeEntry ORM objects
            user_id: User ID for filename
            year: Year for filename
            month: Month for filename (1-12)

        Returns:
            ExportResult with success status, content bytes, filename, content_type
        """
        # Convert ORM objects to DTOs
        rows = [self._convert_entry(entry) for entry in entries]

        # Serialize using handler
        content = self._handler.serialize(rows)

        # Generate filename
        filename = self._generate_filename(user_id, year, month)

        return ExportResult(
            success=True,
            content=content,
            filename=filename,
            content_type=self._handler.content_type,
        )

    def _convert_entry(self, entry: TimeEntry) -> TimeEntryRow:
        """Convert TimeEntry ORM object to TimeEntryRow DTO.

        Args:
            entry: TimeEntry ORM model instance

        Returns:
            TimeEntryRow DTO for serialization
        """
        return TimeEntryRow(
            work_date=entry.work_date,
            start_time=entry.start_time,
            end_time=entry.end_time,
            break_minutes=entry.break_minutes,
            absence_type=entry.absence_type.value,  # Convert enum to string
            notes=entry.notes,
        )

    def _generate_filename(self, user_id: int, year: int, month: int) -> str:
        """Generate export filename.

        Args:
            user_id: User ID
            year: Year (YYYY)
            month: Month (1-12)

        Returns:
            Filename like 'zeiterfassung_1_2026-01.csv'
        """
        extension = self._handler.file_extension
        return f"zeiterfassung_{user_id}_{year}-{month:02d}.{extension}"


__all__ = [
    "ExportService",
]
