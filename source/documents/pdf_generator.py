"""PDF Generator Module for Verk Employee Management.

This class provides simplified PDF generation using Playwright for HTML to PDF conversion.
It provides functionality to generate PDF documents from HTML strings without requiring
file system operations or complex configuration.
"""

from playwright.async_api import Browser, Page, Playwright, async_playwright


class PDFGenerator:
    """Simplified PDF generator using Playwright for HTML to PDF conversion.

    This class manages a headless Chromium browser instance for converting HTML
    strings to PDF bytes. The browser instance can be reused across multiple
    PDF generations for efficiency.
    """

    def __init__(self) -> None:
        """Initialize generator with no active browser."""
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None

    async def setup_context(self) -> None:
        """Initialize headless Chromium browser.

        Sets up a headless Chromium browser with appropriate arguments for
        running in sandboxed environments. The browser instance is stored
        for reuse across multiple PDF generations.
        """
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-gpu",
            ],
        )

    async def generate_pdf_bytes(self, html: str, landscape: bool = False) -> bytes:
        """Generate PDF bytes from HTML string.

        Converts the provided HTML string to a PDF document and returns the
        raw PDF bytes. The browser is automatically initialized if not already
        set up.

        Args:
            html: Complete HTML document string to convert to PDF
            landscape: Use landscape orientation (default: portrait/False)

        Returns:
            PDF content as bytes

        Raises:
            RuntimeError: If browser setup fails
        """
        # Auto-setup browser if not initialized
        if not self.browser:
            await self.setup_context()
        assert self.browser is not None  # Type narrowing for mypy

        # Create new page for this generation
        page: Page = await self.browser.new_page()

        try:
            # Set HTML content
            await page.set_content(html)

            # Generate PDF bytes
            pdf_bytes = await page.pdf(
                format="A4",
                print_background=True,
                landscape=landscape,
                margin={
                    "top": "20px",
                    "bottom": "20px",
                    "left": "20px",
                    "right": "20px",
                },
            )

            return pdf_bytes

        finally:
            # Always clean up the page
            await page.close()

    async def close(self) -> None:
        """Close browser and playwright instances.

        Releases browser and playwright resources. Safe to call multiple times
        (idempotent). Sets browser and playwright to None after closing.
        """
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
