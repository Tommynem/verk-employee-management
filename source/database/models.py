"""SQLAlchemy models for Verk Employee Management.

This module contains the core data models.
"""

from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import Column, Date, DateTime, Enum, Integer, Numeric, String, Time, UniqueConstraint
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.sql import func

from source.database import Base
from source.database.enums import AbsenceType, RecordStatus


class TimeEntry(Base):
    """Time tracking entry for an employee's work day.

    Each entry represents one day of work for a specific user.
    Can represent regular work time or various absence types.
    """

    __tablename__ = "time_entries"
    __table_args__ = (UniqueConstraint("user_id", "work_date", name="uq_user_date"),)

    # Primary key
    id: int = Column(Integer, primary_key=True, autoincrement=True)

    # Required fields
    user_id: int = Column(Integer, nullable=False, index=True)
    work_date: date = Column(Date, nullable=False)

    # Optional time fields (nullable for vacation/sick days)
    start_time: time | None = Column(Time, nullable=True)
    end_time: time | None = Column(Time, nullable=True)

    # Break and notes
    break_minutes: int = Column(Integer, default=0, nullable=False)
    notes: str | None = Column(String, nullable=True)

    # Status and type enums (use native_enum=False for SQLite compatibility)
    absence_type: AbsenceType = Column(Enum(AbsenceType, native_enum=False), default=AbsenceType.NONE, nullable=False)
    status: RecordStatus = Column(Enum(RecordStatus, native_enum=False), default=RecordStatus.DRAFT, nullable=False)

    # Timestamps
    created_at: datetime = Column(DateTime, default=func.now(), nullable=False)
    updated_at: datetime = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        """Return string representation of TimeEntry."""
        return (
            f"<TimeEntry(id={self.id}, user_id={self.user_id}, "
            f"work_date={self.work_date}, status={self.status.value})>"
        )


class UserSettings(Base):
    """User-specific settings for time tracking.

    Stores weekly target hours and custom schedules.
    One settings record per user.
    """

    __tablename__ = "user_settings"

    # Primary key
    id: int = Column(Integer, primary_key=True, autoincrement=True)

    # Required fields
    user_id: int = Column(Integer, nullable=False, unique=True, index=True)
    weekly_target_hours: Decimal = Column(Numeric(4, 2), nullable=False)

    # Optional fields
    schedule_json: dict | None = Column(JSON, nullable=True)

    # Tracking configuration
    tracking_start_date: date | None = Column(Date, nullable=True)
    initial_hours_offset: Decimal | None = Column(Numeric(6, 2), nullable=True)

    # Vacation tracking
    initial_vacation_days: Decimal | None = Column(Numeric(5, 2), nullable=True)
    annual_vacation_days: Decimal | None = Column(Numeric(5, 2), nullable=True)
    vacation_carryover_days: Decimal | None = Column(Numeric(5, 2), nullable=True)
    vacation_carryover_expires: date | None = Column(Date, nullable=True)

    # Timestamps
    created_at: datetime = Column(DateTime, default=func.now(), nullable=False)
    updated_at: datetime = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        """Return string representation of UserSettings."""
        return (
            f"<UserSettings(id={self.id}, user_id={self.user_id}, " f"weekly_target_hours={self.weekly_target_hours})>"
        )


__all__ = [
    "Base",
    "TimeEntry",
    "UserSettings",
]
