"""German public holiday detection service.

This module provides functionality to detect German public holidays, including
Bundesland-specific holidays via the ``holidays`` package.

The Easter calculation uses the Meeus/Jones/Butcher algorithm which is valid
for years 1583-4099 in the Gregorian calendar.
"""

from collections.abc import Mapping
from datetime import date
from typing import Literal, overload

import holidays as holidays_package

HOLIDAY_LANGUAGE = "de"
LEGACY_HOLIDAY_NAMES = {
    "Erster Mai": "Tag der Arbeit",
    "Erster Weihnachtstag": "1. Weihnachtstag",
    "Zweiter Weihnachtstag": "2. Weihnachtstag",
}
STATE_CODE_ALIASES = {
    "DE-NW": "NW",
    "NRW": "NW",
}
STATE_SETTING_KEYS = (
    "holiday_state_code",
    "holiday_state",
    "federal_state_code",
    "federal_state",
    "bundesland_code",
    "bundesland",
    "state_code",
    "state",
)
DEFAULT_COMPANY_CLOSURES = {
    "12-24": {
        "day": 24,
        "month": 12,
        "name": "Heiligabend",
        "recurring": True,
        "enabled": True,
        "counts_as_vacation": False,
    },
    "12-31": {
        "day": 31,
        "month": 12,
        "name": "Silvester",
        "recurring": True,
        "enabled": True,
        "counts_as_vacation": False,
    },
}


def calculate_easter(year: int) -> date:
    """Calculate Easter Sunday date for a given year.

    Uses the Meeus/Jones/Butcher algorithm for computing the date of Easter
    Sunday in the Gregorian calendar.

    Args:
        year: Year to calculate Easter for (valid for 1583-4099)

    Returns:
        Date of Easter Sunday for the given year

    References:
        - Meeus, Jean: "Astronomical Algorithms" (1991)
        - https://en.wikipedia.org/wiki/Date_of_Easter#Anonymous_Gregorian_algorithm
    """
    # Meeus/Jones/Butcher algorithm
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    ell = (32 + 2 * e + 2 * i - h - k) % 7  # Using 'ell' instead of 'l' for clarity
    m = (a + 11 * h + 22 * ell) // 451
    month = (h + ell - 7 * m + 114) // 31
    day = ((h + ell - 7 * m + 114) % 31) + 1

    return date(year, month, day)


def _normalize_state_code(state_code: object | None) -> str | None:
    """Normalize German subdivision codes for the holidays package."""
    if state_code is None:
        return None

    normalized = str(state_code).strip().upper()
    if not normalized:
        return None

    return STATE_CODE_ALIASES.get(normalized, normalized.removeprefix("DE-"))


def _normalize_holiday_name(holiday_name: str) -> str:
    """Keep historical names returned by this module stable."""
    return LEGACY_HOLIDAY_NAMES.get(holiday_name, holiday_name)


def _get_setting_value(settings: object, keys: tuple[str, ...]) -> object | None:
    """Read the first matching value from an object or mapping."""
    if isinstance(settings, Mapping):
        for key in keys:
            if key in settings:
                return settings[key]
        return None

    for key in keys:
        if hasattr(settings, key):
            return getattr(settings, key)

    return None


def _as_bool(value: object | None, default: bool = False) -> bool:
    """Coerce form/JSON-ish truthy values."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "on", "yes"}


def _as_int(value: object | None) -> int | None:
    """Coerce JSON day/month values to int."""
    if value is None:
        return None
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _as_date(value: object | None) -> date | None:
    """Coerce optional ISO date values."""
    if isinstance(value, date):
        return value
    if value is None:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _closure_key(closure: Mapping[str, object]) -> str | None:
    """Build a stable closure key from a closure mapping."""
    month = _as_int(closure.get("month"))
    day = _as_int(closure.get("day"))
    if month is not None and day is not None:
        return f"{month:02d}-{day:02d}"

    closure_date = _as_date(closure.get("date"))
    if closure_date is not None:
        return closure_date.isoformat()

    return None


def _closure_consumes_vacation(closure: Mapping[str, object]) -> bool:
    """Read either supported vacation-consumption flag."""
    if "counts_as_vacation" in closure:
        return _as_bool(closure.get("counts_as_vacation"), default=False)
    return _as_bool(closure.get("consumes_vacation"), default=False)


def _configured_company_closures(settings: object | None) -> object | None:
    """Read configured company closures from settings-like data."""
    if settings is None:
        return None
    schedule_json = _get_setting_value(settings, ("schedule_json",))
    if not isinstance(schedule_json, Mapping):
        return None
    return schedule_json.get("company_closures")


def get_company_closures_for_settings(settings: object | None) -> dict[str, dict[str, object]]:
    """Return company closures overlaid with default recurring closures.

    ``settings=None`` returns no company closures to preserve legacy behavior
    for callers that do not have a settings row. A settings object with no
    explicit closure config receives the default 24.12 and 31.12 closures.
    Both the keyed dict written by the settings UI and a list-style imported
    shape are accepted.
    """
    if settings is None:
        return {}

    closures = {key: value.copy() for key, value in DEFAULT_COMPANY_CLOSURES.items()}
    configured = _configured_company_closures(settings)
    if not configured:
        return closures

    if isinstance(configured, Mapping):
        configured_items = configured.items()
    elif isinstance(configured, list):
        configured_items = []
        for closure in configured:
            if isinstance(closure, Mapping):
                key = _closure_key(closure)
                if key is not None:
                    configured_items.append((key, closure))
    else:
        return closures

    for key, configured_value in configured_items:
        if not isinstance(configured_value, Mapping):
            continue
        normalized_key = str(key)
        merged = closures.get(normalized_key, {}).copy()
        merged.update(dict(configured_value))
        closures[normalized_key] = merged

    return closures


def get_holiday_state_code(settings: object | None) -> str | None:
    """Extract a German state code from settings-like data.

    The current settings model has no dedicated Bundesland column, so this
    helper accepts common future-proof shapes, for example:

    >>> get_holiday_state_code({"holiday_state_code": "NW"})
    'NW'
    >>> get_holiday_state_code({"bundesland": "DE-NW"})
    'NW'

    It also checks ``settings.schedule_json`` and nested ``holidays`` or
    ``holiday_settings`` mappings. Missing values return ``None``, which keeps
    holiday detection nationwide-only.
    """
    if settings is None:
        return None

    if isinstance(settings, str):
        return _normalize_state_code(settings)

    direct_value = _get_setting_value(settings, STATE_SETTING_KEYS)
    if direct_value is not None:
        return _normalize_state_code(direct_value)

    schedule_json = _get_setting_value(settings, ("schedule_json",))
    if not isinstance(schedule_json, Mapping):
        return None

    schedule_value = _get_setting_value(schedule_json, STATE_SETTING_KEYS)
    if schedule_value is not None:
        return _normalize_state_code(schedule_value)

    for nested_key in ("holidays", "holiday_settings"):
        nested_settings = schedule_json.get(nested_key)
        if isinstance(nested_settings, Mapping):
            nested_value = _get_setting_value(nested_settings, STATE_SETTING_KEYS)
            if nested_value is not None:
                return _normalize_state_code(nested_value)

    return None


def get_german_holidays(year: int, state_code: str | None = None) -> dict[date, str]:
    """Get German public holidays for a given year.

    Returns a dictionary mapping holiday dates to their German names.
    By default, only nationwide holidays are returned. Pass an ISO 3166-2
    German subdivision code such as ``"NW"`` to include state-specific
    holidays for that Bundesland.

    German nationwide holidays:
    - Neujahr (New Year's Day) - January 1
    - Karfreitag (Good Friday) - 2 days before Easter
    - Ostermontag (Easter Monday) - 1 day after Easter
    - Tag der Arbeit (Labour Day) - May 1
    - Christi Himmelfahrt (Ascension Day) - 39 days after Easter
    - Pfingstmontag (Whit Monday) - 50 days after Easter
    - Tag der Deutschen Einheit (German Unity Day) - October 3
    - 1. Weihnachtstag (Christmas Day) - December 25
    - 2. Weihnachtstag (Boxing Day) - December 26

    Example NRW-specific holidays:
    - Fronleichnam (Corpus Christi) - state-specific in ``NW``
    - Allerheiligen (All Saints' Day) - state-specific in ``NW``

    Args:
        year: Year to get holidays for
        state_code: Optional German state code such as ``"NW"``. ``None``
            preserves nationwide-only behavior.

    Returns:
        Dictionary mapping holiday dates to their German names
    """
    normalized_state_code = _normalize_state_code(state_code)

    try:
        german_holidays = holidays_package.country_holidays(
            "DE",
            years=year,
            subdiv=normalized_state_code,
            language=HOLIDAY_LANGUAGE,
        )
    except NotImplementedError as exc:
        raise ValueError(f"Unsupported German state code {state_code!r}. Use subdivision codes such as 'NW'.") from exc

    return {
        holiday_date: _normalize_holiday_name(holiday_name) for holiday_date, holiday_name in german_holidays.items()
    }


def get_german_holidays_for_settings(year: int, settings: object | None) -> dict[date, str]:
    """Get German holidays using a settings-derived state code.

    If the settings do not contain a Bundesland value, this falls back to the
    nationwide-only holiday set.
    """
    return get_german_holidays(year, state_code=get_holiday_state_code(settings))


@overload
def is_holiday(check_date: date, return_name: Literal[False] = False, *, state_code: str | None = None) -> bool: ...


@overload
def is_holiday(
    check_date: date, return_name: Literal[True], *, state_code: str | None = None
) -> tuple[bool, str | None]: ...


def is_holiday(
    check_date: date,
    return_name: bool = False,
    *,
    state_code: str | None = None,
) -> bool | tuple[bool, str | None]:
    """Check if a given date is a German public holiday.

    Args:
        check_date: Date to check
        return_name: If True, return tuple (is_holiday, holiday_name)
        state_code: Optional German state code such as ``"NW"``. ``None``
            preserves nationwide-only behavior.

    Returns:
        If return_name is False: Boolean indicating if date is a holiday
        If return_name is True: Tuple (is_holiday, holiday_name or None)

    Examples:
        >>> is_holiday(date(2026, 1, 1))
        True
        >>> is_holiday(date(2026, 1, 1), return_name=True)
        (True, 'Neujahr')
        >>> is_holiday(date(2026, 1, 15))
        False
        >>> is_holiday(date(2026, 1, 15), return_name=True)
        (False, None)
        >>> is_holiday(date(2026, 6, 4), state_code="NW", return_name=True)
        (True, 'Fronleichnam')
    """
    holidays = get_german_holidays(check_date.year, state_code=state_code)
    holiday_name = holidays.get(check_date)

    if return_name:
        return (holiday_name is not None, holiday_name)
    return holiday_name is not None


@overload
def is_holiday_for_settings(
    check_date: date,
    settings: object | None,
    return_name: Literal[False] = False,
) -> bool: ...


@overload
def is_holiday_for_settings(
    check_date: date,
    settings: object | None,
    return_name: Literal[True],
) -> tuple[bool, str | None]: ...


def is_holiday_for_settings(
    check_date: date,
    settings: object | None,
    return_name: bool = False,
) -> bool | tuple[bool, str | None]:
    """Check a holiday using a settings-derived state code."""
    return is_holiday(
        check_date,
        return_name=return_name,
        state_code=get_holiday_state_code(settings),
    )


@overload
def is_non_vacation_consuming_closure_for_settings(
    check_date: date,
    settings: object | None,
    return_name: Literal[False] = False,
) -> bool: ...


@overload
def is_non_vacation_consuming_closure_for_settings(
    check_date: date,
    settings: object | None,
    return_name: Literal[True],
) -> tuple[bool, str | None]: ...


def is_non_vacation_consuming_closure_for_settings(
    check_date: date,
    settings: object | None,
    return_name: bool = False,
) -> bool | tuple[bool, str | None]:
    """Check enabled company closures that do not consume vacation days."""
    for closure in get_company_closures_for_settings(settings).values():
        if not _as_bool(closure.get("enabled"), default=True):
            continue
        if _closure_consumes_vacation(closure):
            continue

        closure_date = _as_date(closure.get("date"))
        recurring = _as_bool(closure.get("recurring"), default=True)
        month = _as_int(closure.get("month"))
        day = _as_int(closure.get("day"))

        matches_once = closure_date == check_date
        matches_recurring = recurring and month == check_date.month and day == check_date.day
        if matches_once or matches_recurring:
            name = str(closure.get("name") or "Betriebsschliessung")
            return (True, name) if return_name else True

    return (False, None) if return_name else False
