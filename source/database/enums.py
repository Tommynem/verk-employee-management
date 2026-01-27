"""Database enums for time tracking."""

import enum


class AbsenceType(str, enum.Enum):
    """Type of absence for a time entry.

    Inherits from str for JSON serialization compatibility and database storage.
    """

    NONE = "none"  # Regular work day
    VACATION = "vacation"  # Urlaub
    SICK = "sick"  # Krank
    HOLIDAY = "holiday"  # Feiertag
    FLEX_TIME = "flex_time"  # Zeitausgleich


class RecordStatus(str, enum.Enum):
    """Status of a time entry record.

    Inherits from str for JSON serialization compatibility and database storage.
    """

    DRAFT = "draft"  # User can edit
    SUBMITTED = "submitted"  # Locked for HR
