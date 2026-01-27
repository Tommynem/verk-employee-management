# Phase 3: Business Logic

## Overview

Pure Python services for time tracking calculations. No HTTP dependencies - testable in isolation.

---

## TimeCalculationService

Location: `source/services/time_calculation.py`

### Methods

```python
class TimeCalculationService:
    def actual_hours(self, entry: TimeEntry) -> Decimal:
        """Calculate actual hours worked for a single entry."""

    def target_hours(self, entry: TimeEntry, settings: UserSettings) -> Decimal:
        """Calculate target hours for a day based on user settings."""

    def daily_balance(self, entry: TimeEntry, settings: UserSettings) -> Decimal:
        """Calculate +/- balance for a single day."""

    def period_balance(
        self,
        entries: list[TimeEntry],
        settings: UserSettings,
        include_carryover: bool = True
    ) -> Decimal:
        """Calculate cumulative balance for a period (week/month)."""

    def weekly_summary(
        self,
        entries: list[TimeEntry],
        settings: UserSettings,
        week_start: date
    ) -> WeeklySummary:
        """Generate weekly summary with totals."""

    def monthly_summary(
        self,
        entries: list[TimeEntry],
        settings: UserSettings,
        year: int,
        month: int
    ) -> MonthlySummary:
        """Generate monthly summary with totals and carryover."""
```

### Data Classes for Summaries

```python
@dataclass
class DaySummary:
    date: date
    actual_hours: Decimal
    target_hours: Decimal
    balance: Decimal
    absence_type: AbsenceType
    has_entry: bool

@dataclass
class WeeklySummary:
    week_start: date
    week_end: date
    days: list[DaySummary]
    total_actual: Decimal
    total_target: Decimal
    total_balance: Decimal

@dataclass
class MonthlySummary:
    year: int
    month: int
    weeks: list[WeeklySummary]
    total_actual: Decimal
    total_target: Decimal
    period_balance: Decimal
    carryover_in: Decimal
    carryover_out: Decimal
```

---

## Validation Rules

Location: `source/services/validation.py`

### TimeEntry Validation

```python
def validate_time_entry(entry: TimeEntryCreate, existing: list[TimeEntry]) -> list[str]:
    """
    Validate a time entry before save.

    Rules:
    1. If start_time set, end_time must also be set
    2. end_time must be after start_time
    3. break_minutes cannot exceed worked duration
    4. No duplicate entries for same user_id + work_date
    5. work_date cannot be in the future (configurable)
    6. Submitted entries cannot be modified

    Returns list of German error messages.
    """
```

### German Error Messages

```python
VALIDATION_ERRORS = {
    "end_before_start": "Endzeit muss nach Startzeit liegen",
    "break_exceeds_duration": "Pausenzeit überschreitet Arbeitszeit",
    "duplicate_entry": "Für diesen Tag existiert bereits ein Eintrag",
    "future_date": "Datum darf nicht in der Zukunft liegen",
    "submitted_readonly": "Abgeschlossene Einträge können nicht bearbeitet werden",
    "missing_end_time": "Endzeit fehlt",
    "missing_start_time": "Startzeit fehlt",
}
```

---

## TDD Test Cases

### TimeCalculationService Tests

```python
class TestActualHours:
    def test_normal_work_day(self):
        """7:00-15:00 with 30min break = 7.5 hours"""

    def test_no_break(self):
        """7:00-12:00 with no break = 5 hours"""

    def test_empty_entry(self):
        """No start/end time = 0 hours"""

    def test_overnight_shift(self):
        """Handle shifts crossing midnight (future consideration)"""

class TestTargetHours:
    def test_weekday(self):
        """32 hours/week = 6.4 hours/day on weekdays"""

    def test_weekend(self):
        """Saturday/Sunday = 0 target hours"""

    def test_custom_weekly_hours(self):
        """40 hours/week = 8 hours/day"""

class TestDailyBalance:
    def test_positive_balance(self):
        """Worked more than target = positive"""

    def test_negative_balance(self):
        """Worked less than target = negative"""

    def test_vacation_counts_as_target(self):
        """Vacation day balance = 0 (actual = target)"""

    def test_sick_counts_as_target(self):
        """Sick day balance = 0"""

class TestPeriodBalance:
    def test_weekly_cumulative(self):
        """Sum of daily balances for a week"""

    def test_with_carryover(self):
        """Include carryover from previous period"""

    def test_without_carryover(self):
        """Exclude carryover for current period only"""
```

### Validation Tests

```python
class TestTimeEntryValidation:
    def test_valid_entry(self):
        """Normal entry passes validation"""

    def test_end_before_start_fails(self):
        """End time before start time rejected"""

    def test_break_exceeds_duration_fails(self):
        """Break longer than work period rejected"""

    def test_duplicate_date_fails(self):
        """Two entries same user same date rejected"""

    def test_submitted_entry_readonly(self):
        """Cannot modify submitted entries"""
```

---

## Implementation Order

1. Write tests for `TimeCalculationService.actual_hours`
2. Implement to pass tests
3. Write tests for `target_hours`
4. Implement
5. Write tests for `daily_balance`
6. Implement
7. Write tests for validation rules
8. Implement validation
9. Write tests for period summaries
10. Implement summaries

Each step follows RED-GREEN-REFACTOR.
