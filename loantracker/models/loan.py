from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Loan:
    id: int | None
    name: str
    principal: float
    apr: float
    minimum_payment: float
    start_date: date

