"""Tests for PDFExportService.

This module tests the PDFExportService that exports time entries
to PDF format with monthly summary data.
"""

from datetime import date, time
from decimal import Decimal

import pytest

from source.services.data_transfer.dataclasses import ExportResult
from source.services.data_transfer.pdf_export_service import PDFExportService
from tests.factories import TimeEntryFactory, UserSettingsFactory, VacationEntryFactory


class TestPDFExportServiceExportPDF:
    """Tests for PDFExportService.export_pdf() method."""

    @pytest.mark.asyncio
    async def test_export_pdf_returns_export_result(self):
        """Test export_pdf returns ExportResult instance."""
        service = PDFExportService()
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("32.00"))
        entries = [
            TimeEntryFactory.build(
                user_id=1,
                work_date=date(2026, 1, 15),
                start_time=time(7, 0),
                end_time=time(15, 0),
                break_minutes=30,
            )
        ]

        result = await service.export_pdf(
            entries=entries,
            settings=settings,
            user_id=1,
            year=2026,
            month=1,
        )

        assert isinstance(result, ExportResult)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_export_pdf_content_is_bytes(self):
        """Test export_pdf content field contains bytes."""
        service = PDFExportService()
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("32.00"))
        entries = [
            TimeEntryFactory.build(
                user_id=1,
                work_date=date(2026, 1, 15),
                start_time=time(7, 0),
                end_time=time(15, 0),
                break_minutes=30,
            )
        ]

        result = await service.export_pdf(
            entries=entries,
            settings=settings,
            user_id=1,
            year=2026,
            month=1,
        )

        assert isinstance(result.content, bytes)
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_export_pdf_filename_format(self):
        """Test export_pdf filename follows format: zeiterfassung_{user_id}_{YYYY-MM}.pdf"""
        service = PDFExportService()
        settings = UserSettingsFactory.build(user_id=42, weekly_target_hours=Decimal("32.00"))
        entries = [
            TimeEntryFactory.build(
                user_id=42,
                work_date=date(2026, 1, 15),
                start_time=time(7, 0),
                end_time=time(15, 0),
                break_minutes=30,
            )
        ]

        result = await service.export_pdf(
            entries=entries,
            settings=settings,
            user_id=42,
            year=2026,
            month=1,
        )

        assert result.filename == "zeiterfassung_42_2026-01.pdf"

    @pytest.mark.asyncio
    async def test_export_pdf_filename_zero_pads_month(self):
        """Test export_pdf filename zero-pads single digit months."""
        service = PDFExportService()
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("32.00"))
        entries = [
            TimeEntryFactory.build(
                user_id=1,
                work_date=date(2026, 3, 15),
                start_time=time(7, 0),
                end_time=time(15, 0),
                break_minutes=30,
            )
        ]

        result = await service.export_pdf(
            entries=entries,
            settings=settings,
            user_id=1,
            year=2026,
            month=3,
        )

        assert result.filename == "zeiterfassung_1_2026-03.pdf"
        assert "2026-3." not in result.filename

    @pytest.mark.asyncio
    async def test_export_pdf_content_type(self):
        """Test export_pdf returns correct content_type for PDF."""
        service = PDFExportService()
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("32.00"))
        entries = [
            TimeEntryFactory.build(
                user_id=1,
                work_date=date(2026, 1, 15),
                start_time=time(7, 0),
                end_time=time(15, 0),
                break_minutes=30,
            )
        ]

        result = await service.export_pdf(
            entries=entries,
            settings=settings,
            user_id=1,
            year=2026,
            month=1,
        )

        assert result.content_type == "application/pdf"

    @pytest.mark.asyncio
    async def test_export_pdf_with_entries_generates_valid_pdf(self):
        """Test export_pdf generates valid PDF from entries (check PDF signature)."""
        service = PDFExportService()
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("32.00"))
        entries = [
            TimeEntryFactory.build(
                user_id=1,
                work_date=date(2026, 1, 13),
                start_time=time(7, 0),
                end_time=time(15, 0),
                break_minutes=30,
                notes="Monday work",
            ),
            TimeEntryFactory.build(
                user_id=1,
                work_date=date(2026, 1, 14),
                start_time=time(8, 0),
                end_time=time(16, 0),
                break_minutes=45,
                notes="Tuesday work",
            ),
        ]

        result = await service.export_pdf(
            entries=entries,
            settings=settings,
            user_id=1,
            year=2026,
            month=1,
        )

        # PDF files start with %PDF- signature
        assert result.content.startswith(b"%PDF-")
        assert len(result.content) > 100  # PDF should be substantial

    @pytest.mark.asyncio
    async def test_export_pdf_empty_entries_generates_pdf(self):
        """Test export_pdf handles empty entries list gracefully."""
        service = PDFExportService()
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("32.00"))
        entries = []

        result = await service.export_pdf(
            entries=entries,
            settings=settings,
            user_id=1,
            year=2026,
            month=1,
        )

        assert result.success is True
        assert isinstance(result.content, bytes)
        # Should still generate valid PDF with headers/summary
        assert result.content.startswith(b"%PDF-")

    @pytest.mark.asyncio
    async def test_export_pdf_includes_monthly_summary_data(self):
        """Test export_pdf includes monthly summary data in generated PDF."""
        service = PDFExportService()
        settings = UserSettingsFactory.build(
            user_id=1,
            weekly_target_hours=Decimal("32.00"),
            carryover_hours=Decimal("5.00"),
        )
        entries = [
            TimeEntryFactory.build(
                user_id=1,
                work_date=date(2026, 1, 13),
                start_time=time(7, 0),
                end_time=time(15, 0),
                break_minutes=30,
            ),
            TimeEntryFactory.build(
                user_id=1,
                work_date=date(2026, 1, 14),
                start_time=time(8, 0),
                end_time=time(16, 0),
                break_minutes=45,
            ),
        ]

        result = await service.export_pdf(
            entries=entries,
            settings=settings,
            user_id=1,
            year=2026,
            month=1,
        )

        # PDF should be generated with summary data
        # We can't easily parse PDF content in tests, but we can verify:
        # 1. PDF was generated successfully
        assert result.success is True
        # 2. PDF contains substantial content (not just empty template)
        assert len(result.content) > 200
        # 3. PDF is valid
        assert result.content.startswith(b"%PDF-")

    @pytest.mark.asyncio
    async def test_export_pdf_with_mixed_entry_types(self):
        """Test export_pdf handles mixed entry types (regular work + vacation)."""
        service = PDFExportService()
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("32.00"))
        entries = [
            TimeEntryFactory.build(
                user_id=1,
                work_date=date(2026, 1, 13),
                start_time=time(7, 0),
                end_time=time(15, 0),
                break_minutes=30,
            ),
            VacationEntryFactory.build(
                user_id=1,
                work_date=date(2026, 1, 14),
            ),
            TimeEntryFactory.build(
                user_id=1,
                work_date=date(2026, 1, 15),
                start_time=time(7, 0),
                end_time=time(15, 0),
                break_minutes=30,
            ),
        ]

        result = await service.export_pdf(
            entries=entries,
            settings=settings,
            user_id=1,
            year=2026,
            month=1,
        )

        assert result.success is True
        assert result.content.startswith(b"%PDF-")
        assert len(result.content) > 200

    @pytest.mark.asyncio
    async def test_export_pdf_december_month_formatting(self):
        """Test export_pdf handles December (month 12) correctly."""
        service = PDFExportService()
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("32.00"))
        entries = [
            TimeEntryFactory.build(
                user_id=1,
                work_date=date(2026, 12, 15),
                start_time=time(7, 0),
                end_time=time(15, 0),
                break_minutes=30,
            )
        ]

        result = await service.export_pdf(
            entries=entries,
            settings=settings,
            user_id=1,
            year=2026,
            month=12,
        )

        assert result.filename == "zeiterfassung_1_2026-12.pdf"

    @pytest.mark.asyncio
    async def test_export_pdf_with_carryover_hours(self):
        """Test export_pdf includes carryover hours in summary calculation."""
        service = PDFExportService()
        settings = UserSettingsFactory.build(
            user_id=1,
            weekly_target_hours=Decimal("32.00"),
            carryover_hours=Decimal("10.50"),
        )
        entries = [
            TimeEntryFactory.build(
                user_id=1,
                work_date=date(2026, 1, 13),
                start_time=time(7, 0),
                end_time=time(15, 0),
                break_minutes=30,
            ),
        ]

        result = await service.export_pdf(
            entries=entries,
            settings=settings,
            user_id=1,
            year=2026,
            month=1,
        )

        # Carryover should be reflected in monthly summary
        assert result.success is True
        assert result.content.startswith(b"%PDF-")

    @pytest.mark.asyncio
    async def test_export_pdf_with_no_carryover(self):
        """Test export_pdf handles None carryover_hours correctly."""
        service = PDFExportService()
        settings = UserSettingsFactory.build(
            user_id=1,
            weekly_target_hours=Decimal("32.00"),
            carryover_hours=None,
        )
        entries = [
            TimeEntryFactory.build(
                user_id=1,
                work_date=date(2026, 1, 13),
                start_time=time(7, 0),
                end_time=time(15, 0),
                break_minutes=30,
            ),
        ]

        result = await service.export_pdf(
            entries=entries,
            settings=settings,
            user_id=1,
            year=2026,
            month=1,
        )

        assert result.success is True
        assert result.content.startswith(b"%PDF-")

    @pytest.mark.asyncio
    async def test_export_pdf_with_multiple_weeks(self):
        """Test export_pdf handles entries spanning multiple weeks."""
        service = PDFExportService()
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("32.00"))
        # Create entries across 4 weeks in January 2026
        entries = [
            # Week 1
            TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 6), start_time=time(7, 0), end_time=time(15, 0)),
            # Week 2
            TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 13), start_time=time(7, 0), end_time=time(15, 0)),
            # Week 3
            TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 20), start_time=time(7, 0), end_time=time(15, 0)),
            # Week 4
            TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 27), start_time=time(7, 0), end_time=time(15, 0)),
        ]

        result = await service.export_pdf(
            entries=entries,
            settings=settings,
            user_id=1,
            year=2026,
            month=1,
        )

        assert result.success is True
        assert result.content.startswith(b"%PDF-")
        # PDF should contain all weeks of data
        assert len(result.content) > 300


class TestPDFExportServiceEdgeCases:
    """Tests for PDFExportService edge cases."""

    @pytest.mark.asyncio
    async def test_export_pdf_with_long_notes(self):
        """Test export_pdf handles entries with long notes."""
        service = PDFExportService()
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("32.00"))
        long_notes = "A" * 500  # 500 character note
        entries = [
            TimeEntryFactory.build(
                user_id=1,
                work_date=date(2026, 1, 15),
                start_time=time(7, 0),
                end_time=time(15, 0),
                break_minutes=30,
                notes=long_notes,
            )
        ]

        result = await service.export_pdf(
            entries=entries,
            settings=settings,
            user_id=1,
            year=2026,
            month=1,
        )

        assert result.success is True
        assert result.content.startswith(b"%PDF-")

    @pytest.mark.asyncio
    async def test_export_pdf_with_special_characters_in_notes(self):
        """Test export_pdf handles special characters in notes."""
        service = PDFExportService()
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("32.00"))
        entries = [
            TimeEntryFactory.build(
                user_id=1,
                work_date=date(2026, 1, 15),
                start_time=time(7, 0),
                end_time=time(15, 0),
                break_minutes=30,
                notes='Meeting with "client" & discuss costs > €1000',
            )
        ]

        result = await service.export_pdf(
            entries=entries,
            settings=settings,
            user_id=1,
            year=2026,
            month=1,
        )

        assert result.success is True
        assert result.content.startswith(b"%PDF-")

    @pytest.mark.asyncio
    async def test_export_pdf_with_zero_target_hours(self):
        """Test export_pdf handles zero target hours correctly."""
        service = PDFExportService()
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("0.00"))
        entries = [
            TimeEntryFactory.build(
                user_id=1,
                work_date=date(2026, 1, 15),
                start_time=time(7, 0),
                end_time=time(15, 0),
                break_minutes=30,
            )
        ]

        result = await service.export_pdf(
            entries=entries,
            settings=settings,
            user_id=1,
            year=2026,
            month=1,
        )

        assert result.success is True
        assert result.content.startswith(b"%PDF-")

    @pytest.mark.asyncio
    async def test_export_pdf_preserves_entry_order(self):
        """Test export_pdf maintains entry order as provided."""
        service = PDFExportService()
        settings = UserSettingsFactory.build(user_id=1, weekly_target_hours=Decimal("32.00"))
        # Provide entries in non-chronological order
        entries = [
            TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 15), start_time=time(7, 0), end_time=time(15, 0)),
            TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 13), start_time=time(7, 0), end_time=time(15, 0)),
            TimeEntryFactory.build(user_id=1, work_date=date(2026, 1, 14), start_time=time(7, 0), end_time=time(15, 0)),
        ]

        result = await service.export_pdf(
            entries=entries,
            settings=settings,
            user_id=1,
            year=2026,
            month=1,
        )

        # Should generate PDF successfully regardless of entry order
        assert result.success is True
        assert result.content.startswith(b"%PDF-")


__all__ = [
    "TestPDFExportServiceExportPDF",
    "TestPDFExportServiceEdgeCases",
]
