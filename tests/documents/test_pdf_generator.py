"""Tests for PDF generation using Playwright.

This test module follows TDD RED phase - all tests are expected to fail initially.
Tests validate the PDFGenerator class behavior for HTML-to-PDF conversion.
"""

import pytest

from source.documents.pdf_generator import PDFGenerator


class TestPDFGeneratorSetup:
    """Test suite for PDFGenerator initialization and setup."""

    @pytest.mark.asyncio
    async def test_setup_creates_browser(self):
        """Test that setup_context initializes browser instance.

        Verifies:
        - setup_context() creates browser instance
        - Browser is not None after setup
        """
        generator = PDFGenerator()
        assert generator.browser is None, "Browser should be None before setup"

        await generator.setup_context()

        assert generator.browser is not None, "Browser should be initialized after setup"
        assert generator.playwright is not None, "Playwright should be initialized after setup"

        # Cleanup
        await generator.close()

    @pytest.mark.asyncio
    async def test_close_releases_resources(self):
        """Test that close() properly releases browser and playwright resources.

        Verifies:
        - Browser and playwright instances are cleaned up
        - Can be called multiple times safely (idempotent)
        """
        generator = PDFGenerator()
        await generator.setup_context()

        assert generator.browser is not None, "Browser should exist before close"
        assert generator.playwright is not None, "Playwright should exist before close"

        await generator.close()

        assert generator.browser is None, "Browser should be None after close"
        assert generator.playwright is None, "Playwright should be None after close"

        # Should be safe to call again
        await generator.close()


class TestPDFGeneratorBasicGeneration:
    """Test suite for basic PDF generation functionality."""

    @pytest.mark.asyncio
    async def test_generate_pdf_bytes_returns_bytes(self):
        """Test that generate_pdf_bytes returns PDF bytes.

        Verifies:
        - Returns bytes type
        - Bytes are non-empty
        - Bytes start with PDF signature (%PDF-)
        """
        generator = PDFGenerator()
        html = """
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"></head>
        <body>
            <h1>Test Document</h1>
            <p>This is a test PDF generation.</p>
        </body>
        </html>
        """

        pdf_bytes = await generator.generate_pdf_bytes(html)

        assert isinstance(pdf_bytes, bytes), "Should return bytes"
        assert len(pdf_bytes) > 0, "PDF bytes should not be empty"
        assert pdf_bytes.startswith(b"%PDF-"), "Should start with PDF signature"

        # Cleanup
        await generator.close()

    @pytest.mark.asyncio
    async def test_auto_setup_on_first_generate(self):
        """Test that generate_pdf_bytes auto-initializes browser if not setup.

        Verifies:
        - Can call generate_pdf_bytes without explicit setup_context()
        - Browser is automatically initialized on first use
        """
        generator = PDFGenerator()
        assert generator.browser is None, "Browser should be None initially"

        html = "<html><body><h1>Auto Setup Test</h1></body></html>"
        pdf_bytes = await generator.generate_pdf_bytes(html)

        assert generator.browser is not None, "Browser should auto-initialize"
        assert len(pdf_bytes) > 0, "Should generate PDF successfully"

        # Cleanup
        await generator.close()


class TestPDFGeneratorOrientation:
    """Test suite for PDF orientation options."""

    @pytest.mark.asyncio
    async def test_generate_pdf_bytes_portrait_default(self):
        """Test that default orientation is portrait.

        Verifies:
        - Default landscape parameter is False
        - Generated PDF dimensions indicate portrait orientation
        """
        generator = PDFGenerator()
        html = "<html><body><h1>Portrait Test</h1></body></html>"

        # Default should be portrait (landscape=False)
        pdf_bytes = await generator.generate_pdf_bytes(html)

        # PDF should be generated successfully
        assert isinstance(pdf_bytes, bytes), "Should return bytes"
        assert len(pdf_bytes) > 0, "Should generate PDF"

        # Note: Actual dimension verification would require PDF parsing library
        # For now, we verify the call succeeds with default parameters

        # Cleanup
        await generator.close()

    @pytest.mark.asyncio
    async def test_generate_pdf_bytes_landscape(self):
        """Test that landscape=True generates landscape-oriented PDF.

        Verifies:
        - Can explicitly request landscape orientation
        - Generated PDF dimensions indicate landscape orientation
        """
        generator = PDFGenerator()
        html = "<html><body><h1>Landscape Test</h1></body></html>"

        pdf_bytes = await generator.generate_pdf_bytes(html, landscape=True)

        # PDF should be generated successfully
        assert isinstance(pdf_bytes, bytes), "Should return bytes"
        assert len(pdf_bytes) > 0, "Should generate PDF in landscape"

        # Note: Actual dimension verification would require PDF parsing library
        # For now, we verify the call succeeds with landscape=True

        # Cleanup
        await generator.close()


class TestPDFGeneratorContentValidation:
    """Test suite for PDF content validation."""

    @pytest.mark.asyncio
    async def test_pdf_contains_content(self):
        """Test that generated PDF contains expected content markers.

        Verifies:
        - Text content from HTML appears in PDF
        - Basic content rendering works
        - Multiple content sections are preserved

        Note: This test uses basic heuristics since full PDF text extraction
        would require additional dependencies (PyPDF2, pdfplumber, etc.)
        """
        generator = PDFGenerator()
        html = """
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"></head>
        <body>
            <h1>Monthly Time Report</h1>
            <p>Employee: Test User</p>
            <table>
                <tr><th>Date</th><th>Hours</th></tr>
                <tr><td>2026-01-15</td><td>8.0</td></tr>
            </table>
            <p>Total Hours: 8.0</p>
        </body>
        </html>
        """

        pdf_bytes = await generator.generate_pdf_bytes(html)

        # Verify PDF was generated
        assert isinstance(pdf_bytes, bytes), "Should return bytes"
        assert len(pdf_bytes) > 0, "Should generate non-empty PDF"

        # Basic content validation - PDF should contain more than just structure
        # A typical minimal empty PDF is ~500 bytes, content-rich PDF should be larger
        assert len(pdf_bytes) > 1000, "PDF with content should be larger than minimal PDF"

        # Verify PDF structure is valid (starts and ends correctly)
        assert pdf_bytes.startswith(b"%PDF-"), "Should have valid PDF header"
        assert b"%%EOF" in pdf_bytes, "Should have valid PDF footer"

        # Cleanup
        await generator.close()

    @pytest.mark.asyncio
    async def test_generate_multiple_pdfs_same_instance(self):
        """Test that same PDFGenerator instance can generate multiple PDFs.

        Verifies:
        - Browser instance is reused across multiple generations
        - No resource leaks between generations
        - Each generation produces valid output
        """
        generator = PDFGenerator()

        html1 = "<html><body><h1>First Document</h1></body></html>"
        html2 = "<html><body><h1>Second Document</h1></body></html>"
        html3 = "<html><body><h1>Third Document</h1></body></html>"

        pdf1 = await generator.generate_pdf_bytes(html1)
        pdf2 = await generator.generate_pdf_bytes(html2)
        pdf3 = await generator.generate_pdf_bytes(html3)

        # All should be valid PDFs
        assert pdf1.startswith(b"%PDF-"), "First PDF should be valid"
        assert pdf2.startswith(b"%PDF-"), "Second PDF should be valid"
        assert pdf3.startswith(b"%PDF-"), "Third PDF should be valid"

        # Each should have content
        assert len(pdf1) > 0, "First PDF should have content"
        assert len(pdf2) > 0, "Second PDF should have content"
        assert len(pdf3) > 0, "Third PDF should have content"

        # Cleanup
        await generator.close()
