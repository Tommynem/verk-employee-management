# Phase 2: Data Model Design

## Source of Truth

Based on `zeiterfassung_old.xlsx` analysis from this session.

---

## TimeEntry Model

Core entity for user view - one entry per day per user.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | Integer | PK | Auto-increment |
| user_id | Integer | Yes | Reference to VaWW user (loose coupling, no FK) |
| work_date | Date | Yes | The day this entry is for |
| start_time | Time | No | Arrival time (nullable for vacation/sick) |
| end_time | Time | No | Departure time |
| break_minutes | Integer | No | Total break duration in minutes |
| notes | String | No | Free text (Abwesenheit/Bemerkung from Excel) |
| absence_type | Enum | No | See AbsenceType enum below |
| status | Enum | Yes | DRAFT or SUBMITTED |
| created_at | DateTime | Yes | Auto-set on create |
| updated_at | DateTime | Yes | Auto-set on update |

### Constraints
- Unique constraint on (user_id, work_date) - one entry per day per user
- If start_time set, end_time should also be set (validation rule)
- break_minutes defaults to 0

---

## UserSettings Model

Employee-level configuration.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | Integer | PK | Auto-increment |
| user_id | Integer | Yes | Reference to VaWW user (unique) |
| weekly_target_hours | Decimal(4,2) | Yes | e.g., 32.00 hours |
| carryover_hours | Decimal(6,2) | No | Übertrag from previous period |
| schedule_json | JSON | No | Regular schedule per weekday |
| created_at | DateTime | Yes | Auto-set |
| updated_at | DateTime | Yes | Auto-set |

### schedule_json Format
```json
{
  "monday": {"start": "07:00", "end": "14:00"},
  "tuesday": {"start": "07:00", "end": "17:00"},
  "wednesday": {"start": "07:00", "end": "14:00"},
  "thursday": {"start": "07:00", "end": "14:00"},
  "friday": {"start": "07:00", "end": "11:00"}
}
```

---

## Enums

### AbsenceType
```python
class AbsenceType(str, Enum):
    NONE = "none"           # Regular work day
    VACATION = "vacation"   # Urlaub
    SICK = "sick"           # Krank
    HOLIDAY = "holiday"     # Feiertag (public holiday)
    FLEX_TIME = "flex_time" # Zeitausgleich
```

### RecordStatus
```python
class RecordStatus(str, Enum):
    DRAFT = "draft"         # User can still edit
    SUBMITTED = "submitted" # Locked for HR review (future)
```

---

## Calculated Fields (NOT Stored)

Compute at runtime, do not persist:

```python
def actual_hours(entry: TimeEntry) -> Decimal:
    """Calculate actual hours worked."""
    if entry.start_time is None or entry.end_time is None:
        return Decimal("0.00")

    start = datetime.combine(entry.work_date, entry.start_time)
    end = datetime.combine(entry.work_date, entry.end_time)
    duration = end - start
    hours = Decimal(duration.total_seconds()) / 3600
    break_hours = Decimal(entry.break_minutes or 0) / 60
    return hours - break_hours

def target_hours(entry: TimeEntry, settings: UserSettings) -> Decimal:
    """Calculate target hours for the day."""
    # Weekend = 0 hours
    if entry.work_date.weekday() >= 5:
        return Decimal("0.00")
    # Weekday = weekly_target / 5
    return settings.weekly_target_hours / 5

def balance(entry: TimeEntry, settings: UserSettings) -> Decimal:
    """Calculate +/- balance for the day."""
    actual = actual_hours(entry)
    target = target_hours(entry, settings)

    # Special: vacation/sick/holiday count as target hours worked
    if entry.absence_type in (AbsenceType.VACATION, AbsenceType.SICK, AbsenceType.HOLIDAY):
        actual = target

    return actual - target
```

---

## TDD Order

1. **Write tests first** for:
   - AbsenceType and RecordStatus enums
   - TimeEntry model CRUD
   - UserSettings model CRUD
   - Unique constraint validation
   - Calculated fields (actual_hours, target_hours, balance)

2. **Implement models** to make tests pass

3. **Create migration** after tests pass:
   ```bash
   uv run alembic revision --autogenerate -m "Add TimeEntry and UserSettings"
   uv run alembic upgrade head
   ```

---

## Factory Boy Factories (After Models)

```python
class UserSettingsFactory(factory.Factory):
    class Meta:
        model = UserSettings

    user_id = factory.Sequence(lambda n: n + 1)
    weekly_target_hours = Decimal("32.00")
    carryover_hours = Decimal("0.00")

class TimeEntryFactory(factory.Factory):
    class Meta:
        model = TimeEntry

    user_id = factory.Sequence(lambda n: n + 1)
    work_date = factory.Faker("date_this_month")
    start_time = time(7, 0)
    end_time = time(15, 0)
    break_minutes = 30
    absence_type = AbsenceType.NONE
    status = RecordStatus.DRAFT
```

---

## Excel Column Mapping

| Excel Column | Model Field |
|--------------|-------------|
| Tag (A) | work_date |
| Ankunft (B) | start_time |
| Ende (D) | end_time |
| Pausen (F) | break_minutes |
| Abwesenheit/Bemerkung (O) | notes |
| Urlaub? (R) | absence_type = VACATION if True |
| Name (Row 5) | user_id (linked to VaWW user) |
| Sollstunden pro Woche | weekly_target_hours |
| Übertrag Vormonat | carryover_hours |
