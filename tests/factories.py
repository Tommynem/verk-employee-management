"""Factory Boy factories for test data generation.

This module provides factories for creating test instances of database models.
Factories use Factory Boy to generate realistic test data with sensible defaults.

Usage:
    # Build in-memory instance (not persisted)
    entry = TimeEntryFactory.build()
    db_session.add(entry)
    db_session.commit()

    # Build with custom values
    entry = TimeEntryFactory.build(user_id=42, work_date=date(2026, 1, 15))
"""

from datetime import date, time
from decimal import Decimal

import factory

from source.database.enums import AbsenceType, RecordStatus
from source.database.models import TimeEntry, UserSettings


class TimeEntryFactory(factory.Factory):
    """Factory for creating TimeEntry test instances.

    Creates regular work day entries by default with standard working hours.
    Use specialized factories (VacationEntryFactory, SickEntryFactory) for absence types.
    """

    class Meta:
        model = TimeEntry

    user_id = factory.Sequence(lambda n: n + 1)
    work_date = factory.LazyFunction(lambda: date.today())
    start_time = time(7, 0)
    end_time = time(15, 0)
    break_minutes = 30
    notes = None
    absence_type = AbsenceType.NONE
    status = RecordStatus.DRAFT


class VacationEntryFactory(TimeEntryFactory):
    """Factory for creating vacation time entries.

    Vacation entries have no start/end times, only the work_date matters.
    """

    absence_type = AbsenceType.VACATION
    start_time = None
    end_time = None
    break_minutes = 0


class SickEntryFactory(TimeEntryFactory):
    """Factory for creating sick day time entries.

    Sick entries have no start/end times, only the work_date matters.
    """

    absence_type = AbsenceType.SICK
    start_time = None
    end_time = None
    break_minutes = 0


class HolidayEntryFactory(TimeEntryFactory):
    """Factory for creating holiday time entries.

    Holiday entries have no start/end times, only the work_date matters.
    """

    absence_type = AbsenceType.HOLIDAY
    start_time = None
    end_time = None
    break_minutes = 0


class UserSettingsFactory(factory.Factory):
    """Factory for creating UserSettings test instances.

    Creates user settings with default 32-hour weekly target (German part-time standard).
    """

    class Meta:
        model = UserSettings

    user_id = factory.Sequence(lambda n: n + 1)
    weekly_target_hours = Decimal("32.00")
    carryover_hours = None
    schedule_json = None


__all__ = [
    "TimeEntryFactory",
    "VacationEntryFactory",
    "SickEntryFactory",
    "HolidayEntryFactory",
    "UserSettingsFactory",
]
