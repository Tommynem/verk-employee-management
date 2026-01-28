"""Data transfer objects for import/export operations.

This module defines format-agnostic DTOs for representing time entry rows,
validation errors, and operation results.
"""

from dataclasses import dataclass, field
from datetime import date, time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from source.database.models import TimeEntry


@dataclass
class TimeEntryRow:
    """Format-agnostic representation of a time entry row.

    This dataclass provides a normalized representation of time entry data
    that can be used across different import/export formats (CSV, Excel, JSON, etc).

    Args:
        work_date: Date of the time entry
        start_time: Optional start time for work entries
        end_time: Optional end time for work entries
        break_minutes: Break duration in minutes (defaults to 0)
        absence_type: Type of absence (defaults to "none")
        notes: Optional notes or comments
    """

    work_date: date
    start_time: time | None = None
    end_time: time | None = None
    break_minutes: int = 0
    absence_type: str = "none"
    notes: str | None = None


@dataclass
class ValidationError:
    """Validation error with location information.

    This dataclass represents a validation error encountered during import
    or processing of time entry data.

    Args:
        row_number: Row number where error occurred (0 for structural errors)
        field: Field name where error occurred
        message: German user-facing error message
        code: Machine-readable error code
    """

    row_number: int
    field: str
    message: str  # German for user-facing
    code: str  # Machine-readable code


@dataclass
class ImportResult:
    """Result of an import operation.

    This dataclass contains the outcome of importing time entry data,
    including any validation errors and successfully imported entries.

    Args:
        success: Whether the import operation was successful
        imported_count: Number of entries successfully imported
        skipped_count: Number of entries skipped due to errors
        errors: List of validation errors encountered
        entries: List of successfully imported TimeEntry objects
    """

    success: bool
    imported_count: int = 0
    skipped_count: int = 0
    errors: list[ValidationError] = field(default_factory=list)
    entries: list["TimeEntry"] = field(default_factory=list)


@dataclass
class ExportResult:
    """Result of an export operation.

    This dataclass contains the outcome of exporting time entry data
    to a specific format.

    Args:
        success: Whether the export operation was successful
        content: Exported data as bytes
        filename: Suggested filename for the export
        content_type: MIME type of the exported content
    """

    success: bool
    content: bytes = b""
    filename: str = ""
    content_type: str = ""


__all__ = [
    "TimeEntryRow",
    "ValidationError",
    "ImportResult",
    "ExportResult",
]
