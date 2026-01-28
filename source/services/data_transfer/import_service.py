"""Import service for time entry data.

This module orchestrates importing time entries from various formats.
"""

from datetime import date, datetime, time

from sqlalchemy.orm import Session

from source.database.enums import AbsenceType
from source.database.models import TimeEntry
from source.services.data_transfer.base import FormatHandler
from source.services.data_transfer.csv_format import CSVFormatHandler
from source.services.data_transfer.dataclasses import ImportResult, TimeEntryRow, ValidationError


class ImportService:
    """Service for importing time entries from files."""

    # German to internal absence type mapping
    GERMAN_ABSENCE_MAP = {
        "Keine": "none",
        "Urlaub": "vacation",
        "Krank": "sick",
        "Feiertag": "holiday",
        "Gleitzeit": "flex_time",
    }

    def __init__(self, handler: FormatHandler | None = None):
        """Initialize with a format handler.

        Args:
            handler: Format handler to use. Defaults to CSVFormatHandler.
        """
        self._handler = handler or CSVFormatHandler()

    @property
    def handler(self) -> FormatHandler:
        """Get the format handler.

        Returns:
            The format handler instance.
        """
        return self._handler

    def import_file(
        self,
        content: bytes,
        user_id: int,
        db: Session,
        dry_run: bool = False,
        skip_duplicates: bool = False,
    ) -> ImportResult:
        """Import time entries from file content.

        Pipeline: validate_structure → parse rows → validate business rules
                  → check duplicates → persist (unless dry_run)

        Args:
            content: Raw file bytes
            user_id: User ID for the entries
            db: Database session
            dry_run: If True, validate only (don't persist)
            skip_duplicates: If True, skip entries for dates that exist

        Returns:
            ImportResult with success, counts, errors, entries
        """
        errors: list[ValidationError] = []
        entries: list[TimeEntry] = []
        skipped_count = 0
        seen_dates: set[date] = set()

        # Step 1: Structure validation
        structure_errors = self._handler.validate_structure(content)
        if structure_errors:
            return ImportResult(success=False, errors=structure_errors)

        # Get existing dates for this user
        existing_dates = self._get_existing_dates(db, user_id)

        # Step 2-3: Parse and validate each row
        for row_num, row_dict in self._handler.deserialize(content):
            # Parse row into TimeEntryRow
            row, parse_errors = self._parse_row(row_num, row_dict)
            if parse_errors:
                errors.extend(parse_errors)
                continue

            # Validate business rules
            rule_errors = self._validate_business_rules(row_num, row)
            if rule_errors:
                errors.extend(rule_errors)
                continue

            # Check intra-file duplicates
            if row.work_date in seen_dates:
                errors.append(
                    ValidationError(
                        row_number=row_num,
                        field="work_date",
                        message="Datum kommt mehrfach in der Datei vor",
                        code="duplicate_date_in_file",
                    )
                )
                continue
            seen_dates.add(row.work_date)

            # Check DB duplicates
            if row.work_date in existing_dates:
                if skip_duplicates:
                    skipped_count += 1
                    continue
                else:
                    errors.append(
                        ValidationError(
                            row_number=row_num,
                            field="work_date",
                            message="Für diesen Tag existiert bereits ein Eintrag",
                            code="duplicate_date",
                        )
                    )
                    continue

            # Create TimeEntry (not yet persisted)
            entry = self._create_entry(row, user_id)
            entries.append(entry)

        # All-or-nothing: if any errors, don't persist
        if errors:
            return ImportResult(success=False, errors=errors)

        # Step 4: Persist if not dry_run
        if not dry_run:
            for entry in entries:
                db.add(entry)
            db.commit()
            # Refresh to get IDs
            for entry in entries:
                db.refresh(entry)

        return ImportResult(
            success=True,
            imported_count=len(entries),
            skipped_count=skipped_count,
            entries=entries,
        )

    def _get_existing_dates(self, db: Session, user_id: int) -> set[date]:
        """Get existing work dates for user.

        Args:
            db: Database session
            user_id: User ID to query

        Returns:
            Set of existing work dates for the user
        """
        results = db.query(TimeEntry.work_date).filter(TimeEntry.user_id == user_id).all()
        return {r[0] for r in results}

    def _parse_row(self, row_num: int, row_dict: dict) -> tuple[TimeEntryRow | None, list[ValidationError]]:
        """Parse row dictionary into TimeEntryRow.

        Args:
            row_num: Row number in source file
            row_dict: Dictionary of field values

        Returns:
            Tuple of (TimeEntryRow or None, list of ValidationErrors)
        """
        errors = []

        # Parse date
        work_date = None
        date_str = row_dict.get("work_date", "")
        if date_str:
            try:
                work_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                errors.append(
                    ValidationError(
                        row_number=row_num,
                        field="work_date",
                        message="Ungültiges Datumsformat",
                        code="invalid_date",
                    )
                )
        else:
            errors.append(
                ValidationError(
                    row_number=row_num,
                    field="work_date",
                    message="Ungültiges Datumsformat",
                    code="invalid_date",
                )
            )

        # Parse times
        start_time = self._parse_time(row_dict.get("start_time", ""))
        end_time = self._parse_time(row_dict.get("end_time", ""))

        # Check for invalid time format
        start_str = row_dict.get("start_time", "")
        end_str = row_dict.get("end_time", "")
        if start_str and start_time is None:
            errors.append(
                ValidationError(
                    row_number=row_num,
                    field="start_time",
                    message="Ungültiges Zeitformat",
                    code="invalid_time",
                )
            )
        if end_str and end_time is None:
            errors.append(
                ValidationError(
                    row_number=row_num,
                    field="end_time",
                    message="Ungültiges Zeitformat",
                    code="invalid_time",
                )
            )

        # Parse break_minutes
        break_minutes = 0
        break_str = row_dict.get("break_minutes", "0")
        try:
            break_minutes = int(break_str) if break_str else 0
        except ValueError:
            errors.append(
                ValidationError(
                    row_number=row_num,
                    field="break_minutes",
                    message="Pausenzeit muss eine Zahl sein",
                    code="invalid_break_minutes",
                )
            )

        # Parse absence type
        absence_type = "none"
        absence_str = row_dict.get("absence_type", "Keine")
        if absence_str in self.GERMAN_ABSENCE_MAP:
            absence_type = self.GERMAN_ABSENCE_MAP[absence_str]
        elif absence_str and absence_str not in self.GERMAN_ABSENCE_MAP:
            errors.append(
                ValidationError(
                    row_number=row_num,
                    field="absence_type",
                    message="Ungültiger Abwesenheitstyp",
                    code="invalid_absence_type",
                )
            )

        # Notes
        notes = row_dict.get("notes", "") or None

        if errors:
            return None, errors

        return (
            TimeEntryRow(
                work_date=work_date,
                start_time=start_time,
                end_time=end_time,
                break_minutes=break_minutes,
                absence_type=absence_type,
                notes=notes,
            ),
            [],
        )

    def _parse_time(self, time_str: str) -> time | None:
        """Parse time string to time object.

        Args:
            time_str: Time string in HH:MM format

        Returns:
            time object or None if empty/invalid
        """
        if not time_str:
            return None
        try:
            return datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            return None

    def _validate_business_rules(self, row_num: int, row: TimeEntryRow) -> list[ValidationError]:
        """Validate business rules for a row.

        Args:
            row_num: Row number in source file
            row: Parsed TimeEntryRow

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check missing time pairs
        if row.start_time and not row.end_time:
            errors.append(
                ValidationError(
                    row_number=row_num,
                    field="end_time",
                    message="Endzeit fehlt",
                    code="missing_end_time",
                )
            )
        if row.end_time and not row.start_time:
            errors.append(
                ValidationError(
                    row_number=row_num,
                    field="start_time",
                    message="Startzeit fehlt",
                    code="missing_start_time",
                )
            )

        # Check end after start
        if row.start_time and row.end_time:
            if row.end_time <= row.start_time:
                errors.append(
                    ValidationError(
                        row_number=row_num,
                        field="end_time",
                        message="Endzeit muss nach Startzeit liegen",
                        code="end_before_start",
                    )
                )
            else:
                # Check break doesn't exceed duration
                start_dt = datetime.combine(date.today(), row.start_time)
                end_dt = datetime.combine(date.today(), row.end_time)
                duration_minutes = (end_dt - start_dt).total_seconds() / 60
                if row.break_minutes > duration_minutes:
                    errors.append(
                        ValidationError(
                            row_number=row_num,
                            field="break_minutes",
                            message="Pausenzeit überschreitet Arbeitszeit",
                            code="break_exceeds_duration",
                        )
                    )

        return errors

    def _create_entry(self, row: TimeEntryRow, user_id: int) -> TimeEntry:
        """Create TimeEntry from row.

        Args:
            row: Parsed TimeEntryRow
            user_id: User ID for the entry

        Returns:
            TimeEntry instance (not yet persisted)
        """
        return TimeEntry(
            user_id=user_id,
            work_date=row.work_date,
            start_time=row.start_time,
            end_time=row.end_time,
            break_minutes=row.break_minutes,
            absence_type=AbsenceType(row.absence_type),
            notes=row.notes,
        )


__all__ = [
    "ImportService",
]
