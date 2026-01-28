"""PDF export service for time entries.

This module provides the PDFExportService for exporting time entries
to PDF format with monthly summary data.
"""

import base64
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from source.database.models import TimeEntry, UserSettings
from source.documents.pdf_generator import PDFGenerator
from source.services.data_transfer.dataclasses import ExportResult
from source.services.time_calculation import TimeCalculationService

# German weekday abbreviations (Monday = 0, Sunday = 6)
GERMAN_WEEKDAYS = {
    0: "Mo",
    1: "Di",
    2: "Mi",
    3: "Do",
    4: "Fr",
    5: "Sa",
    6: "So",
}

# German absence labels
ABSENCE_LABELS = {
    "none": "",
    "vacation": "Urlaub",
    "sick": "Krank",
    "holiday": "Feiertag",
    "flex_time": "Gleitzeit",
}

# German month names
GERMAN_MONTHS = {
    1: "Januar",
    2: "Februar",
    3: "März",
    4: "April",
    5: "Mai",
    6: "Juni",
    7: "Juli",
    8: "August",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Dezember",
}


def get_template_env() -> Environment:
    """Create Jinja2 environment for template rendering.

    Returns:
        Configured Jinja2 Environment
    """
    env = Environment(loader=FileSystemLoader("templates"))
    # Add 'now' function for timestamp
    env.globals["now"] = datetime.now
    return env


class PDFExportService:
    """Service for exporting time entries to PDF format."""

    def __init__(self) -> None:
        """Initialize PDF export service."""
        self.calc_service = TimeCalculationService()

    async def export_pdf(
        self,
        entries: list[TimeEntry],
        settings: UserSettings,
        user_id: int,
        year: int,
        month: int,
    ) -> ExportResult:
        """Export time entries for a month as PDF.

        Args:
            entries: List of TimeEntry instances for the month
            settings: UserSettings with weekly_target_hours and carryover_hours
            user_id: User ID for filename
            year: Year of the month
            month: Month number (1-12)

        Returns:
            ExportResult with PDF bytes and metadata
        """
        # Prepare entry data for template
        prepared_entries = []
        for entry in entries:
            weekday = GERMAN_WEEKDAYS[entry.work_date.weekday()]
            actual_hours = self.calc_service.actual_hours(entry)
            target_hours = self.calc_service.target_hours(entry, settings)
            balance = self.calc_service.daily_balance(entry, settings)
            absence_label = ABSENCE_LABELS.get(entry.absence_type.value, "")

            prepared_entries.append(
                {
                    "work_date": entry.work_date,
                    "weekday": weekday,
                    "start_time": entry.start_time,
                    "end_time": entry.end_time,
                    "break_minutes": entry.break_minutes,
                    "actual_hours": actual_hours,
                    "target_hours": target_hours,
                    "balance": balance,
                    "notes": entry.notes,
                    "absence_label": absence_label,
                }
            )

        # Calculate monthly summary
        summary = self.calc_service.monthly_summary(entries, settings, year, month)

        # Get German month name
        month_name = GERMAN_MONTHS[month]

        # Load and embed logo
        logo_path = Path("static/logo.png")
        if logo_path.exists():
            logo_bytes = logo_path.read_bytes()
            logo_base64 = base64.b64encode(logo_bytes).decode("utf-8")
            logo_data_uri = f"data:image/png;base64,{logo_base64}"
        else:
            # Fallback if logo doesn't exist
            logo_data_uri = ""

        # Render template
        env = get_template_env()
        template = env.get_template("pdf/time_entries_monthly.html")
        html = template.render(
            year=year,
            month=month,
            month_name=month_name,
            entries=prepared_entries,
            summary=summary,
            logo_data_uri=logo_data_uri,
        )

        # Generate PDF
        generator = PDFGenerator()
        try:
            pdf_bytes = await generator.generate_pdf_bytes(html, landscape=True)
        finally:
            await generator.close()

        # Create filename
        filename = f"zeiterfassung_{user_id}_{year}-{month:02d}.pdf"

        return ExportResult(
            success=True,
            content=pdf_bytes,
            filename=filename,
            content_type="application/pdf",
        )


__all__ = [
    "PDFExportService",
]
