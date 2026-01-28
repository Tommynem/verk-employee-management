"""Base classes for format handlers.

This module defines the abstract base class for format-specific handlers
that serialize and deserialize time entry data.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterator

from source.services.data_transfer.dataclasses import TimeEntryRow, ValidationError


class FormatHandler(ABC):
    """Abstract base class for format handlers.

    Implement this for each supported format (CSV, JSON, Excel, etc).
    Each format handler is responsible for:
    - Serializing TimeEntryRow objects to bytes
    - Deserializing bytes to field dictionaries
    - Validating format-specific structure
    - Providing format metadata (content type, file extension)
    """

    @abstractmethod
    def serialize(self, rows: list[TimeEntryRow]) -> bytes:
        """Convert rows to bytes in this format.

        Args:
            rows: List of TimeEntryRow objects to serialize

        Returns:
            Serialized bytes in this format
        """
        pass

    @abstractmethod
    def deserialize(self, content: bytes) -> Iterator[tuple[int, dict]]:
        """Parse bytes to (row_number, field_dict) tuples.

        This method should yield tuples of (row_number, field_dict) where:
        - row_number is the 1-based row number in the source data
        - field_dict is a dictionary of field names to raw values

        Args:
            content: Raw bytes in this format

        Yields:
            Tuples of (row_number, dict of field values)
        """
        pass

    @abstractmethod
    def validate_structure(self, content: bytes) -> list[ValidationError]:
        """Validate format structure (headers, encoding, etc).

        This method should validate format-specific requirements such as:
        - File encoding
        - Required headers/columns
        - File structure validity
        - Format-specific constraints

        Args:
            content: Raw bytes to validate

        Returns:
            List of ValidationError objects (empty if valid)
        """
        pass

    @property
    @abstractmethod
    def content_type(self) -> str:
        """MIME type for this format.

        Returns:
            MIME type string (e.g., 'text/csv', 'application/json')
        """
        pass

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """File extension for this format.

        Returns:
            File extension without dot (e.g., 'csv', 'xlsx', 'json')
        """
        pass


__all__ = [
    "FormatHandler",
]
