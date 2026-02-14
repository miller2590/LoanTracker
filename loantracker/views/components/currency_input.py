"""Currency input component and utilities."""

from __future__ import annotations

from nicegui import ui

from ...utils.currency import format_currency, parse_currency as _parse


def currency_input(label: str, value: float | None = None) -> ui.input:
    """Create a currency input field that formats on blur.

    User types a number, it gets formatted with commas and 2 decimals when they leave the field.
    Example: User types "100000" -> displays "100,000.00" on blur.

    Args:
        label: The input label text.
        value: Optional initial value as a float.

    Returns:
        A NiceGUI input element configured for currency.
    """
    initial_value = format_currency(value) if value else ""

    inp = ui.input(
        label=label,
        value=initial_value,
        validation={"Must be positive": lambda v: _parse(v) >= 0 if v else True}
    )

    def format_on_blur(e) -> None:
        raw = e.sender.value
        if not raw or not raw.strip():
            return
        parsed = _parse(raw)
        if parsed > 0:
            e.sender.value = format_currency(parsed)

    inp.on("blur", format_on_blur)
    return inp


def parse_currency(value: str | float | None) -> float:
    """Parse a currency string to float."""
    return _parse(value)

