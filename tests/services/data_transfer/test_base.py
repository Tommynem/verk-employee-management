"""Tests for base format handler classes.

This module tests the abstract base classes for format handlers:
- FormatHandler: Abstract base for format-specific serializers/deserializers
"""

import pytest

from source.services.data_transfer.base import FormatHandler
from source.services.data_transfer.dataclasses import ValidationError


class TestFormatHandler:
    """Tests for FormatHandler abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that FormatHandler cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            FormatHandler()

    def test_concrete_handler_must_implement_serialize(self):
        """Test that concrete handler must implement serialize method."""

        class IncompleteHandler(FormatHandler):
            def deserialize(self, content: bytes):
                pass

            def validate_structure(self, content: bytes):
                pass

            @property
            def content_type(self) -> str:
                return "text/csv"

            @property
            def file_extension(self) -> str:
                return "csv"

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteHandler()

    def test_concrete_handler_must_implement_deserialize(self):
        """Test that concrete handler must implement deserialize method."""

        class IncompleteHandler(FormatHandler):
            def serialize(self, rows):
                pass

            def validate_structure(self, content: bytes):
                pass

            @property
            def content_type(self) -> str:
                return "text/csv"

            @property
            def file_extension(self) -> str:
                return "csv"

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteHandler()

    def test_concrete_handler_must_implement_validate_structure(self):
        """Test that concrete handler must implement validate_structure method."""

        class IncompleteHandler(FormatHandler):
            def serialize(self, rows):
                pass

            def deserialize(self, content: bytes):
                pass

            @property
            def content_type(self) -> str:
                return "text/csv"

            @property
            def file_extension(self) -> str:
                return "csv"

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteHandler()

    def test_concrete_handler_must_implement_content_type_property(self):
        """Test that concrete handler must implement content_type property."""

        class IncompleteHandler(FormatHandler):
            def serialize(self, rows):
                pass

            def deserialize(self, content: bytes):
                pass

            def validate_structure(self, content: bytes):
                pass

            @property
            def file_extension(self) -> str:
                return "csv"

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteHandler()

    def test_concrete_handler_must_implement_file_extension_property(self):
        """Test that concrete handler must implement file_extension property."""

        class IncompleteHandler(FormatHandler):
            def serialize(self, rows):
                pass

            def deserialize(self, content: bytes):
                pass

            def validate_structure(self, content: bytes):
                pass

            @property
            def content_type(self) -> str:
                return "text/csv"

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteHandler()

    def test_complete_handler_can_be_instantiated(self):
        """Test that handler with all methods implemented can be instantiated."""

        class CompleteHandler(FormatHandler):
            def serialize(self, rows):
                return b"test"

            def deserialize(self, content: bytes):
                yield (1, {})

            def validate_structure(self, content: bytes):
                return []

            @property
            def content_type(self) -> str:
                return "text/csv"

            @property
            def file_extension(self) -> str:
                return "csv"

        handler = CompleteHandler()

        assert handler is not None
        assert handler.content_type == "text/csv"
        assert handler.file_extension == "csv"

    def test_serialize_method_signature(self):
        """Test that serialize method has correct signature."""

        class TestHandler(FormatHandler):
            def serialize(self, rows):
                return b"test"

            def deserialize(self, content: bytes):
                yield (1, {})

            def validate_structure(self, content: bytes):
                return []

            @property
            def content_type(self) -> str:
                return "text/csv"

            @property
            def file_extension(self) -> str:
                return "csv"

        handler = TestHandler()
        result = handler.serialize([])

        assert isinstance(result, bytes)

    def test_deserialize_method_signature(self):
        """Test that deserialize method returns iterator of tuples."""

        class TestHandler(FormatHandler):
            def serialize(self, rows):
                return b"test"

            def deserialize(self, content: bytes):
                yield (1, {"work_date": "2026-01-28"})
                yield (2, {"work_date": "2026-01-29"})

            def validate_structure(self, content: bytes):
                return []

            @property
            def content_type(self) -> str:
                return "text/csv"

            @property
            def file_extension(self) -> str:
                return "csv"

        handler = TestHandler()
        results = list(handler.deserialize(b"test"))

        assert len(results) == 2
        assert results[0] == (1, {"work_date": "2026-01-28"})
        assert results[1] == (2, {"work_date": "2026-01-29"})

    def test_validate_structure_method_signature(self):
        """Test that validate_structure returns list of ValidationError."""

        class TestHandler(FormatHandler):
            def serialize(self, rows):
                return b"test"

            def deserialize(self, content: bytes):
                yield (1, {})

            def validate_structure(self, content: bytes):
                return [
                    ValidationError(
                        row_number=0,
                        field="structure",
                        message="Fehlende Spalte: work_date",
                        code="missing_column",
                    )
                ]

            @property
            def content_type(self) -> str:
                return "text/csv"

            @property
            def file_extension(self) -> str:
                return "csv"

        handler = TestHandler()
        errors = handler.validate_structure(b"invalid")

        assert len(errors) == 1
        assert isinstance(errors[0], ValidationError)
        assert errors[0].code == "missing_column"
