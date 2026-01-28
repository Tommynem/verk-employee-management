"""German public holiday detection service.

This module provides functionality to detect German public holidays including
movable holidays that depend on the Easter date calculation.

The Easter calculation uses the Meeus/Jones/Butcher algorithm which is valid
for years 1583-4099 in the Gregorian calendar.
"""

from datetime import date, timedelta


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


def get_german_holidays(year: int) -> dict[date, str]:
    """Get all German nationwide public holidays for a given year.

    Returns a dictionary mapping holiday dates to their German names.
    Includes both fixed holidays and movable holidays based on Easter.

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

    Args:
        year: Year to get holidays for

    Returns:
        Dictionary mapping holiday dates to their German names
    """
    holidays = {}

    # Fixed holidays
    holidays[date(year, 1, 1)] = "Neujahr"
    holidays[date(year, 5, 1)] = "Tag der Arbeit"
    holidays[date(year, 10, 3)] = "Tag der Deutschen Einheit"
    holidays[date(year, 12, 25)] = "1. Weihnachtstag"
    holidays[date(year, 12, 26)] = "2. Weihnachtstag"

    # Movable holidays based on Easter
    easter = calculate_easter(year)
    holidays[easter - timedelta(days=2)] = "Karfreitag"  # Good Friday
    holidays[easter + timedelta(days=1)] = "Ostermontag"  # Easter Monday
    holidays[easter + timedelta(days=39)] = "Christi Himmelfahrt"  # Ascension Day
    holidays[easter + timedelta(days=50)] = "Pfingstmontag"  # Whit Monday

    return holidays


def is_holiday(check_date: date, return_name: bool = False) -> bool | tuple[bool, str | None]:
    """Check if a given date is a German public holiday.

    Args:
        check_date: Date to check
        return_name: If True, return tuple (is_holiday, holiday_name)

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
    """
    holidays = get_german_holidays(check_date.year)
    holiday_name = holidays.get(check_date)

    if return_name:
        return (holiday_name is not None, holiday_name)
    return holiday_name is not None
