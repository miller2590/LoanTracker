from __future__ import annotations

from datetime import date


class ValidationError(ValueError):
    pass


def _require_positive(value: float, field: str) -> None:
    if value <= 0:
        raise ValidationError(f"{field} must be greater than 0")


def _require_non_negative(value: float, field: str) -> None:
    if value < 0:
        raise ValidationError(f"{field} must be 0 or greater")


def validate_loan(name: str, principal: float, apr: float, minimum_payment: float, start_date: date) -> None:
    if not name.strip():
        raise ValidationError("Loan name is required")
    _require_positive(principal, "Principal")
    if apr < 0 or apr >= 100:
        raise ValidationError("APR must be between 0 and 100")
    _require_positive(minimum_payment, "Minimum payment")
    if not isinstance(start_date, date):
        raise ValidationError("Start date is invalid")


def validate_payment(amount: float, payment_date: date) -> None:
    _require_positive(amount, "Payment amount")
    if not isinstance(payment_date, date):
        raise ValidationError("Payment date is invalid")


def validate_scenario(name: str, extra_monthly: float) -> None:
    if not name.strip():
        raise ValidationError("Scenario name is required")
    _require_non_negative(extra_monthly, "Extra monthly payment")

