"""Template rendering utilities for FastAPI routes."""

from decimal import Decimal

from fastapi import Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


def format_hours(value: Decimal | float | int | None) -> str:
    """Format decimal as hours: 8,50 h.

    Args:
        value: Numeric value to format (hours)

    Returns:
        Formatted string with German number format and h suffix

    Examples:
        >>> format_hours(Decimal("8.50"))
        '8,50 h'
        >>> format_hours(Decimal("0.00"))
        '0,00 h'
        >>> format_hours(None)
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


# Register custom Jinja2 filters
templates.env.filters["hours"] = format_hours
templates.env.filters["minutes"] = format_minutes


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
