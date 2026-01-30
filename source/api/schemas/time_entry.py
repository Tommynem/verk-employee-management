"""Pydantic schemas for TimeEntry following VaWW pattern.

Schema Pattern (VaWW convention):
- TimeEntryUpdate: Base with all mutable fields (all optional)
- TimeEntryCreate: Inherits from Update, adds required fields
- TimeEntryResponse: Inherits from Update, adds read-only database fields
"""

from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from source.database.calculations import actual_hours as calc_actual_hours
from source.database.enums import AbsenceType, RecordStatus


class TimeEntryUpdate(BaseModel):
    """Base schema with all mutable fields (all optional for updates).

    Includes updated_at for optimistic locking to prevent race conditions.
    """

    start_time: time | None = None
    end_time: time | None = None
    break_minutes: int | None = Field(None, ge=0, le=480)
    notes: str | None = Field(None, max_length=500)
    absence_type: AbsenceType = AbsenceType.NONE
    updated_at: datetime | None = Field(None, description="Timestamp for optimistic locking")


class TimeEntryCreate(TimeEntryUpdate):
    """Schema for creating new time entries.

    Inherits all fields from TimeEntryUpdate, adds required work_date.
    """

    work_date: date


class TimeEntryResponse(TimeEntryUpdate):
    """Schema for time entry responses.

    Adds read-only database fields and calculated fields.
    Includes actual_hours, target_hours, and balance computed from ORM model.

    Note: actual_hours is computed from start_time, end_time, and break_minutes.
    target_hours and balance require UserSettings and should be set at service layer.
    """

    # Database-generated fields
    id: int
    user_id: int
    work_date: date
    status: RecordStatus
    created_at: datetime
    updated_at: datetime

    # Calculated fields (populated by model_validator)
    actual_hours: Decimal = Field(default=Decimal("0.00"))
    target_hours: Decimal = Field(default=Decimal("0.00"))
    balance: Decimal = Field(default=Decimal("0.00"))

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def compute_calculated_fields(cls, data):
        """Compute calculated fields from ORM TimeEntry model.

        This validator runs before field validation and has access to the source object
        when using model_validate() with from_attributes=True.

        Computes:
        - actual_hours: from start_time, end_time, break_minutes
        - target_hours: defaults to 0.00 (requires UserSettings, set at service layer)
        - balance: defaults to 0.00 (requires UserSettings, set at service layer)
        """
        # If data is already a dict with calculated fields, use them
        if isinstance(data, dict):
            return data

        # If data is an ORM model (has attributes), compute actual_hours
        if hasattr(data, "start_time") and hasattr(data, "end_time"):
            # Import here to avoid circular dependencies
            from source.database.models import TimeEntry

            # Check if this is a TimeEntry ORM model
            if isinstance(data, TimeEntry):
                # Compute actual_hours using calculation function
                calculated_actual_hours = calc_actual_hours(data)

                # Return a dict with all fields plus calculated ones
                return {
                    "id": data.id,
                    "user_id": data.user_id,
                    "work_date": data.work_date,
                    "start_time": data.start_time,
                    "end_time": data.end_time,
                    "break_minutes": data.break_minutes,
                    "notes": data.notes,
                    "absence_type": data.absence_type,
                    "status": data.status,
                    "created_at": data.created_at,
                    "updated_at": data.updated_at,
                    "actual_hours": calculated_actual_hours,
                    "target_hours": Decimal("0.00"),  # Set at service layer
                    "balance": Decimal("0.00"),  # Set at service layer
                }

        return data


__all__ = [
    "TimeEntryUpdate",
    "TimeEntryCreate",
    "TimeEntryResponse",
]
