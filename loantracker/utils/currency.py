"""Currency formatting and parsing utilities."""

from __future__ import annotations


def format_currency(value: float | None) -> str:
    """Format a float value as a currency string with commas and 2 decimal places.

    Args:
        value: The numeric value to format.

    Returns:
        Formatted string like "1,234.56" or empty string if value is None/0.
    """
    if value is None or value == 0:
        return ""
    return f"{value:,.2f}"


def parse_currency(value: str | float | None) -> float:
    """Parse a currency string to float.

    Simply parses the numeric value - user types what they mean.
    Examples:
    - "100.50" -> 100.50
    - "1,234.56" -> 1234.56
    - "$1,234.56" -> 1234.56
    - "100000" -> 100000.0

    Args:
        value: The value to parse (string, float, or None).

    Returns:
        The parsed float value, or 0.0 if parsing fails.
    """
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)

    # Remove $ and commas
    cleaned = str(value).replace("$", "").replace(",", "").strip()
    if not cleaned:
        return 0.0

    try:
        return float(cleaned)
    except ValueError:
        return 0.0

