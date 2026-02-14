from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Payment:
    id: int | None
    loan_id: int
    amount: float
    payment_date: date
    note: str | None

