"""Template rendering utilities for FastAPI routes."""

from decimal import Decimal

from fastapi import Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


def format_hours_decimal(value: Decimal | float | int | None) -> str:
    """Format decimal as hours: 8,50 h.

    Args:
        value: Numeric value to format (hours)

    Returns:
        Formatted string with German number format and h suffix

    Examples:
        >>> format_hours_decimal(Decimal("8.50"))
        '8,50 h'
        >>> format_hours_decimal(Decimal("0.00"))
        '0,00 h'
        >>> format_hours_decimal(None)
        '-'
    """
    if value is None:
        return "-"
    decimal_value = Decimal(str(value))
    # Format with comma as decimal separator
    formatted = f"{decimal_value:.2f}".replace(".", ",")
    return f"{formatted} h"


def format_minutes(value: int | None) -> str:
    """Format minutes as time string: 30 min.

    Args:
        value: Minutes to format

    Returns:
        Formatted string with min suffix

    Examples:
        >>> format_minutes(30)
        '30 min'
        >>> format_minutes(0)
        '0 min'
        >>> format_minutes(None)
        '-'
    """
    if value is None:
        return "-"
    return f"{value} min"


def format_hours(value: Decimal | None) -> str:
    """Format Decimal hours as HHH:MMh format.

    Args:
        value: Decimal hours to format

    Returns:
        Formatted string in HHH:MMh format

    Examples:
        >>> format_hours(Decimal("149.6333"))
        '149:38h'
        >>> format_hours(Decimal("8.5"))
        '8:30h'
        >>> format_hours(None)
        '-'
    """
    if value is None:
        return "-"

    # Handle negative values
    is_negative = value < 0
    abs_value = abs(value)

    # Extract hours and minutes
    hours = int(abs_value)
    minutes = round((abs_value - hours) * 60)

    # Format with sign if negative
    if is_negative:
        return f"-{hours}:{minutes:02d}h"
    return f"{hours}:{minutes:02d}h"


def format_duration(value: int | None) -> str:
    """Format integer minutes as H:MMh format.

    Args:
        value: Integer minutes to format

    Returns:
        Formatted string in H:MMh format

    Examples:
        >>> format_duration(30)
        '0:30h'
        >>> format_duration(90)
        '1:30h'
        >>> format_duration(None)
        '-'
    """
    if value is None:
        return "-"

    # Handle negative values
    is_negative = value < 0
    abs_value = abs(value)

    # Extract hours and minutes
    hours = abs_value // 60
    minutes = abs_value % 60

    # Format with sign if negative
    if is_negative:
        return f"-{hours}:{minutes:02d}h"
    return f"{hours}:{minutes:02d}h"


def format_balance(value: Decimal | None) -> str:
    """Format Decimal hours as signed +H:MM or -H:MM format.

    Args:
        value: Decimal hours to format

    Returns:
        Formatted string with + or - prefix, no 'h' suffix

    Examples:
        >>> format_balance(Decimal("1.5"))
        '+1:30'
        >>> format_balance(Decimal("-0.75"))
        '-0:45'
        >>> format_balance(Decimal("0"))
        '+0:00'
        >>> format_balance(None)
        '-'
    """
    if value is None:
        return "-"

    # Determine sign (zero is positive)
    is_negative = value < 0
    abs_value = abs(value)

    # Extract hours and minutes
    hours = int(abs_value)
    minutes = round((abs_value - hours) * 60)

    # Format with appropriate sign
    sign = "-" if is_negative else "+"
    return f"{sign}{hours}:{minutes:02d}"


# Register custom Jinja2 filters
templates.env.filters["hours"] = format_hours_decimal  # Original filter name for backward compatibility
templates.env.filters["minutes"] = format_minutes
templates.env.filters["format_hours"] = format_hours
templates.env.filters["format_duration"] = format_duration
templates.env.filters["format_balance"] = format_balance


def render_template(request: Request, template_name: str, **context) -> str:
    """Render a Jinja2 template with the given context.

    Args:
        request: FastAPI request object
        template_name: Path to template file relative to templates directory
        **context: Template context variables

    Returns:
        Rendered HTML string

    Example:
        html = render_template(request, "partials/_detail_time_entry.html", time_entry=entry)
    """
    response_body = templates.TemplateResponse(name=template_name, context={"request": request, **context}).body
    # TemplateResponse.body returns bytes, decode to string
    if isinstance(response_body, bytes):
        return response_body.decode()
    return str(response_body)
